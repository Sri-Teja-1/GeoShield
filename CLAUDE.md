# CLAUDE.md — GeoShield

This file is loaded at the start of every Claude Code session. Read it completely before writing any code.

---

## 1. Project Identity

**GeoShield** is a configurable land-use monitoring system that performs zero-shot classification of satellite imagery against user-defined class taxonomies. It is built as a portfolio piece demonstrating agentic AI systems, retrieval-augmented generation, and cross-modal pipelines. Every architectural decision must be **interview-defensible** — not just functionally correct. The "Interview Defense" sections in `ARCHITECTURE.md` are the canonical source for why decisions were made; do not contradict them.

This is one of three portfolio projects:
- **GeoShield** (this project) — agents, RAG, vision-language pipelines
- **ALP** — custom PyTorch Transformer, model internals, computer vision
- **Promptly** — MERN + LLM API integration

---

## 2. Reference Documents

Three documents live at the project root. **Read them before touching any file they govern.**

| File | Governs |
|------|---------|
| `ARCHITECTURE.md` | Everything: system design, all LangGraph nodes, FastAPI routes, Qdrant schema, frontend structure, tech stack rationale |
| `DESIGN.md` | All frontend visual decisions: colors, typography, spacing, components, motion, page specs |
| `geoshield-preview.html` | The static HTML mockup of the frontend; the React implementation must match its structure and aesthetic |

If there is a conflict between this file and `ARCHITECTURE.md` or `DESIGN.md`, the markdown documents win. This file provides context and instructions; those documents are the spec.

---

## 3. Dev Environment

- **OS:** Windows 11, project on `D:` drive
- **Project root:** `D:\Sriteja Work\3-1 PS\GeoShield_Agent` (confirm with user if this path differs)
- **Python:** Python 3.11.9, managed with `uv`. Project-specific env, NOT the "standard" global env.
- **Node:** Node.js 24.15.0, npm 11.12
- **Package manager (Python):** `uv` — always use `uv add` / `uv run`, never bare `pip install`
- **Package manager (JS):** npm
- **CUDA:** 13.2, cuDNN 9.22, RTX 5070 Ti Laptop GPU 12GB — CLIP runs locally on CPU (small model, acceptable latency on fallback path)
- **Docker:** Docker Desktop, data root on `D:\Docker_images` — Qdrant runs in Docker
- **IDE:** VS Code or IntelliJ via JetBrains Toolbox

---

## 4. Repository Structure

Scaffold this structure exactly. Do not create files outside it without confirming with the user.

