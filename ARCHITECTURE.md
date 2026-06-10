# Architecture Specification: Configurable Land-Use Monitoring System

## Table of Contents

1. [Introduction & Overview](#1-introduction--overview)
2. [Workflow](#2-workflow)
3. [Tech Stack](#3-tech-stack)
4. [LangGraph Agent Design](#4-langgraph-agent-design)
5. [Vector Database Schema](#5-vector-database-schema)
6. [FastAPI Backend Design](#6-fastapi-backend-design)
7. [Frontend Structure & Layout](#7-frontend-structure--layout)

---

## 1. Introduction & Overview

### 1.1 Project Description

- This project is a configurable land-use monitoring system that performs zero-shot classification of satellite imagery against user-defined class taxonomies.
- It is built as an extension to Microsoft's GeoVision Labeler (GVL) paper, which proposed a strict zero-shot classification framework using a vision-language model (vLLM) to generate descriptions and a downstream LLM to classify those descriptions into user-supplied categories.
- The system extends GVL from a stateless, single-image inference pipeline into a stateful, agentic system orchestrated by a LangGraph agent that adds conditional hierarchical clustering, parallel patch-level visual reasoning, retrieval-augmented temporal context, and confidence-gated fallbacks.
- The user submits a satellite image, a geographic location (latitude and longitude), and a list of candidate classes; the system returns a predicted class, a confidence score, the model's reasoning, the supporting visual description, and any retrieved prior analyses that informed the prediction.

### 1.2 Core Idea

- The original GVL pipeline is stateless: each image is classified independently with no memory of prior analyses and no notion of geographic context across requests.
- This project preserves GVL's core insight (vLLM for description, LLM for classification) but treats the pipeline as one component within a larger agent that maintains state, retrieves relevant priors, and chooses among classification strategies based on input characteristics.
- Three principal extensions distinguish this system from the paper: a LangGraph agent that conditionally invokes hierarchical clustering when the class list is large, a hybrid RAG retrieval layer that injects prior analyses at the same location into the classifier prompt, and a confidence-gated fallback chain (targeted vLLM retry, then CLIP recovery) for graceful degradation.
- The framing is "configurable land-use monitoring" rather than "threat detection" because GVL's strongest empirical results are on configurable taxonomies (UC Merced, RESISC45) rather than fixed-threat detection, and because temporal context retrieval directly serves a land-use monitoring use case.

### 1.3 High-Level Workflow

- The frontend submits an image, latitude/longitude, class list, and optional retrieval parameters (radius, time window) to the FastAPI backend.
- FastAPI invokes the LangGraph agent, which executes a sequence of nodes that validate inputs, preprocess and optionally tile the image, decide whether hierarchical clustering is needed, generate visual descriptions of each patch in parallel via the vLLM, synthesize them into a single description, retrieve prior analyses from Qdrant using a hybrid filter-then-rank query, classify the synthesized description with a structured-output LLM call, gate on confidence with retry or CLIP fallback paths, store the result if confidence is acceptable, and format the final response.
- The frontend receives the response either as a single JSON payload (`/analyze`) or as a stream of Server-Sent Events (`/analyze/stream`) that progressively populates the report's sections as each pipeline stage completes.

### 1.4 In-Scope

- Single-user system with no authentication or multi-tenancy in v1, with the schema future-proofed for a `user_id` field.
- Single image per request, with batch processing handled at the API layer as a simple loop if needed.
- RGB satellite imagery in PNG or JPEG format, with a sensible upper bound on file size (target: 20 MB).
- Lat/lon coordinates as the canonical location identifier, supplied either by clicking on a map or by entering values manually in a coordinate picker modal.
- Configurable class taxonomies submitted per-request, with optional per-class descriptions for disambiguation.
- Hybrid RAG retrieval combining geospatial filtering, class-list compatibility filtering, optional temporal filtering, and semantic similarity over vLLM description embeddings.
- Confidence scoring inline in the classification call (1–5 integer scale) with structured output that also includes alternative classes and an ambiguity reason.
- A web frontend designed for desktop viewports (≥1280px width) with no mobile or tablet responsiveness.

### 1.5 Out-of-Scope

- Authentication, user profiles, and any multi-tenant data isolation beyond the single-user assumption.
- Mobile or tablet-responsive layouts; the system displays a "desktop only" message on smaller viewports.
- Mid-analysis cancellation of in-flight requests.
- Real-time multi-user collaboration or shared analysis state.
- Multi-spectral or hyperspectral imagery; the system supports RGB only, matching GVL's stated limitation.
- GeoTIFF, NITF, or other specialized geospatial raster formats.
- Streaming or real-time satellite feeds; all input is user-uploaded static imagery.
- Internationalization; American English only.
- Production-grade observability (full distributed tracing, metrics dashboards), beyond the operational metadata stored per analysis for inline debugging.

---

## 2. Workflow

This section walks through the pipeline stage by stage. Each stage corresponds to a LangGraph node (or a small group of nodes) and describes what the stage does, what it consumes, the exact processing logic, and what it produces. Each stage also includes an "Interview Defense" subsection summarizing the reasoning behind the design choice for last-minute interview revision.

### 2.1 Input Validation

- **Purpose:** Reject malformed or unsupported inputs at the earliest possible stage so that downstream nodes never have to defensively re-check the input contract.
- **Inputs:**
  - `image_bytes`: raw uploaded image (PNG or JPEG)
  - `lat`: float, must be in [-90, 90]
  - `lon`: float, must be in [-180, 180]
  - `class_list`: list of strings, length between 2 and 50
  - `class_descriptions`: optional dict mapping class name to description string
  - `retrieval_radius_km`: float, default 5.0, range 0.1 to 100
  - `retrieval_time_window_days`: optional integer, default None
  - `timestamp`: optional datetime, defaults to current UTC time

- **Processing logic:**
  - The node first validates that `image_bytes` is non-empty and that the bytes can be opened as a valid image using PIL.
  - It then validates the image format is PNG or JPEG and rejects RGBA or grayscale unless they can be losslessly converted to RGB.
  - It validates that `lat` and `lon` are within their respective ranges, returning an error if not.
  - It checks `class_list` length is between 2 and 50 and that all entries are non-empty strings after trimming whitespace.
  - It checks for exact-duplicate classes after normalization (lowercase, trimmed) and rejects the request if duplicates are present.
  - It computes `class_list_hash` as a stable SHA-256 hash of the sorted, normalized class list to be used downstream for retrieval compatibility filtering.
  - It computes `image_hash` as a SHA-256 of the raw image bytes for storage deduplication.
  - On any validation failure, the node sets a fatal error in state and the API surface returns HTTP 400 with the error message.

- **Outputs:**
  - Updates state with `image_bytes`, `image_hash`, `lat`, `lon`, `class_list`, `class_list_hash`, `class_descriptions`, `retrieval_radius_km`, `retrieval_time_window_days`, and `timestamp`.

#### Interview Defense

- Validation is a fatal-fail node, not a graceful-degradation node, because every downstream node depends on the input contract being satisfied; allowing partial garbage through would silently produce nonsense classifications rather than a clean 400 response.
- Coordinates are required as floats (not strings or place names) because string-based location identifiers ("Hyderabad downtown" vs "Hyd downtown") do not support geographic-proximity queries, while lat/lon supports first-class geo filtering in Qdrant.
- The `class_list_hash` is computed at validation time so that every downstream node uses the same canonical hash; computing it lazily would risk inconsistencies if classes were normalized differently in different places.

### 2.2 Image Preprocessing

- **Purpose:** Normalize the input image into a form the vLLM can reliably describe, including handling EXIF orientation, color modes, and tiling for large images.
- **Inputs:**
  - `image_bytes` from the validation node
- **Processing logic:**
  - The node opens the image with PIL and applies EXIF orientation correction so that rotated phone or drone imagery is upright before description.
  - It converts the image to RGB if it is currently RGBA, grayscale, or another mode, ensuring downstream model inputs are uniform.
  - It rejects the image if either dimension is below 224 pixels, because Kosmos-2 and Llama 3.2 Vision both work with 224-resolution patches natively, and below this threshold there is insufficient context for the vLLM to produce a useful description.
  - If the image is at most 1024×1024 pixels, the node passes the image through whole without tiling and sets `was_tiled = False`.
  - If the image exceeds 1024×1024 pixels, the node tiles the image into approximately 512×512 pixel patches with roughly 10% overlap between adjacent patches, and sets `was_tiled = True`.
  - Each patch is wrapped in a `PatchData` object containing the patch image bytes, its `(row, col)` position in the source grid, and a unique patch index.
  - The resulting list of patches (or a single-element list containing the whole image) is stored in state as `processed_patches`.

- **Outputs:**
  - `processed_patches`: list of `PatchData` objects
  - `was_tiled`: boolean
  - `num_patches`: integer

#### Interview Defense

- Tiling at 512×512 with 10% overlap is informed by Kosmos-2's native 224-pixel patch resolution: 512 gives the model roughly 2x the resolution while staying well within attention-budget limits, and overlap prevents cutting buildings or features at tile boundaries, which is a standard pattern in remote-sensing inference.
- The 1024×1024 passthrough threshold is chosen because GVL's empirical results on UC Merced and RESISC45 use 256×256 native and SpaceNet uses 1024×1024 split into 9 patches; staying below 1024 avoids the attention-dilution problem the paper itself flags as a limitation.
- Rejecting images below 224 pixels is honest about the pipeline's lower bound; silently upsampling a low-resolution image would produce confident but ungrounded descriptions, which is the worst failure mode for an interpretable system.

### 2.3 Conditional Hierarchical Clustering

- **Purpose:** When the class list is large, group classes into coarser meta-classes so that the classifier is asked to distinguish among a small number of well-separated groups rather than dozens of overlapping fine-grained classes.
- **Inputs:**
  - `class_list` and `class_list_hash` from validation
- **Processing logic:**
  - The `decide_cluster` node inspects the length of `class_list` and selects a clustering strategy: `none` for 2 to 9 classes, `hierarchical_d1` for 10 to 25 classes, and `hierarchical_d2` for 26 or more classes.
  - If the strategy is `none`, the node sets `effective_class_list = class_list` directly and skips the clustering node entirely.
  - If clustering is required, the `cluster` node first checks an in-memory or persistent cache keyed by `class_list_hash` and clustering strategy.
  - On a cache hit, the cached hierarchy is returned immediately without making any LLM calls.
  - On a cache miss, the node calls the classifier LLM with a prompt that asks it to suggest non-overlapping meta-class names for the provided class list (Step 1 of the GVL clustering procedure).
  - For each original class, a second LLM call (or a structured single-pass call returning all assignments) maps the class to one of the suggested meta-class names (Step 2).
  - For `hierarchical_d2`, the node recursively applies the same procedure within each top-level meta-class to produce a second level of sub-meta-classes (Step 3).
  - The final hierarchy is cached by `class_list_hash` and the appropriate level's meta-class names are written to `effective_class_list` in state.
  - The `class_hierarchy` field in state stores the full nested mapping so that the final result can be expanded back to original classes if needed during post-processing.

- **Outputs:**
  - `clustering_strategy`: one of `none`, `hierarchical_d1`, `hierarchical_d2`
  - `effective_class_list`: the list the classifier will actually use
  - `class_hierarchy`: optional nested dictionary of meta-classes to original classes

#### Interview Defense

- The thresholds (10 and 26 classes) are informed interpolations between GVL's tested points: the paper shows enumerating 21 classes on UC Merced drops accuracy by 11–19 percentage points and the same pattern is worse with 45 classes on RESISC45. The 10 and 26 thresholds are positioned to engage clustering before the prompt-dilution effect becomes severe.
- Clustering is cached by class-list hash because the same user often runs many images against the same taxonomy; without caching, the system would re-cluster identical class lists on every request, wasting LLM calls and adding latency to every analysis.
- Clustering is treated as optional rather than mandatory because GVL itself shows no clustering is needed at low class counts (binary buildings vs no-buildings achieves 93.2% accuracy with no clustering at all), and forcing clustering on small lists would add latency without benefit.

### 2.4 Parallel Patch Description (vLLM Stage)

- **Purpose:** Generate a detailed natural-language description of each patch independently, leveraging the vLLM's strength at producing rich textual descriptions of visual content.
- **Inputs:**
  - `processed_patches`: the list of patch objects from preprocessing
  - `class_descriptions`: optional disambiguation strings to optionally inject into the vLLM prompt
- **Processing logic:**
  - The `describe_patches` node uses LangGraph's `Send` API to fan out one parallel call per patch to a `describe_single_patch` worker node.
  - A concurrency limit (default 4 in-flight calls) wraps the fan-out to avoid tripping rate limits on the hosted vLLM provider.
  - Each `describe_single_patch` invocation builds a prompt of the form: a context statement ("This is a satellite image patch."), the patch's grid position when applicable, and a directive to produce a detailed visual description.
  - The vLLM (Llama 3.2 Vision via Groq) is called with the patch bytes and the prompt, returning a description string.
  - On a transient API error, the worker node retries once with the same prompt before failing.
  - On persistent failure, the worker writes an empty description for that patch and appends an entry to `pipeline_errors` rather than killing the whole pipeline.
  - Patch descriptions are accumulated into the shared `patch_descriptions` list using a custom reducer (`Annotated[List[str], operator.add]`) that allows parallel writes to append cleanly without clobbering each other.

- **Outputs:**
  - `patch_descriptions`: list of strings, one per patch, in order

#### Interview Defense

- Per-patch description in parallel is correct because each patch's description is independent of the others: there is no cross-patch dependency at the description stage, so sequential processing would waste wall-clock time. LangGraph's `Send` API handles the fan-out and join cleanly.
- Concurrency is capped because hosted vLLM providers (Groq, Together) enforce per-second rate limits; uncapped fan-out on a 16-tile image would trip rate limits and cause cascading failures rather than a graceful queue.
- Per-patch description rather than passing the whole tiled image at once preserves spatial granularity in the descriptions: "buildings in the top-left, forest in the bottom-right" is a useful reasoning signal that the synthesis stage can use, and a single-shot description of a tiled mosaic would lose this.

### 2.5 Description Synthesis

- **Purpose:** Combine the per-patch descriptions into a single coherent description of the entire image, preserving spatial patterns, before the classifier sees it.
- **Inputs:**
  - `patch_descriptions`: list of strings
  - `was_tiled`: boolean indicating whether tiling occurred
- **Processing logic:**
  - If `was_tiled` is False (single-patch image), the node simply copies the only entry of `patch_descriptions` into `synthesized_description` and skips the LLM call entirely.
  - If `was_tiled` is True, the node constructs a synthesis prompt that lists each patch description prefixed with its grid position (e.g., "Top-left (row 0, col 0): ...") and asks the classifier LLM to produce a single coherent description of the entire scene, noting any spatial patterns (such as concentration of buildings, directional roads, or zones of vegetation).
  - The prompt explicitly instructs the model to preserve specific visual details from each patch rather than over-abstracting.
  - The LLM response is stored as `synthesized_description` in state.
  - On error, the node falls back to a simple concatenation of patch descriptions joined by spatial-position labels, marking `pipeline_errors` accordingly.

- **Outputs:**
  - `synthesized_description`: single string used as input to the retrieval and classification stages

#### Interview Defense

- Synthesis is performed at the description stage rather than per-patch classification followed by aggregation because per-patch classification creates an aggregation problem with no clean solution: weighted voting across patches with different confidence pathways obscures rather than helps, and the classifier sees the entire image's evidence in one shot, mirroring how a human analyst would interpret a scene.
- Synthesis is skipped when there is only one patch because there is no synthesis to do; an LLM call to "synthesize a single description into itself" would waste latency and tokens.
- Including patch grid positions in the synthesis prompt preserves spatial reasoning ("buildings concentrated in the north", "river running diagonally") which a naive concatenation of descriptions would lose.

### 2.6 Hybrid RAG Retrieval

- **Purpose:** Find prior analyses near the same geographic location with a compatible class taxonomy, and inject the most semantically similar ones into the classifier's prompt as temporal context.
- **Inputs:**
  - `lat`, `lon` from validation
  - `class_list_hash` from validation
  - `synthesized_description` from synthesis
  - `retrieval_radius_km` and `retrieval_time_window_days` from request parameters
- **Processing logic:**
  - The `retrieve` node embeds the `synthesized_description` using OpenAI's `text-embedding-3-small` model, producing a 1536-dimensional vector that becomes the query vector.
  - It constructs a Qdrant filter that combines a geospatial radius filter (within `retrieval_radius_km` of the query lat/lon, expressed in meters), an exact-match filter on `class_list_hash` for taxonomy compatibility, a confidence floor of 3 (only retrieve high- or medium-confidence priors), and an optional time-range filter when `retrieval_time_window_days` is set.
  - It sends a single Qdrant query that applies the filter as a metadata pre-filter and ranks the surviving candidates by cosine similarity to the query embedding, returning the top 3.
  - If the initial query returns zero results, the node applies progressive relaxation: first dropping the time filter, then dropping the class-list-hash filter, recording each relaxation in `retrieval_relaxation_applied`.
  - When no candidates are found even after full relaxation, the node returns an empty list and the rest of the pipeline proceeds without retrieved context.
  - The results are mapped into `RetrievedAnalysis` objects containing the prior's timestamp, distance from the current location, predicted class, confidence, vLLM description, and reasoning, and stored in `retrieved_context`.

- **Outputs:**
  - `retrieved_context`: list of `RetrievedAnalysis` objects (0 to 3 entries)
  - `retrieval_relaxation_applied`: list of strings naming any relaxation steps

#### Interview Defense

- The hybrid filter-then-search pattern (geo + class-hash + time → semantic rank) is chosen over pure semantic search because pure semantic search would retrieve "looks like a beach" descriptions across the globe regardless of whether they are relevant to the user's specific location, while the metadata filters constrain the candidate pool to genuinely relevant priors before semantic ranking refines among them.
- The query vector is the current `synthesized_description` embedding, not the image embedding or the predicted class, because the description is the visual evidence rendered as text, and finding prior descriptions that are visually similar (at the description level) is exactly the desired retrieval signal. The classifier reads descriptions, so retrieving by description-similarity matches the consumer.
- Class-list-hash matching is used for compatibility filtering because retrieving a "buildings vs no-buildings" prior to inform a "wetland vs forest vs urban" classification is useless context: the prior was answering a different question. Exact-hash matching is strict for v1; future work could implement Jaccard-similarity hashing for partial overlap.
- The confidence floor of 3 prevents poisoning the retrieval pool with low-confidence prior predictions, which would create a feedback loop where each new analysis is conditioned on increasingly unreliable priors. This is paired with the storage logic that only persists analyses with confidence ≥ 3.
- The progressive relaxation strategy degrades gracefully rather than returning empty results immediately, surfacing the relaxation in the response so the user knows the system had to widen its search.
- The radius and time window are exposed as user-facing controls (with sensible defaults of 5km and "any time") because different use cases need different ranges (a single farm plot vs. regional land-use trends), and presets rather than free-form sliders prevent users from picking pathological values that would make the system look broken.

### 2.7 LLM Classification

- **Purpose:** Classify the synthesized description into one of the user-defined classes using a structured-output LLM call, returning class, confidence, reasoning, and ambiguity information in a single response.
- **Inputs:**
  - `synthesized_description` from synthesis
  - `effective_class_list` from clustering (or original class list)
  - `retrieved_context` from retrieval
  - `class_descriptions`: optional disambiguation strings
- **Processing logic:**
  - The `classify` node constructs a prompt with three parts: a directive to classify the description into one of the provided classes, the classes themselves (with optional descriptions for disambiguation), the description, and a "Prior context" section listing the retrieved analyses with the explicit framing "Prior classifications are reference only; classify based on the current description."
  - The prompt requests structured JSON output with the schema: `predicted_class` (string), `confidence` (integer 1–5), `reasoning` (string), `alternative_classes` (list of strings, populated only if confidence < 4), and `ambiguity_reason` (string, populated only if confidence < 4).
  - The classifier LLM is Gemini 2.0 or 2.5 Flash, called via the Google AI Studio API in JSON mode, which reliably returns parseable structured output.
  - If the model returns a class that is not in `effective_class_list`, the node logs the violation and falls back to CLIP for direct image-to-text classification (treating this as a classification failure rather than a confidence-gate failure).
  - On transient API errors, the node retries once before failing.
  - On persistent failure, the node sets confidence to 0, which the downstream confidence gate routes directly to the CLIP fallback path.

- **Outputs:**
  - `predicted_class`: string, must be in `effective_class_list`
  - `confidence`: integer 1–5
  - `reasoning`: string explaining the classification
  - `alternative_classes`: optional list of strings
  - `ambiguity_reason`: optional string

#### Interview Defense

- Structured output (JSON mode) is used rather than free-text parsing because reliability of parsing is critical: a malformed LLM response would block the rest of the pipeline, and Gemini's JSON mode produces schema-conforming output far more reliably than regex-extracting fields from free text.
- Confidence, reasoning, alternatives, and ambiguity reason are all returned in a single structured call rather than as separate LLM-as-judge calls, because the additional fields cost only a few output tokens and obtain the disambiguation information needed for a targeted retry "for free." Calling an LLM twice to ask "are you sure?" would double cost and latency for information already implicit in the first call.
- Retrieved context is injected with the explicit "reference only" framing because retrieved priors can be wrong, and presenting them as authoritative would encourage the classifier to copy past mistakes; framing them as evidence to consider but not trust mitigates the RAG-poisoning failure mode.
- The classifier's class output is constrained to `effective_class_list` rather than the original class list because if clustering was used, the classifier is choosing among meta-classes, not original classes; this keeps the classification node simple and orthogonal to the clustering strategy.

### 2.8 Confidence-Gated Routing

- **Purpose:** Decide whether the classification is reliable enough to accept, requires a targeted retry, or requires falling back to CLIP.
- **Inputs:**
  - `confidence`, `predicted_class`, `alternative_classes`, `ambiguity_reason`, `reasoning` from the classify node
  - `used_retry`: boolean tracking whether a retry has already occurred
- **Processing logic:**
  - Routing is implemented as a LangGraph conditional edge function on the output of `classify`, not as a separate node.
  - If `confidence ≥ 4`, the edge routes directly to `store`.
  - If `confidence` is 2 or 3 and `used_retry` is False, the edge routes to `retry_vllm_targeted`.
  - If `confidence ≤ 1`, the edge routes to `clip_fallback`.
  - If `used_retry` is already True (the retry has already been attempted), the edge applies a simpler rule: confidence ≥ 3 routes to `store`, otherwise routes to `clip_fallback`. This prevents infinite retry loops.
  - The `retry_vllm_targeted` node constructs a refined vLLM prompt of the form "The previous description was classified as [predicted_class] but could plausibly be [alternative_classes]. Re-examine the image and describe the specific features that would distinguish [predicted_class] from [alternatives]. Focus on [ambiguity_reason]." and re-runs the per-patch description and synthesis stages.
  - After retry, the pipeline re-enters `classify` with the new synthesized description and the same retrieved context (retrieval is not re-run, since the geographic location has not changed), producing a second classification result that is then routed by the simpler post-retry rule.
  - The `clip_fallback` node uses CLIP to compute cosine similarity between the original image and text prompts constructed from each class label, returning the highest-similarity class as the prediction with confidence set to 2 (a marker indicating "fallback was used"), and reasoning set to a brief string identifying CLIP as the source.

- **Outputs:**
  - Updated `predicted_class`, `confidence`, `reasoning` (potentially overwritten by retry or CLIP)
  - `used_retry`: boolean
  - `used_clip_fallback`: boolean

#### Interview Defense

- Inline confidence in the classification call is preferred over a separate LLM-as-judge pass because the additional information needed for a targeted retry (alternative classes and ambiguity reason) is obtainable in the same call for a few output tokens; calling another LLM to ask "is this right?" is wasteful when the original LLM already knows what it was uncertain about.
- The targeted retry prompt is preferred over a generic "describe more carefully" retry because it tells the vLLM what to look for (specific distinguishing features between candidate classes), which is meaningfully more actionable; without this, retries are unfocused and rarely fix the original ambiguity.
- The retry path bounds at one retry to prevent infinite loops; after one retry, the system commits to the higher-confidence of the two attempts or falls back to CLIP.
- CLIP is used as the absolute floor fallback (not retry) because if the LLM has already failed twice with rich context, further LLM prompting is unlikely to help; CLIP's image-to-text similarity is an entirely different modality and serves as a meaningful last-resort signal.
- The confidence gate is implemented as a conditional edge rather than a routing node because LangGraph conditional edges read state and return a node name, which is exactly the right primitive for this pattern; making it a node would add an extra hop without semantic benefit.

### 2.9 Storage

- **Purpose:** Persist the analysis result in Qdrant for future RAG retrieval, but only if the result is reliable enough to inform later predictions.
- **Inputs:**
  - All accumulated state fields needed to populate the storage payload
- **Processing logic:**
  - The `store` node computes the embedding of `synthesized_description` (already computed during retrieval, but recomputed here if not cached in state) using `text-embedding-3-small`.
  - It checks `confidence`: if `confidence < 3`, the node logs the result and skips the Qdrant write.
  - If `confidence ≥ 3`, the node assembles the full payload (see Section 5) including the embedding, the description text, classification result, retrieved context references, pipeline metadata flags, and provenance tags.
  - The image bytes themselves are written to object storage (Cloudflare R2 in production, local filesystem in development), and the resulting URL or path is stored as `image_ref` in the payload.
  - The Qdrant point is created with a UUID identifier (carried in state as `analysis_id`) so the same identifier is used in the API response.
  - The node always returns success (the response is delivered even if storage fails), with any storage error logged to `pipeline_errors`.

- **Outputs:**
  - `analysis_id`: UUID of the stored analysis
  - On low confidence: no Qdrant write, but the API response still includes the result

#### Interview Defense

- Storing only confidence ≥ 3 prevents poisoning the RAG pool with unreliable predictions; storing low-confidence results would mean future analyses are conditioned on prior bad predictions, compounding error over time.
- Image bytes are written to object storage rather than embedded in the Qdrant payload because vector databases are not optimized for binary blob storage; keeping Qdrant focused on vectors and structured metadata, with images in S3-compatible storage, follows the standard pattern and keeps the vector DB lean.
- Storage failures are non-fatal because the user expects a classification response regardless of whether persistence succeeds; failing the response on a storage error would be a worse user experience than serving the result and logging the failure for later reconciliation.

### 2.10 Final Output Generation

- **Purpose:** Format the agent's accumulated state into the API response, distinguishing what is user-facing from what is internal debug-level information.
- **Inputs:**
  - All accumulated state
- **Processing logic:**
  - The `format` node constructs a `ClassificationResult` (or `AnalyzeResponse`) object containing: `analysis_id`, `predicted_class`, `confidence`, `reasoning`, `synthesized_description`, `retrieved_context` (with snippets, not full descriptions, for compactness), `used_clustering`, `used_retry`, `used_clip_fallback`, and `alternative_classes` if confidence < 4.
  - Per-patch descriptions are not included by default in the response but are available in the stored payload for debugging.
  - The reasoning field is exposed but consumers (the frontend) display it under the "LLM Interpretation" label and flag it as model-generated.
  - On the streaming endpoint, this node also emits the final `complete` SSE event containing the assembled response.

- **Outputs:**
  - `final_result`: structured `AnalyzeResponse` payload returned by the API

#### Interview Defense

- The response includes the synthesized description and retrieved context (not just the predicted class) because interpretability is a core feature of the system; users should be able to see why a classification was made and what evidence informed it, mirroring GVL's interpretability claim.
- Per-patch descriptions are excluded from the default response but available on request because they are debug-level detail; bloating the default response with per-patch text would harm UX without serving the typical user.
- The pipeline metadata flags (`used_clustering`, `used_retry`, `used_clip_fallback`) are exposed so the frontend can render the "Pipeline Trace" section and so the system's branching behavior is visible during interview demos rather than hidden in logs.

---

## 3. Tech Stack

### 3.1 Frontend

- **React with Vite and TypeScript:** The frontend is a single-page React application built with Vite as the bundler and TypeScript for type safety against the backend response schemas.
- **Tailwind CSS and shadcn/ui:** Tailwind handles utility-first styling; shadcn/ui provides a copy-paste component library built on Radix primitives, giving polished primitives (Dialog, Tooltip, etc.) without an npm dependency for the components themselves.
- **react-router-dom:** Client-side routing for the four pages (Overview, Analysis, Archive, Architecture).
- **react-leaflet with Leaflet.js:** Map rendering for the Archive page and the coordinate picker modal. Leaflet is the underlying library; react-leaflet provides the React bindings.
- **CartoDB dark_matter tiles:** The dark, minimal map style is sourced from CartoDB's free tile service, which supports labels for usability while preserving the editorial aesthetic.
- **React Flow:** The interactive agent graph on the Architecture page uses React Flow for node/edge rendering, pan/zoom, hover states, and minimap support.
- **Lucide icons:** Default icon set bundled with shadcn/ui.

#### Interview Defense

- Vite is preferred over Create React App because CRA is deprecated and Vite is the modern default for new React projects; Vite's dev server is significantly faster and its build output is smaller.
- React was chosen over Next.js because the developer has prior production experience with React and the project's needs (single-page workspace, REST backend, no SSR or edge-routing requirements) do not justify Next.js's additional complexity. This is a scope-aware tradeoff.
- TypeScript is used because the API returns structured data with multiple optional fields and nested arrays; typing the response catches mismatches between frontend and backend at compile time rather than runtime.

### 3.2 Backend

- **FastAPI:** The backend is a FastAPI application running in a single process. FastAPI's async-native design supports the parallel patch processing in the agent, and Pydantic models provide validation and serialization for request and response schemas.
- **LangGraph:** The agent is built on LangGraph, running in-process with the FastAPI server (no separate LangGraph Server service). The agent is compiled once at app startup and invoked per request.
- **Uvicorn:** ASGI server hosting the FastAPI application.
- **slowapi:** Rate limiting based on client IP, applied as a decorator on the `/analyze` endpoint.

#### Interview Defense

- LangGraph is used in-process rather than as a separate service because for a single-user system the additional deployment complexity of LangGraph Server is not justified. In production with multi-tenant workloads, splitting the agent into its own service would allow independent scaling, but for this scope a single FastAPI process is correct.
- LangGraph specifically (rather than a hand-rolled Python orchestration script) is chosen because the agent has real conditional branching (clustering decision, confidence gate), parallel fan-out (patch description), and stateful retry/fallback paths; LangGraph's primitives (`Send`, conditional edges, state reducers) express these cleanly, and the resulting graph is visualizable, which is itself a feature of the project (the Architecture page).

### 3.3 Models

- **vLLM (visual description):** Llama 3.2 Vision via Groq's hosted inference API. Llama 3.2 Vision was chosen over Kosmos-2 because it is broadly supported across hosted inference providers, while Kosmos-2 would require self-hosting or a dedicated GPU instance. This is a deployability-vs-accuracy tradeoff: GVL's results suggest Kosmos-2 outperforms Llama 3.2 Vision by 5–10 percentage points, but the ability to deploy without GPU infrastructure is more valuable for a portable demo.
- **LLM (classifier and synthesis):** Gemini 2.0 or 2.5 Flash via Google AI Studio. Gemini Flash provides reliable structured output via JSON mode, generous free tier limits, low cost per call, and comparable capability to GPT-4o for a fraction of the cost.
- **Embeddings:** OpenAI `text-embedding-3-small` (1536 dimensions). Chosen for strong MTEB retrieval benchmarks, mature tooling, and Matryoshka-truncatable embeddings (which provides a future-work path for dimension reduction without re-embedding).
- **CLIP (fallback):** Local CLIP (the `openai/clip-vit-base-patch32` model) running in-process within FastAPI, since CLIP is small enough to run on CPU with acceptable latency for fallback use.

#### Interview Defense

- Different models for different stages preserve the architectural separation between visual grounding (vLLM) and semantic classification (LLM), which is the core insight of GVL; using Gemini for both would collapse this and undermine the interpretability story.
- Hosted inference rather than self-hosted models is chosen for all three primary models because hosted APIs have free or near-free tiers at the demo's scale, eliminate GPU costs, and require zero infrastructure work; self-hosting would consume engineering time better spent on the agent and retrieval logic.
- CLIP is local and CPU-bound because it is invoked rarely (only on confidence-floor failures), and the latency hit on a CPU forward pass is acceptable for a fallback path that should be hit on perhaps 5% of requests.

### 3.4 Data Layer

- **Qdrant (vector database):** Self-hosted via Docker in development, Qdrant Cloud free tier in production. Native geospatial filtering (geo_radius queries) is the decisive feature for this project; Qdrant is the only major vector DB that exposes geo as a first-class field type.
- **Cloudflare R2 (object storage):** S3-compatible storage for image bytes in production. Local filesystem is used in development behind the same `get_image(image_id)` interface.
- **No relational database:** The system uses Qdrant for both vectors and metadata; introducing Postgres or MongoDB would add a third storage system without benefit.

#### Interview Defense

- Qdrant was chosen over Pinecone because Qdrant has native geo-filtering (a first-class feature for this project's access pattern), supports local Docker development for rapid iteration, and is open source. Pinecone is more mainstream but its filtering is weaker, it has no native geo support, and it is cloud-only.
- Qdrant was chosen over pgvector despite pgvector's appeal of consolidating storage in a single Postgres instance, because the geo-filtering performance and developer experience for vector-first workloads is meaningfully better in Qdrant, and the project's scale does not benefit from Postgres's relational features.
- Object storage is separate from Qdrant because vector databases are optimized for vectors and structured metadata, not binary blobs; mixing them in one system is an anti-pattern.

### 3.5 Deployment

- **Frontend:** Deployed to Vercel or Netlify (auto-detect for Vite React).
- **Backend:** Deployed to Railway or Render. Both support free-tier deployments from a GitHub repository.
- **Vector DB:** Qdrant Cloud free tier (1 GB).
- **Object storage:** Cloudflare R2 free tier (10 GB).
- **No authentication:** The system is publicly accessible; rate limiting by IP via slowapi prevents trivial abuse.

---

## 4. LangGraph Agent Design

### 4.1 Purpose

- The LangGraph agent orchestrates the full classification pipeline as a stateful graph of nodes connected by conditional and unconditional edges.
- It owns the entire flow from input validation through final output generation, including all parallelism, branching, retry, and fallback logic.
- It is invoked by the FastAPI `/analyze` endpoint synchronously (via `graph.ainvoke`) or by the `/analyze/stream` endpoint asynchronously (via `graph.astream` or `astream_events`) to support Server-Sent Events streaming.
- It interacts with Qdrant directly from within the `retrieve` and `store` nodes, with the vLLM and LLM via their respective hosted API clients, and with object storage from within the `store` node.

### 4.2 State Schema

- The agent's state is a flat `TypedDict` that flows through every node; nodes return partial updates which are merged into the global state by LangGraph's reducer machinery.
- The full schema is:

  - **Inputs (set at validation, never modified after):**
    - `image_bytes`: bytes
    - `image_hash`: string
    - `lat`: float
    - `lon`: float
    - `timestamp`: datetime
    - `class_list`: list of strings
    - `class_list_hash`: string
    - `class_descriptions`: optional dict[str, str]
    - `retrieval_radius_km`: float
    - `retrieval_time_window_days`: optional integer
    - `analysis_id`: UUID, generated at validation

  - **Preprocessing:**
    - `processed_patches`: optional list of `PatchData`
    - `was_tiled`: boolean
    - `num_patches`: integer

  - **Clustering:**
    - `clustering_strategy`: literal of `none` / `flat` / `hierarchical_d1` / `hierarchical_d2`
    - `class_hierarchy`: optional nested dict
    - `effective_class_list`: list of strings

  - **vLLM:**
    - `patch_descriptions`: list of strings (with `Annotated[List[str], operator.add]` reducer to support parallel writes)
    - `synthesized_description`: string

  - **RAG:**
    - `retrieved_context`: list of `RetrievedAnalysis` objects
    - `retrieval_relaxation_applied`: list of strings

  - **Classification:**
    - `predicted_class`: optional string
    - `confidence`: optional integer
    - `reasoning`: optional string
    - `alternative_classes`: optional list of strings
    - `ambiguity_reason`: optional string

  - **Pipeline metadata:**
    - `used_retry`: boolean
    - `used_clip_fallback`: boolean
    - `used_clustering`: boolean
    - `pipeline_errors`: list of strings (with append reducer)

  - **Output:**
    - `final_result`: optional `AnalyzeResponse`

#### Interview Defense

- The state schema is flat rather than nested because LangGraph merges updates at the top level; nested state complicates partial updates and reducer semantics. Flat is easier to reason about and easier to debug in interview demos.
- Critical fields like `patch_descriptions` and `pipeline_errors` use append reducers because parallel nodes (especially in the patch-description fan-out) need to write without clobbering each other; without an explicit reducer, parallel writes would race.
- `effective_class_list` is decoupled from `class_list` so that the classify node always classifies against `effective_class_list` regardless of whether clustering occurred; this keeps classification orthogonal to the clustering strategy and avoids special-casing in the classify node.

### 4.3 Node-by-Node Design

#### 4.3.1 `validate`

- **Purpose:** Validate all inputs, compute deterministic hashes, and reject malformed requests immediately.
- **Inputs read from state:** `image_bytes`, `lat`, `lon`, `class_list`, `retrieval_radius_km`, `retrieval_time_window_days`.
- **Processing:** Validates ranges and types (see Section 2.1). Computes `class_list_hash` and `image_hash`. Generates `analysis_id` UUID.
- **Outputs (state writes):** `class_list_hash`, `image_hash`, `analysis_id`, normalized `class_list`, `timestamp` (defaulted if not supplied).
- **Failure mode:** Sets a fatal error and the API surface returns HTTP 400; the graph does not proceed.

#### 4.3.2 `preprocess`

- **Purpose:** Apply EXIF orientation, RGB conversion, size validation, and tiling (if needed).
- **Inputs read from state:** `image_bytes`.
- **Processing:** EXIF rotation, RGB conversion, dimension check, tile-or-passthrough decision (see Section 2.2).
- **Outputs (state writes):** `processed_patches`, `was_tiled`, `num_patches`.
- **Failure mode:** Sets a fatal error if image is below the minimum dimension; otherwise transient errors during tiling fall back to whole-image processing.

#### 4.3.3 `decide_cluster`

- **Purpose:** Choose a clustering strategy based on class list length.
- **Inputs read from state:** `class_list`.
- **Processing:** Reads length and selects `none`, `hierarchical_d1`, or `hierarchical_d2`.
- **Outputs (state writes):** `clustering_strategy`. If `none`, also sets `effective_class_list = class_list` and the conditional edge skips the `cluster` node.
- **Failure mode:** Pure logic, no failure mode.

#### 4.3.4 `cluster` (conditional)

- **Purpose:** Generate meta-class hierarchy via LLM for large class lists.
- **Inputs read from state:** `class_list`, `class_list_hash`, `clustering_strategy`.
- **Processing:** Cache lookup by hash; on miss, calls LLM for meta-class generation and per-class assignment (see Section 2.3); recursive call for D=2.
- **Outputs (state writes):** `class_hierarchy`, `effective_class_list`, `used_clustering = True`.
- **Failure mode:** On LLM failure, falls back to `clustering_strategy = none` and uses original class list, logging error.

#### 4.3.5 `describe_patches` (fan-out parent)

- **Purpose:** Emit parallel `Send` events to `describe_single_patch` for each patch.
- **Inputs read from state:** `processed_patches`.
- **Processing:** Issues one `Send("describe_single_patch", patch)` per patch, up to a concurrency limit.
- **Outputs (state writes):** None directly; child nodes append to `patch_descriptions`.
- **Failure mode:** Trivial dispatch logic; no failure mode at this node.

#### 4.3.6 `describe_single_patch` (fan-out worker)

- **Purpose:** Generate a vLLM description of a single patch.
- **Inputs (per Send):** `PatchData` for one patch; reads `class_descriptions` from state.
- **Processing:** Builds prompt, calls vLLM, retries once on transient error.
- **Outputs (state writes):** Appends to `patch_descriptions` via append reducer.
- **Failure mode:** On persistent error, appends an empty string and an entry to `pipeline_errors`; does not fail the graph.

#### 4.3.7 `synthesize`

- **Purpose:** Combine patch descriptions into a single coherent description.
- **Inputs read from state:** `patch_descriptions`, `was_tiled`.
- **Processing:** If single-patch, copy through; otherwise call LLM with positional synthesis prompt (see Section 2.5).
- **Outputs (state writes):** `synthesized_description`.
- **Failure mode:** On LLM failure, falls back to spatial-position-labeled concatenation.

#### 4.3.8 `retrieve`

- **Purpose:** Run hybrid filter-then-rank query against Qdrant.
- **Inputs read from state:** `lat`, `lon`, `class_list_hash`, `synthesized_description`, `retrieval_radius_km`, `retrieval_time_window_days`.
- **Processing:** Embed description, build Qdrant filter, query top-3, apply progressive relaxation if empty (see Section 2.6).
- **Outputs (state writes):** `retrieved_context`, `retrieval_relaxation_applied`.
- **Failure mode:** On Qdrant error, returns empty `retrieved_context` and logs error; pipeline proceeds without prior context.

#### 4.3.9 `classify`

- **Purpose:** Classify the description with structured-output LLM call.
- **Inputs read from state:** `synthesized_description`, `effective_class_list`, `retrieved_context`, `class_descriptions`.
- **Processing:** Constructs structured-output prompt with reference-only framing, calls Gemini in JSON mode, validates output (see Section 2.7).
- **Outputs (state writes):** `predicted_class`, `confidence`, `reasoning`, `alternative_classes`, `ambiguity_reason`.
- **Failure mode:** On error, sets `confidence = 0`; conditional edge routes to CLIP fallback.

#### 4.3.10 `retry_vllm_targeted` (conditional)

- **Purpose:** Re-run vLLM with a targeted disambiguation prompt.
- **Inputs read from state:** `predicted_class`, `alternative_classes`, `ambiguity_reason`, `processed_patches`.
- **Processing:** Builds focused prompt, re-runs per-patch description (parallel), re-runs synthesis, then routes back to `classify`.
- **Outputs (state writes):** Updates `patch_descriptions` and `synthesized_description`; sets `used_retry = True`.
- **Failure mode:** On error, falls through to CLIP fallback.

#### 4.3.11 `clip_fallback` (conditional)

- **Purpose:** Use CLIP for image-to-text similarity classification when LLM has failed or returned very low confidence.
- **Inputs read from state:** `image_bytes`, `effective_class_list`.
- **Processing:** Computes CLIP embedding for the image and for each class label (rendered as a short prompt); takes argmax over cosine similarities.
- **Outputs (state writes):** `predicted_class`, `confidence = 2`, `reasoning = "CLIP fallback was used because the primary classification pipeline did not produce a confident result."`, `used_clip_fallback = True`.
- **Failure mode:** On error, returns the first class with confidence 0 and logs; this is a true last-resort path.

#### 4.3.12 `store`

- **Purpose:** Persist the analysis to Qdrant and image bytes to object storage.
- **Inputs read from state:** All state needed for the payload.
- **Processing:** Writes image to object storage, computes/reuses embedding, writes Qdrant point (only if `confidence ≥ 3`).
- **Outputs (state writes):** None to graph state; the `analysis_id` was set at validation.
- **Failure mode:** Logs error and continues; never fails the response.

#### 4.3.13 `format`

- **Purpose:** Build the final API response object.
- **Inputs read from state:** All accumulated state.
- **Processing:** Constructs the `AnalyzeResponse` Pydantic model with user-facing fields.
- **Outputs (state writes):** `final_result`.
- **Failure mode:** No external calls; assembling the response is pure logic.

### 4.4 Edge Topology

- `START → validate → preprocess → decide_cluster`.
- From `decide_cluster`: conditional edge — if `clustering_strategy == none`, go to `describe_patches`; otherwise go to `cluster` then `describe_patches`.
- `describe_patches` fans out via `Send` to multiple `describe_single_patch` workers, joining at `synthesize`.
- `synthesize → retrieve → classify`.
- From `classify`: conditional edge — if `confidence ≥ 4`, go to `store`; if `confidence ∈ {2, 3}` and `used_retry == False`, go to `retry_vllm_targeted`; if `confidence ≤ 1`, go to `clip_fallback`.
- `retry_vllm_targeted → describe_patches → ... → classify` (re-enters with `used_retry = True`).
- After `classify` post-retry: if `confidence ≥ 3`, go to `store`; otherwise go to `clip_fallback`.
- `clip_fallback → store`.
- `store → format → END`.

### 4.5 Interactions with FastAPI and Other Components

- **FastAPI `/analyze` endpoint:** Calls `graph.ainvoke(initial_state)` synchronously, awaits the final state, and returns `final_result` as the JSON response body.
- **FastAPI `/analyze/stream` endpoint:** Calls `graph.astream_events(initial_state)` and emits Server-Sent Events as nodes complete (one event per node, with the node name and any partial state fields needed by the frontend to update the corresponding shimmer section).
- **Qdrant:** Accessed directly from `retrieve` (read) and `store` (write) using the `qdrant-client` Python SDK; no Qdrant access from FastAPI route handlers themselves except in the `/history` endpoint, which queries Qdrant directly without invoking the agent.
- **Object storage:** Accessed only from `store`; the FastAPI surface does not interact with object storage directly.
- **Hosted model APIs:** Groq (vLLM), Google AI Studio (LLM), OpenAI (embeddings) are accessed only from within agent nodes, never from FastAPI routes.

---

## 5. Vector Database Schema

### 5.1 Collection Setup

- **Collection name:** `analyses`
- **Vector configuration:** 1536 dimensions, cosine distance (matching OpenAI `text-embedding-3-small`).
- **Payload indexes (for efficient filtering):**
  - `location` indexed as a `GEO` field for `geo_radius` queries.
  - `class_list_hash` indexed as `KEYWORD` for exact-match filters.
  - `timestamp` indexed as `DATETIME` for range filters.
  - `confidence` indexed as `INTEGER` for floor filters.
- **Point ID:** UUID (matches `analysis_id` carried in agent state and returned in API responses).

### 5.2 Payload Schema

Each point's payload contains:

- **Spatial fields:**
  - `location`: object with `lat` (float) and `lon` (float), used by Qdrant's geo index.
  - `geohash`: optional precomputed geohash at precision 6 (~1.2 km cell), used as a redundant fast-filter field if needed for performance.

- **Temporal:**
  - `timestamp`: ISO 8601 string (UTC) representing when the analysis was performed.

- **Image provenance:**
  - `image_hash`: SHA-256 of the original image bytes, used for deduplication checks.
  - `image_ref`: pointer to the image in object storage (e.g., `r2://bucket/path/to/image.jpg` or `file:///local/path` in development).
  - `was_tiled`: boolean.
  - `num_patches`: integer.

- **Grounded data (for RAG retrieval and inspection):**
  - `vllm_description`: the synthesized description (or single-patch description) — this is the text whose embedding lives in the vector field.
  - `patch_descriptions`: list of strings, the raw per-patch descriptions, kept for audit and debugging.

- **Classification result:**
  - `predicted_class`: string.
  - `confidence`: integer 1–5.
  - `class_list_hash`: string, used for retrieval compatibility filtering.
  - `class_list`: the original class list, stored for audit.

- **Model-generated interpretation (NOT used for retrieval):**
  - `reasoning`: string, surfaced to the user as "LLM Interpretation" but flagged as model-generated.
  - `alternative_classes`: optional list of strings.
  - `ambiguity_reason`: optional string.

- **Pipeline metadata (for debugging and interview demonstration):**
  - `used_clustering`: boolean.
  - `clustering_strategy`: string (`none`, `hierarchical_d1`, `hierarchical_d2`).
  - `used_retry`: boolean.
  - `used_clip_fallback`: boolean.
  - `vllm_model`: string identifier of the vLLM used.
  - `llm_model`: string identifier of the classifier LLM used.
  - `embedding_model`: string identifier of the embedding model used (for migration support).

- **Tenancy (future-proofed):**
  - `user_id`: optional string, null in single-user v1.

### 5.3 What is and is not Embedded

- The **only embedded field** is `vllm_description`; its embedding lives in the vector field and is the basis for cosine-similarity retrieval.
- `reasoning` is **stored but not embedded** because it is model interpretation rather than visual evidence; embedding it would create a feedback loop where each analysis's retrieval is increasingly influenced by prior model interpretations rather than ground-truth visual signals.

#### Interview Defense

- One record per image (not per patch) is the chosen granularity because the unit of analysis is the whole image; storing patches separately would let RAG retrieve fragments of prior analyses, which is rarely what the user wants and complicates the schema. Per-patch descriptions are kept inside the parent record's payload for audit.
- `class_list_hash` is exact-match for v1 because partial overlap (Jaccard similarity) introduces complexity without a clear payoff at the demo's scale; future work can add LSH-based partial overlap matching.
- `embedding_model` is stored explicitly because if the embedding model is ever swapped, embeddings across models cannot be compared meaningfully; tagging each embedding with its source model lets the system detect mismatches and run a re-embedding job.
- The `confidence ≥ 3` filter is applied at query time (in addition to being enforced at storage time) as defense in depth: even if low-confidence data leaks into the collection, retrieval still excludes it.

---

## 6. FastAPI Backend Design

### 6.1 Application Structure

- The FastAPI app is initialized at module import time with the `title`, CORS configuration, and rate-limiter setup.
- The compiled LangGraph agent is built once at startup (`@app.on_event("startup")`) and stored on `app.state.graph` so each request can invoke `app.state.graph.ainvoke(...)` without recompiling.
- The Qdrant client is similarly initialized at startup and stored on `app.state.qdrant`.

### 6.2 Middlewares

- **CORS middleware:** Configured to allow requests from the frontend's deployed origin (Vercel/Netlify URL) and from `localhost` during development. No wildcard origins in production.
- **Rate limiting middleware (slowapi):** Applied as a decorator on the `/analyze` and `/analyze/stream` endpoints, limiting to 10 requests per minute per client IP. Not applied to `/health` or `/history`.
- **Request logging middleware (optional):** Logs request method, path, status, and latency to stdout for observability.
- **Exception handler middleware:** A global exception handler that converts unhandled exceptions into HTTP 500 responses with a consistent error schema (`{"error": "...", "details": "..."}`). Validation errors (`pydantic.ValidationError`) become 400 responses.

### 6.3 Routes

#### 6.3.1 `POST /analyze`

- **Purpose:** Run the full classification pipeline synchronously and return a single JSON response.
- **Request format:** `multipart/form-data` (because the request includes a file upload).
  - Form fields:
    - `image`: `UploadFile`, required.
    - `lat`: float, required.
    - `lon`: float, required.
    - `class_list`: JSON-encoded list of strings or comma-separated string, required.
    - `class_descriptions`: optional JSON-encoded dict of class-to-description.
    - `retrieval_radius_km`: optional float, default 5.0.
    - `retrieval_time_window_days`: optional integer.

- **Middlewares applied:**
  - CORS (always applies).
  - Rate limiting (applied as `@limiter.limit("10/minute")` decorator, evaluated before route logic).
  - Exception handler (applies globally).

- **Processing logic:**
  - The route handler first reads `image.read()` to obtain raw bytes.
  - It parses `class_list` (JSON or comma-separated) into a Python list.
  - It builds an `AnalyzeRequest` Pydantic model from the form fields, which performs initial type validation; any Pydantic error is converted to HTTP 400 by the exception handler.
  - It constructs the initial agent state dictionary with all input fields populated, including a freshly generated `analysis_id`.
  - It calls `app.state.graph.ainvoke(initial_state)` and awaits the final state.
  - If the final state contains a fatal `pipeline_errors` entry from the validation node, it returns HTTP 400.
  - Otherwise it extracts `final_result` from the final state and returns it as the JSON response body, conforming to the `AnalyzeResponse` Pydantic model.

- **Response format (`AnalyzeResponse`):**
  - `analysis_id`: string (UUID).
  - `predicted_class`: string.
  - `confidence`: integer 1–5.
  - `reasoning`: string.
  - `synthesized_description`: string.
  - `retrieved_context`: list of `RetrievedContext` objects (each with `timestamp`, `lat`, `lon`, `distance_km`, `predicted_class`, `confidence`, `description_snippet`, `reasoning`).
  - `used_clustering`: boolean.
  - `used_retry`: boolean.
  - `used_clip_fallback`: boolean.
  - `alternative_classes`: optional list of strings.

- **Frontend interaction:**
  - The Analysis page's "Analyze" button submits this request when the streaming endpoint is unavailable or disabled.
  - The response populates the report panel sections all at once, with shimmer fading to content simultaneously.

#### 6.3.2 `POST /analyze/stream`

- **Purpose:** Run the classification pipeline and emit Server-Sent Events as each pipeline stage completes, supporting progressive reveal in the frontend.
- **Request format:** Identical to `/analyze`.
- **Middlewares applied:** Same as `/analyze` (CORS, rate limiting, exception handler).
- **Processing logic:**
  - The route handler builds the initial agent state identically to `/analyze`.
  - It invokes `app.state.graph.astream_events(initial_state, version="v2")` (or `astream` with appropriate configuration) and yields SSE-formatted events as they arrive from the LangGraph runtime.
  - For each node-completion event, it emits a `stage_update` SSE event with payload `{"stage": <node_name>, "status": "complete", "partial_result": <relevant fields>}`.
  - For node-start events, it emits `stage_update` with `"status": "in_progress"`.
  - On error within any node, it emits an `error` SSE event with the node name and error message.
  - After the agent finishes, it emits a `complete` event containing the full `AnalyzeResponse` payload.
  - The response is returned with `media_type="text/event-stream"` and appropriate keepalive headers.

- **Response format:** SSE event stream. Each event is structured as:

  ```
  event: stage_update
  data: {"stage": "retrieve", "status": "complete", "partial_result": {...}}
  ```

- **Frontend interaction:**
  - The Analysis page subscribes to this endpoint when the user clicks Analyze.
  - The frontend maintains a mapping of pipeline stage to report section (see Section 11 of the design spec) and swaps each section from shimmer to content as the corresponding event arrives.

#### 6.3.3 `GET /history`

- **Purpose:** Return prior analyses for display on the Archive page, optionally filtered by location or radius.
- **Request format:** Query parameters.
  - `lat`: optional float.
  - `lon`: optional float.
  - `radius_km`: optional float, default 10.0.
  - `confidence_tier`: optional string (`all`, `high`, `medium`, `low`).
  - `class`: optional string filter on predicted class.
  - `limit`: optional integer, default 50, max 200.
  - `offset`: optional integer for pagination.

- **Middlewares applied:** CORS, exception handler. No rate limiting (read endpoint).

- **Processing logic:**
  - The route handler builds a Qdrant filter dynamically based on supplied parameters.
  - If `lat` and `lon` are provided, a `geo_radius` filter is applied.
  - If `confidence_tier` is provided, the corresponding integer range is added.
  - If `class` is provided, an exact match on `predicted_class` is added.
  - The handler calls Qdrant's `scroll` API (not `search`, since this is a list query without a query vector) with the filter and limit.
  - It maps each Qdrant point to a `RetrievedContext` object with appropriate fields.
  - It returns the list as the JSON response body.

- **Response format:** List of `RetrievedContext` objects (same schema as the embedded list in `AnalyzeResponse`).

- **Frontend interaction:**
  - The Archive page calls this endpoint on page load (with no spatial filter) to populate the map with reticle markers.
  - When the user pans the map and the viewport changes, the page may optionally re-query with the new viewport bounds.
  - The right panel's filter controls (confidence tier, class) trigger a re-query with the corresponding parameters.

#### 6.3.4 `GET /analyses/{analysis_id}`

- **Purpose:** Return the full payload of a single stored analysis, used when the user clicks a marker on the Archive map and the right panel switches to detail view.
- **Request format:** Path parameter `analysis_id` (UUID string).
- **Middlewares applied:** CORS, exception handler.
- **Processing logic:**
  - The route handler queries Qdrant by point ID and returns the full payload mapped to a response model.
  - On not-found, returns HTTP 404.

- **Response format:** A `FullAnalysisResponse` model containing all the fields of `AnalyzeResponse` plus per-patch descriptions and pipeline metadata for the Pipeline Trace section.

- **Frontend interaction:**
  - The Archive page calls this when the user clicks a marker; the response populates the detail-view report.

#### 6.3.5 `GET /health`

- **Purpose:** Report whether the service is up and dependencies are reachable. Used by deployment platforms (Railway, Render) for health checks and by the frontend for a status indicator if needed.
- **Request format:** No parameters.
- **Middlewares applied:** CORS only (no rate limiting).
- **Processing logic:**
  - Returns a JSON object with `status: "ok"`, the configured model identifiers (so the deployed service self-reports its model versions), and a Qdrant connectivity check (a fast `qdrant.get_collections()` call).
- **Response format:** `{"status": "ok", "qdrant": "ok", "vllm_model": "...", "llm_model": "..."}` or `{"status": "degraded", ...}` on partial failure.

### 6.4 Frontend-to-Backend Mapping

- **Overview page CTAs:** Static navigation; no backend interaction.
- **Analysis page "Analyze" button:** Triggers `POST /analyze/stream` (preferred) or `POST /analyze` (fallback) with the configured form data.
- **Analysis page coordinate picker modal:** Pure client-side; no backend interaction (the map tiles are loaded directly from CartoDB).
- **Archive page initial load:** Triggers `GET /history` to populate the map.
- **Archive page filters:** Trigger re-query of `GET /history` with updated parameters.
- **Archive page marker click:** Triggers `GET /analyses/{analysis_id}` for the full detail view.
- **Architecture page:** Static React Flow graph defined in the frontend; no backend interaction in v1 (the node metadata is hardcoded in the frontend rather than fetched).

#### Interview Defense

- Two analyze endpoints (`/analyze` and `/analyze/stream`) are provided rather than only one because the streaming endpoint is the primary user-facing path but the non-streaming endpoint is needed for testing scripts, the seed-data script, and any consumer that doesn't want to handle SSE. Both invoke the same agent, so there is no duplication of business logic.
- A separate `/analyses/{analysis_id}` endpoint exists rather than embedding full detail in the `/history` list response because the list response is intentionally compact (snippets only) for fast map population; full detail is fetched on demand when the user actually wants to read it.
- The `/health` endpoint reports model identifiers so that interviewers (and operators) can see which models are deployed without inspecting environment variables; this is operational maturity at zero cost.
- Routes do not access agent internals directly — they only call `graph.ainvoke` or `graph.astream_events`. This keeps the API surface decoupled from the agent's internal node structure, which means the agent can be refactored without changing the API.

---

## 7. Frontend Structure & Layout

### 7.1 Application Shell

- The application is a single-page React application with four routes.
- A persistent horizontal navigation bar at the top of every page contains the application logo on the left and four nav items: Overview, Analysis, Archive, Architecture.
- There is no vertical sidebar nav.
- The nav is fixed at the top; pages render in the area below.
- Minimum supported viewport is 1280px wide; below this, a "desktop only" message is displayed.

### 7.2 Overview Page

- **Route:** `/`
- **Purpose:** Communicate what the system does in under 30 seconds and direct the visitor to the working pages.
- **Structure:** Single-column scroll layout with three sections.
  - **Hero section:** Full-width, large headline, brief description, two CTAs (primary linking to Analysis, secondary linking to Architecture).
  - **Pipeline section:** A header and three cards in a row describing Visual Reasoning, Retrieval-Augmented Context, and Structured Classification.
  - **Capabilities section:** Two-column block with capability bullets on the left and a supporting visual on the right.
- **Footer:** Minimal footer with links.

### 7.3 Analysis Page

- **Route:** `/analysis`
- **Purpose:** The primary working surface where the user configures and runs a classification.
- **Structure:** Two-column split layout: 40% left panel for inputs, 60% right panel for the report.
- **Left panel (inputs), top to bottom:**
  - Page header (title and one-line subtitle).
  - Upload zone for the satellite image (drag-and-drop or click-to-browse, accepts PNG/JPEG up to 20 MB).
  - "Select Coordinates" button that opens the coordinate picker modal; after selection, displays the chosen coordinates.
  - Class list input (chip-based; classes added with Enter or comma, removable individually).
  - Toggle selector for retrieval radial distance (500m / 1km / 5km / 10km, default 5km).
  - Toggle selector for retrieval temporal depth (6M / 1Y / 3Y / All, default All).
  - Analyze button (full width, disabled until all required inputs are valid; transitions to loading state during analysis).
- **Right panel (report) states:**
  - **Idle (before first analysis):** Centered placeholder with a brief instruction to configure and run an analysis.
  - **Loading (analysis in progress):** Five report sections render as shimmer placeholders, each with approximate final shape so the layout does not shift on content arrival.
  - **Report (analysis complete):** Five sections in order: Headline Result, Visual Evidence, LLM Interpretation, Prior Context, Pipeline Trace.
- **Coordinate picker modal:**
  - Opens on "Select Coordinates" click.
  - Modal width approximately 60% of viewport, centered.
  - Map fills the modal interior; manual lat/lon input fields are positioned in the bottom-right corner of the map area as a glass overlay.
  - Two-way sync: clicking the map updates the inputs; typing valid values updates the map.
  - Confirm button at the bottom-right of the modal; Cancel as a tertiary action.
- **Persistence between analyses:** Class list, radial distance, and temporal depth persist across runs; image and coordinates reset.

### 7.4 Archive Page

- **Route:** `/archive`
- **Purpose:** Geospatial view of all stored analyses for revisiting prior classifications and inspecting RAG context.
- **Structure:** Two-column split: 65% left panel for the map, 35% right panel for list or detail view.
- **Left panel (map):**
  - Full-bleed CartoDB dark_matter tiles with labels.
  - Reticle markers at every stored analysis location.
  - Zoom controls in the top-left corner.
  - Locate-me control below the zoom controls.
  - Viewport status readout in the bottom-left corner showing center coordinates and visible analysis count.
- **Right panel states:**
  - **Default (list view):** Header, filter controls (confidence tier, class type), scrollable list of cards for each prior analysis.
  - **Hover (marker hovered, no click):** Right panel remains in list view; a small glass tooltip appears near the hovered marker showing class, confidence, timestamp.
  - **Detail (marker clicked):** Back button at top, full report for the selected analysis using the same five-section structure as the Analysis page report.
- **Empty state (no analyses stored):** Map renders with no markers; an empty-state message is overlaid in the center inviting the user to start their first analysis.

### 7.5 Architecture Page

- **Route:** `/architecture`
- **Purpose:** Self-documentation of the agent's internal structure for technical visitors.
- **Structure:** Full-viewport React Flow canvas below the nav, with a minimal page header overlaid in the top-left.
- **Graph content:**
  - Nodes correspond to LangGraph agent nodes: `validate`, `preprocess`, `decide_cluster`, `cluster`, `describe_patches`, `synthesize`, `retrieve`, `classify`, `retry_vllm_targeted`, `clip_fallback`, `store`, `format`.
  - Edges show the flow; conditional edges (decision points) are visually distinct from linear edges.
  - Layout is top-down with branches expanding horizontally where conditional edges diverge.
- **Hover interaction:**
  - On hover (200 ms delay), a card appears adjacent to the hovered node showing: function (1–2 sentences), inputs (state fields read), outputs (state fields written), branches (conditional edge targets, if any), failure mode.
  - Hover card dismisses 100 ms after hover-out.
  - No pinning in v1; hover-only.
- **Default view:** Graph fits the viewport on page load with a brief entrance animation as nodes fade in.
- **Controls:** Standard React Flow controls (fit view, zoom in, zoom out) in the bottom-left corner; minimap in the bottom-right.
- **No backend interaction:** Node metadata is hardcoded in the frontend.

#### Interview Defense

- The four pages are organized by audience: Overview is for first-time visitors, Analysis is for users with a task, Archive is for users revisiting their work, Architecture is for technical depth. Mixing these audiences on a single page would dilute each.
- The Analysis page deliberately has no map outside the coordinate picker modal because the page's job is configuring and reviewing a single analysis, not exploration; the map view is the Archive page's domain. Separating these surfaces keeps each page focused.
- The Archive page's hover-vs-click distinction (preview on hover, full detail on click) follows standard map UX patterns from Google Maps and Airbnb, which users already understand without explanation.
- The Architecture page exists primarily as an interview-demo surface: the system has a non-trivial graph that benefits from being explained visually, and an interactive page does that better than a static diagram in a README. It also signals self-awareness about the system's complexity.