```
GeoShield/
├── CLAUDE.md                  ← this file
├── ARCHITECTURE.md
├── DESIGN.md
├── geoshield-preview.html
├── .env.example               ← template; never commit .env
├── .gitignore
│
├── backend/
│   ├── pyproject.toml         ← uv project file
│   ├── .python-version        ← 3.11
│   ├── main.py                ← FastAPI app entry point
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── graph.py           ← LangGraph graph definition and compilation
│   │   ├── state.py           ← AgentState TypedDict, all reducers
│   │   ├── nodes/
│   │   │   ├── __init__.py
│   │   │   ├── validate.py
│   │   │   ├── preprocess.py
│   │   │   ├── cluster.py     ← decide_cluster + cluster nodes
│   │   │   ├── describe.py    ← describe_patches + describe_single_patch
│   │   │   ├── synthesize.py
│   │   │   ├── retrieve.py
│   │   │   ├── classify.py
│   │   │   ├── retry.py       ← retry_vllm_targeted
│   │   │   ├── clip_fallback.py
│   │   │   ├── store.py
│   │   │   └── format.py
│   │   └── edges.py           ← all conditional edge functions
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── analyze.py     ← POST /analyze and POST /analyze/stream
│   │   │   ├── history.py     ← GET /history
│   │   │   ├── analyses.py    ← GET /analyses/{analysis_id}
│   │   │   └── health.py      ← GET /health
│   │   ├── schemas.py         ← all Pydantic request/response models
│   │   └── middleware.py      ← CORS, rate limiting, exception handlers
│   ├── services/
│   │   ├── __init__.py
│   │   ├── qdrant.py          ← Qdrant client init, collection setup
│   │   ├── storage.py         ← object storage abstraction (R2 / local)
│   │   ├── embeddings.py      ← OpenAI text-embedding-3-small wrapper
│   │   ├── vllm.py            ← Groq / Llama 3.2 Vision wrapper
│   │   ├── llm.py             ← Gemini Flash wrapper
│   │   └── clip.py            ← local CLIP model wrapper
│   ├── models/
│   │   ├── __init__.py
│   │   └── types.py           ← PatchData, RetrievedAnalysis, AnalyzeResponse, etc.
│   └── config.py              ← settings from environment variables (pydantic-settings)
│
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── tailwind.config.ts
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx            ← router setup
        ├── styles/
        │   ├── globals.css    ← CSS custom properties from DESIGN.md tokens
        │   └── tailwind.css
        ├── lib/
        │   ├── api.ts         ← typed API client (all backend calls)
        │   └── utils.ts
        ├── types/
        │   └── api.ts         ← TypeScript types mirroring backend Pydantic schemas
        ├── pages/
        │   ├── Overview.tsx
        │   ├── Analysis.tsx
        │   ├── Archive.tsx
        │   └── Architecture.tsx
        ├── components/
        │   ├── layout/
        │   │   └── Nav.tsx
        │   ├── analysis/
        │   │   ├── UploadZone.tsx
        │   │   ├── CoordinatePicker.tsx   ← button + modal
        │   │   ├── ClassInput.tsx         ← chip-based class list input
        │   │   ├── ToggleSelector.tsx     ← reusable toggle for distance/time
        │   │   ├── AnalyzeButton.tsx      ← loading state, progress bar
        │   │   └── report/
        │   │       ├── ReportPanel.tsx    ← idle / loading / report states
        │   │       ├── HeadlineResult.tsx
        │   │       ├── VisualEvidence.tsx
        │   │       ├── LLMInterpretation.tsx
        │   │       ├── PriorContext.tsx
        │   │       └── PipelineTrace.tsx
        │   ├── archive/
        │   │   ├── ArchiveMap.tsx
        │   │   ├── AnalysisList.tsx
        │   │   ├── AnalysisCard.tsx
        │   │   └── MarkerTooltip.tsx
        │   ├── architecture/
        │   │   ├── AgentGraph.tsx
        │   │   └── NodeHoverCard.tsx
        │   └── ui/
        │       ├── ConfidenceIndicator.tsx
        │       ├── Shimmer.tsx
        │       ├── GlassCard.tsx
        │       └── EmptyState.tsx
        └── hooks/
            ├── useAnalysis.ts   ← SSE subscription, pipeline state machine
            └── useArchive.ts    ← archive data fetching and filtering
```

---

## 5. Tech Stack — Do Not Deviate

### Backend
- **FastAPI** + **Uvicorn** (ASGI)
- **LangGraph** — in-process, compiled once at startup on `app.state.graph`
- **Pydantic v2** for all schemas
- **slowapi** for rate limiting
- **qdrant-client** for vector DB
- **langgraph**, **langchain-core** — do not use LangChain chains or agents outside LangGraph
- **Groq SDK** for Llama 3.2 Vision (vLLM)
- **google-generativeai** for Gemini Flash (classifier + synthesis LLM)
- **openai** SDK for `text-embedding-3-small`
- **transformers** + **torch** for local CLIP (CPU, `openai/clip-vit-base-patch32`)
- **Pillow** for image processing
- **boto3** for Cloudflare R2 (S3-compatible); local filesystem behind same interface in dev
- **pydantic-settings** for config from `.env`

### Frontend
- **React 18** + **Vite** + **TypeScript**
- **Tailwind CSS** — utility classes only; all design tokens as CSS custom properties in `globals.css`
- **shadcn/ui** — for Dialog, Tooltip, Accordion primitives. Components are copy-pasted into `src/components/ui/`, not imported from npm.
- **react-router-dom v6** — client-side routing
- **react-leaflet** + **Leaflet.js** — map on Archive page and coordinate picker modal
- **@xyflow/react** (React Flow v12) — Architecture page graph
- **lucide-react** — icons

### Data
- **Qdrant** — Docker in dev, Qdrant Cloud in production. Collection: `analyses`. See `ARCHITECTURE.md` Section 5 for full schema.
- **No relational database.** Qdrant handles both vectors and metadata.
- **Cloudflare R2** in production, local filesystem in dev. Both behind the same `storage.py` interface.

---

## 6. Environment Variables

These go in `.env` (gitignored). Always read from `config.py` via pydantic-settings, never hardcoded.

```
# Models
GROQ_API_KEY=
GOOGLE_API_KEY=
OPENAI_API_KEY=

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=                    # empty for local Docker

# Storage
STORAGE_BACKEND=local              # "local" or "r2"
LOCAL_STORAGE_PATH=./data/images
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET_NAME=

# App
FRONTEND_ORIGIN=http://localhost:5173
RATE_LIMIT=10/minute
```

---

## 7. Design System Constraints (Non-Negotiable)

The full spec is in `DESIGN.md`. These are the rules most likely to be violated — treat them as hard constraints.

**Colors:** All tokens are defined in `frontend/src/styles/globals.css` as CSS custom properties. Never use a raw hex value in a component; always reference a token. The full token set is in `DESIGN.md` Section 3.

**No 1px borders for sectioning.** Tonal surface shifts only. Borders allowed only on form inputs (`outline_variant` at 40% opacity).

**No pure black.** Use `--surface-container-lowest` (`#0b0e14`).

**Typography:** Space Grotesk for display/headlines, Inter for body/data, Inter tabular-nums for coordinates and timestamps. Load both from Google Fonts in `index.html`.

**Shimmer:** Left-to-right sweep only, 1500ms linear infinite. Never static pulse, never spinner. This is the unified loading language for the entire app.

**Confidence states:** Always paired — semantic glow on the section + colored dots + text label ("High" / "Medium" / "Low"). Never color alone.

**Model-generated content labeling:** Classifier reasoning → "LLM Interpretation". Retrieved context cards → "Model-generated reasoning from prior analysis". Confidence scores → paired with semantic label. See `DESIGN.md` Section 2.

**Glassmorphism:** Floating overlays (map controls, hover cards, coordinate input panel) use `surface_variant` at 60% opacity + `backdrop-filter: blur(32px)`. See `DESIGN.md` Section 3.

**Motion:** 200ms ease-out entering, 150ms for micro-interactions. No springs, no parallax, no multi-second animations outside shimmer. See `DESIGN.md` Section 7.

---

## 8. LangGraph Agent — Key Implementation Rules

Read `ARCHITECTURE.md` Sections 2 and 4 in full before implementing any node. Highlights:

**State:** Flat `TypedDict` in `agent/state.py`. `patch_descriptions` and `pipeline_errors` use `Annotated[List[str], operator.add]` reducers for parallel-safe appending. `effective_class_list` is always what nodes downstream of clustering use — never `class_list` directly.

**Parallelism:** The `describe_patches` node uses LangGraph's `Send` API to fan out to `describe_single_patch` worker nodes. Concurrency capped at 4 in-flight calls. See Section 2.4.

**Conditional edges** (implement as edge functions in `edges.py`, not as nodes):
- After `decide_cluster`: route to `cluster` or directly to `describe_patches`
- After `classify`: confidence ≥ 4 → `store`; confidence 2–3 and not retried → `retry_vllm_targeted`; confidence ≤ 1 → `clip_fallback`
- After `classify` post-retry: confidence ≥ 3 → `store`; else → `clip_fallback`

**Confidence gate logic:** Implemented as a conditional edge function reading `confidence` and `used_retry` from state. See Section 2.8.

**Storage guard:** The `store` node only writes to Qdrant if `confidence >= 3`. Always writes image to object storage regardless. Storage failures are non-fatal — log and continue.

**Graph is compiled once at startup** and stored on `app.state.graph`. Do not recompile per request.

---

## 9. FastAPI — Key Implementation Rules

Read `ARCHITECTURE.md` Section 6 in full. Highlights:

**Two analyze endpoints:** `POST /analyze` (sync, `graph.ainvoke`) and `POST /analyze/stream` (SSE, `graph.astream_events`). Both invoke the same compiled graph. No business logic in route handlers — handlers build initial state, call the graph, return results.

**Request format:** `multipart/form-data` for both analyze endpoints (file upload + form fields). `class_list` arrives as JSON-encoded string or comma-separated; parse defensively.

**SSE format:**
```
event: stage_update
data: {"stage": "retrieve", "status": "complete", "partial_result": {...}}
```
Emit `in_progress` on node start, `complete` on node end, `error` on node failure, `complete` (with full `AnalyzeResponse`) when the graph finishes.

**CORS:** Allow `FRONTEND_ORIGIN` from env + `localhost:5173`. No wildcard in production.

**Rate limiting:** slowapi, 10/minute per IP on `/analyze` and `/analyze/stream` only. Not on `/health` or `/history`.

---

## 10. Frontend — Key Implementation Rules

**API client (`lib/api.ts`):** All backend calls go through typed functions here. No `fetch` calls scattered in components. The SSE subscription is in `hooks/useAnalysis.ts` using the browser's `EventSource` API.

**TypeScript types (`types/api.ts`):** Mirror every Pydantic response model from the backend. Keep in sync manually when schemas change.

**Routing:** Four routes via react-router-dom. Nav is always present, fixed top. Below 1280px, show desktop-only message.

**Report panel states:** The `ReportPanel` component has three states — idle, loading (all five sections shimmer), report (sections populated). The section-to-stage mapping for progressive reveal is in `DESIGN.md` Section 11. Headline Result holds shimmer until the confidence gate finalizes.

**Map:** `react-leaflet` on Archive page and inside the Coordinate Picker Modal. CartoDB dark_matter tiles: `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png`. Reticle markers are SVG, not default Leaflet pins. See `DESIGN.md` Section 8.

**Architecture graph:** `@xyflow/react` with dagre layout. Nodes styled per `DESIGN.md` Section 9.4. Node data is hardcoded in the frontend — no backend call. Hover cards use floating-ui for placement (right of node, flip left if overflow).

**shadcn/ui:** Only use for Dialog (Coordinate Picker), Tooltip, and Accordion (Pipeline Trace expand/collapse). Init with `npx shadcn@latest init` and add components individually. Apply Orbital Lens tokens, not shadcn defaults.

---

## 11. Implementation Phases

Work through phases in order. **Do not start the next phase until the user confirms the current phase is complete.** After completing each phase, write a brief summary of what was built and what the user should verify.

---

### Phase 0 — Project Scaffold
**Goal:** Correct directory structure and tooling config. No implementation logic yet.

Tasks:
1. Create `backend/` directory with `pyproject.toml` (uv project, Python 3.11), empty `__init__.py` files in all packages, and all module files as empty stubs with correct imports declared.
2. Create `frontend/` with `package.json`, `vite.config.ts`, `tsconfig.json`, `tailwind.config.ts`. Install deps: react, react-dom, react-router-dom, react-leaflet, leaflet, @xyflow/react, lucide-react, tailwindcss, and type packages.
3. Create `frontend/src/styles/globals.css` with **all** CSS custom properties from `DESIGN.md` Sections 3, 4, 5 as `--token-name: value` on `:root`.
4. Create `.env.example` with all variables from Section 6 above.
5. Create `.gitignore` covering `.env`, `__pycache__`, `.venv`, `node_modules`, `dist`, `data/`.

**Verify:** `uv run uvicorn main:app` starts (no routes yet). `npm run dev` in `frontend/` starts Vite dev server. No TypeScript errors on empty stubs.

---

### Phase 1 — Backend Data Layer
**Goal:** Qdrant collection initialized, all Pydantic schemas defined, config loading from env.

Tasks:
1. Implement `config.py` — pydantic-settings `Settings` class loading all env vars from Section 6.
2. Implement `models/types.py` — all domain types: `PatchData`, `RetrievedAnalysis`, `AnalyzeRequest`, `AnalyzeResponse`, `RetrievedContext`, `FullAnalysisResponse`, `HealthResponse`.
3. Implement `api/schemas.py` — all Pydantic request/response models for FastAPI routes. These mirror `models/types.py` but may differ in serialization (e.g., datetime formatting).
4. Implement `services/qdrant.py` — client init from config, `create_collection_if_not_exists()` function that sets up the `analyses` collection with the exact schema from `ARCHITECTURE.md` Section 5 (vector config, all payload indexes).
5. Implement `services/storage.py` — `StorageBackend` interface with `save_image(image_bytes, image_hash) -> str` and `get_image_url(image_ref) -> str`. Two implementations: `LocalStorage` and `R2Storage`. Factory function reads `STORAGE_BACKEND` from config.

**Verify:** Running `uv run python -c "from services.qdrant import create_collection_if_not_exists; create_collection_if_not_exists()"` with Docker Qdrant running creates the collection. Collection has correct vector dimensions and payload indexes.

---

### Phase 2 — Agent State and Service Wrappers
**Goal:** LangGraph state schema fully defined; all external service wrappers implemented and independently testable.

Tasks:
1. Implement `agent/state.py` — `AgentState` TypedDict with every field from `ARCHITECTURE.md` Section 4.2. Apply `Annotated[List[str], operator.add]` to `patch_descriptions` and `pipeline_errors`. Import `operator`.
2. Implement `services/embeddings.py` — `embed_text(text: str) -> list[float]` using OpenAI `text-embedding-3-small`. Cache the client on module load.
3. Implement `services/vllm.py` — `describe_image(image_bytes: bytes, prompt: str) -> str` using Groq SDK with `llama-3.2-11b-vision-preview` (or latest available Llama 3.2 Vision on Groq). Handle transient errors with one retry.
4. Implement `services/llm.py` — `classify_structured(prompt: str) -> dict` using `google.generativeai` with Gemini Flash in JSON mode. `synthesize(prompt: str) -> str` for free-text synthesis calls.
5. Implement `services/clip.py` — load `openai/clip-vit-base-patch32` from HuggingFace on module import (CPU). `classify_with_clip(image_bytes: bytes, class_list: list[str]) -> tuple[str, float]` returns the best class and its cosine similarity score.

**Verify:** Each service wrapper has a `if __name__ == "__main__"` test block or a `tests/` file. Run manually to confirm API keys work and models respond.

---

### Phase 3 — LangGraph Nodes (Happy Path)
**Goal:** The happy path through the agent works end-to-end: validate → preprocess → describe → synthesize → retrieve → classify → store → format.

Implement nodes in this order, one file at a time. Each node is a function `async def node_name(state: AgentState) -> dict` returning partial state updates.

1. `nodes/validate.py` — full logic from Section 2.1: PIL validation, coordinate ranges, class list checks, SHA-256 hashes, UUID generation.
2. `nodes/preprocess.py` — EXIF correction, RGB conversion, dimension check (reject < 224px), tiling logic (passthrough ≤ 1024px, 512px patches with 10% overlap for larger), returns `processed_patches`, `was_tiled`, `num_patches`.
3. `nodes/describe.py` — `describe_patches` fan-out node using `Send` API; `describe_single_patch` worker calling `services/vllm.py`. Cap concurrency at 4.
4. `nodes/synthesize.py` — passthrough if single patch; LLM call with positional synthesis prompt if tiled.
5. `nodes/retrieve.py` — embed description, build Qdrant filter (geo + class_list_hash + confidence floor + optional time window), query top-3, progressive relaxation on zero results.
6. `nodes/classify.py` — build structured prompt with retrieved context, call Gemini in JSON mode, validate output is in `effective_class_list`.
7. `nodes/store.py` — check `confidence >= 3`, write image to storage, write Qdrant point.
8. `nodes/format.py` — assemble `AnalyzeResponse` from state.
9. `nodes/cluster.py` — `decide_cluster` node (pure logic, no LLM); skip `cluster` node for now (stub that sets `effective_class_list = class_list`).
10. `edges.py` — all conditional edge functions. `route_after_classify` handles the confidence gate.
11. `agent/graph.py` — wire all nodes and edges. Compile with `graph.compile()`. Export `build_graph() -> CompiledGraph`.

**Verify:** Write a test script `backend/test_pipeline.py` that submits a real satellite image (any JPEG will do), lat/lon, and 2–3 classes, and calls `graph.ainvoke(initial_state)`. The pipeline should complete and return a `final_result` dict. Check that Qdrant has a new point after running.

---

### Phase 4 — Agent Branches (Clustering, Retry, CLIP Fallback)
**Goal:** All conditional branches are implemented and reachable.

1. Complete `nodes/cluster.py` — `cluster` node with LLM-based meta-class generation, cache by `class_list_hash`. Implement `hierarchical_d1` (10–25 classes) and `hierarchical_d2` (26+ classes) strategies.
2. Implement `nodes/retry.py` — `retry_vllm_targeted` node: build focused disambiguation prompt from `alternative_classes` and `ambiguity_reason`, re-run `describe_patches` → `synthesize` subgraph, set `used_retry = True`.
3. Implement `nodes/clip_fallback.py` — call `services/clip.py`, set `confidence = 2`, `used_clip_fallback = True`.
4. Update `edges.py` to handle the post-retry routing rule (confidence ≥ 3 → store, else → clip_fallback).
5. Update `agent/graph.py` with the `decide_cluster` conditional edge and the retry/fallback branches.

**Verify:** Test each branch explicitly:
- Submit 12 classes → clustering should activate
- Mock `classify` to return confidence 2 → retry should fire
- Mock `classify` to return confidence 0 → CLIP fallback should fire
Check `used_clustering`, `used_retry`, `used_clip_fallback` in the returned state.

---

### Phase 5 — FastAPI Routes
**Goal:** All four routes implemented and serving correct responses.

1. Implement `main.py` — FastAPI app init, CORS middleware, rate limiter setup, startup event that calls `build_graph()` and stores on `app.state.graph`, calls `create_collection_if_not_exists()`, includes all routers.
2. Implement `api/middleware.py` — CORS config (from `FRONTEND_ORIGIN` env var + localhost), slowapi limiter, global exception handler (unhandled → 500, `pydantic.ValidationError` → 400).
3. Implement `api/routes/analyze.py`:
   - `POST /analyze` — multipart form, call `graph.ainvoke`, return `AnalyzeResponse`
   - `POST /analyze/stream` — SSE with `graph.astream_events`, emit `stage_update` events per node, `complete` at end
4. Implement `api/routes/history.py` — `GET /history` with optional geo filter, confidence tier, class filter, pagination via Qdrant `scroll`.
5. Implement `api/routes/analyses.py` — `GET /analyses/{analysis_id}` fetching full point payload, 404 on miss.
6. Implement `api/routes/health.py` — `GET /health` checking Qdrant connectivity, returning model identifiers from config.

**Verify:** Use Postman or `curl` to hit each endpoint. The `/analyze` endpoint should complete a real classification. The `/analyze/stream` endpoint should emit a sequence of SSE events in the browser's DevTools Network tab. `/history` should return stored analyses. `/health` should return `{"status": "ok"}`.

---

### Phase 6 — Frontend Foundation
**Goal:** React app running with routing, nav, design tokens, and static page shells.

1. Confirm `globals.css` has all tokens from Phase 0 as CSS custom properties. Reference in `tailwind.config.ts` via `var(--token-name)` for any tokens used as Tailwind values.
2. Implement `App.tsx` with react-router-dom `BrowserRouter` and routes for all four pages.
3. Implement `components/layout/Nav.tsx` — fixed top nav, logo left, four links, active state with `primary` color + 1px underline, inactive `on_surface_variant`. Below 1280px, return desktop-only message instead of routes.
4. Implement `lib/api.ts` — typed async functions for all five backend endpoints (`analyze`, `history`, `getAnalysis`, `health`). Base URL from `import.meta.env.VITE_API_URL`.
5. Implement `types/api.ts` — TypeScript interfaces mirroring all Pydantic response models.
6. Implement `hooks/useAnalysis.ts` — manages the SSE connection lifecycle, maps incoming stage events to a pipeline state object, exposes `{ submit, status, result, error }`.
7. Implement page shells: `Overview.tsx`, `Analysis.tsx`, `Archive.tsx`, `Architecture.tsx` — each rendering a placeholder `<h1>` with the page name for now.

**Verify:** `npm run dev` loads. Nav links route to each page. `tsc --noEmit` passes.

---

### Phase 7 — Analysis Page
**Goal:** The Analysis page is fully functional: inputs work, pipeline runs, report renders with progressive reveal.

Build in this order:

1. `components/ui/Shimmer.tsx` — left-to-right sweep shimmer component. Takes `className` for sizing.
2. `components/ui/ConfidenceIndicator.tsx` — 5 dots, semantic color by score, paired text label.
3. `components/analysis/ToggleSelector.tsx` — sliding pill toggle for options. Used for distance and time.
4. `components/analysis/UploadZone.tsx` — drag-and-drop, click-to-browse, file selected state, validation errors.
5. `components/analysis/ClassInput.tsx` — chip-based input, Enter/comma to add, × to remove, min 2 / max 50.
6. `components/analysis/CoordinatePicker.tsx` — button + shadcn Dialog containing react-leaflet map + glass panel with lat/lon inputs. Two-way sync. CartoDB dark_matter tiles.
7. `components/analysis/AnalyzeButton.tsx` — loading state with shimmer sweep + SSE progress bar at bottom edge.
8. `components/analysis/report/HeadlineResult.tsx` — predicted class, confidence indicator, semantic glow, timestamp.
9. `components/analysis/report/VisualEvidence.tsx` — image display (or patch grid), synthesized description, accordion for per-patch descriptions.
10. `components/analysis/report/LLMInterpretation.tsx` — reasoning text, alternatives subsection if confidence < 4, model-generated caption.
11. `components/analysis/report/PriorContext.tsx` — retrieval params summary, prior analysis cards, relaxation note, empty state.
12. `components/analysis/report/PipelineTrace.tsx` — collapsible accordion, metadata fields, latency breakdown.
13. `components/analysis/report/ReportPanel.tsx` — orchestrates idle / loading / report states. Consumes `useAnalysis` hook. Implements section-to-stage progressive reveal per `DESIGN.md` Section 11.
14. `pages/Analysis.tsx` — two-column layout, all input components left, `ReportPanel` right.

**Verify:** Full end-to-end: upload an image, pick coordinates on the map, add classes, click Analyze. Watch SSE events arrive and sections shimmer-to-content progressively. Confirm confidence glow matches score. Confirm all five sections render.

---

### Phase 8 — Archive Page
**Goal:** Archive page shows stored analyses on a map with list and detail views.

1. `components/archive/ArchiveMap.tsx` — react-leaflet map with CartoDB tiles, SVG reticle markers, glass-panel overlays (zoom, locate-me, viewport status readout).
2. `components/archive/AnalysisCard.tsx` — card in list view: class, confidence indicator, description snippet, timestamp, locate link.
3. `components/archive/AnalysisList.tsx` — scrollable list with filter controls (confidence tier toggle, class dropdown). Calls `GET /history`.
4. `components/archive/MarkerTooltip.tsx` — glass card tooltip on marker hover.
5. `hooks/useArchive.ts` — fetches history, manages filter state, exposes `{ analyses, filters, setFilters, loading }`.
6. `pages/Archive.tsx` — 65/35 split, map left, list/detail right. Implement list → detail → back state transitions. On marker or card click, fetch `GET /analyses/{id}` and render full report using the same report section components from Phase 7. Empty state when no analyses exist.

**Verify:** With analyses in Qdrant from Phase 5 testing, the Archive page loads markers on the map, the list renders on the right, clicking a marker loads the detail report, Back returns to list.

---

### Phase 9 — Architecture Page
**Goal:** Interactive React Flow graph of the LangGraph agent with hover cards.

1. Define node data in `Architecture.tsx` — one entry per LangGraph node, each with: id, label, function description (1–2 sentences), inputs (state field names), outputs (state field names), branches (if conditional), failure mode. Source from `ARCHITECTURE.md` Section 4.3.
2. Define edges — connect nodes per the topology in `ARCHITECTURE.md` Section 4.4. Conditional edges use dashed `on_surface_variant` stroke; happy-path edges use solid `primary` stroke.
3. `components/architecture/NodeHoverCard.tsx` — glass card, 320px fixed width, content structure from `DESIGN.md` Section 8. Uses floating-ui for right/left placement. 200ms hover-in delay, 100ms hover-out delay, 150ms fade.
4. `components/architecture/AgentGraph.tsx` — React Flow canvas with dagre layout, custom node components, hover card integration, standard controls bottom-left, minimap bottom-right (glass card style), entrance animation (nodes fade in with y-offset, staggered 40ms).
5. `pages/Architecture.tsx` — full-viewport canvas, minimal glass-card header overlaid top-left.

**Verify:** Graph renders all 12 nodes. Edges show correct topology with visual distinction for conditional edges. Hovering a node shows the hover card with correct content after 200ms. Card disappears 100ms after hover-out. Graph fits viewport on load.

---

### Phase 10 — Polish and Integration
**Goal:** All pages work together, no console errors, no visual regressions, design fidelity spot-checked against `geoshield-preview.html`.

1. Open `geoshield-preview.html` in a browser. Diff visually against the React implementation. Align any tokens, spacing, or layout that has drifted.
2. Check all color token references. No raw hex values in components.
3. Check all copy strings against `DESIGN.md` Section 2 (preferred vs. avoid table).
4. Add `<title>` and meta tags to `index.html`.
5. Add `VITE_API_URL` to a `.env.local` for the frontend pointing to `http://localhost:8000`.
6. Confirm `npm run build` produces no TypeScript errors.
7. Write `backend/seed.py` — a script that submits 5–10 test images to `POST /analyze` to populate Qdrant for demo purposes.

**Verify:** Run `seed.py`. Open the app fresh. Archive page shows seeded analyses. Run a new analysis from scratch. Full pipeline completes. Architecture page graph is readable and interactive. No console errors in any page.

---

## 12. Rules for Every Session

1. **Read before writing.** If you are about to implement something in `ARCHITECTURE.md` or `DESIGN.md`, re-read the relevant section first. Do not rely on memory.
2. **One phase at a time.** Confirm completion with the user before starting the next phase.
3. **No unilateral tech swaps.** Do not substitute libraries, change the stack, or skip components without explicitly flagging it and waiting for approval.
4. **Interview defensibility.** If a decision is not in the spec and you have to make a judgment call, prefer the option that is easier to explain in an interview. Document the decision in a comment.
5. **Errors are non-fatal at the node level.** Individual node failures should log to `pipeline_errors` and continue where possible — never crash the pipeline on a recoverable error.
6. **Keep the git history clean.** Commit after each phase completes. Commit message format: `phase N: brief description`.
7. **Never commit `.env`.** The `.gitignore` must cover it; verify before every commit.
8. **Surface blockers immediately.** If a library doesn't behave as expected, an API key is missing, or the Qdrant schema needs adjustment, stop and flag it rather than working around it silently.
