# Design System Specification: The Orbital Lens

## 1. Overview & Creative North Star

The "Orbital Lens" is the creative North Star for this design system. It moves away from the cluttered, dashboard-heavy aesthetics typical of geospatial tools, opting instead for a **High-End Editorial Technicality**.

This system treats satellite imagery not as a series of spreadsheets, but as a curated gallery of high-precision intelligence. We break the "template" look through **intentional asymmetry**, where data panels may overlap map viewports, and **tonal depth**, where information is revealed through layers of light rather than boxes. The experience should feel like a high-altitude observer: silent, precise, and authoritative.

The voice is **slightly editorial** — technically grounded, but written with a measured confidence. We describe what the system does, not what we wish it did.

---

## 2. Voice & Copy Guidelines

Copy should be **direct, technically accurate, and free of marketing inflation**. The aesthetic carries the premium feel; copy should not try to compete with it.

### Core Principles

- **Describe capabilities, not claims.** "Zero-shot classification without task-specific training" is a capability. "98.4% accuracy" without a benchmark is a claim to avoid.
- **Use precise terminology.** Say "image" instead of "telemetry" unless the system actually processes telemetry. Say "upload" instead of "ingest" unless there's a real ingestion pipeline.
- **Prefer short, declarative sentences.** Editorial does not mean ornate.
- **American English** across the app (analyze, color, center).

### Common String Patterns

| Context | Preferred | Avoid |
|---------|-----------|-------|
| Primary CTA | "Analyze" | "Execute Orbital Analysis" |
| Upload prompt | "Drop a satellite image here, or click to browse" | "Initialize Data Ingestion" |
| Format hint | "PNG or JPEG, up to 20MB" | "GeoTIFF, NITF, or raw orbital streams" |
| Status indicator | Remove unless meaningful | "SYSTEM ONLINE • COVERAGE ACTIVE" |
| Archive empty state | "No analyses yet" | "Awaiting telemetry" |
| Tagline | "Zero-shot geospatial classification with vision-language models and retrieval-augmented context" | "Classified data streams analyzed in real-time" |

### Labels for Model-Generated Content

Any content produced by the LLM that is surfaced to the user must be labeled as model-generated, because it is interpretation, not ground truth.

- The classifier's reasoning is labeled **"LLM Interpretation"**, not "LLM Reasoning" or "Analysis"
- Cards surfacing retrieved context should note "Model-generated reasoning from prior analysis"
- Confidence scores should be paired with their semantic label ("Confidence: High") so users understand these are model self-assessments

---

## 3. Color System

The palette is rooted in the deep void of low-earth orbit, using charcoals and electric accents to guide the eye toward critical information. Token naming follows Material Design 3 conventions.

### Core Palette

| Token | Hex | Role |
|-------|-----|------|
| `primary` | `#adc6ff` | Active states, critical data paths, primary actions |
| `primary_container` | `#2d3f6b` | Gradient partner for primary; hover backgrounds |
| `on_primary` | `#0b0e14` | Text on primary-colored surfaces |
| `secondary` | `#b7c8e1` | Supporting information, deactivated UI |
| `on_secondary` | `#10131a` | Text on secondary-colored surfaces |
| `tertiary` | `#4edea3` | Success states, confirmed detections |
| `on_tertiary` | `#0b0e14` | Text on tertiary-colored surfaces |

### Surface Hierarchy

Surfaces nest through tonal shifts, not borders. Each step up the hierarchy is a subtle lightening.

| Token | Hex | Use |
|-------|-----|-----|
| `surface_container_lowest` | `#0b0e14` | Base canvas, map background, landing page |
| `surface` | `#10131a` | Default app background |
| `surface_container_low` | `#141822` | Primary content panels |
| `surface_container` | `#1a1f2a` | Cards, elevated content |
| `surface_container_high` | `#222834` | Interactive widgets, toggles |
| `surface_container_highest` | `#2a3140` | Topmost interactive surfaces |
| `surface_variant` | `#1a1f2a` | Glassmorphism base (with transparency) |

### On-Surface Text

| Token | Hex | Use |
|-------|-----|-----|
| `on_surface` | `#e6eaf2` | Primary text |
| `on_surface_variant` | `#a8b1c4` | Secondary text, labels, metadata |
| `outline` | `#3a4254` | Subtle visual separation if absolutely required |
| `outline_variant` | `#2a3140` | Ghost Border base; used at 15% opacity |

### Semantic Colors

For state communication that color alone cannot carry — always pair with a text label or icon.

| Token | Hex | Use |
|-------|-----|-----|
| `success` | `#4edea3` | High confidence (4–5), confirmed states; same as `tertiary` |
| `warning` | `#ffc76b` | Medium confidence (3), cautionary states |
| `danger` | `#ff7b7b` | Low confidence (1–2), error states, anomaly flags |

### The "No-Line" Rule

1px solid borders are **prohibited for sectioning components**. Boundaries are defined through background color shifts between surface tiers. A side panel at `surface_container_low` sits directly against a `surface` background; the tonal shift provides containment.

Exception: **form inputs may use borders** at `outline_variant` with 40% opacity. This is a usability accommodation; sectioning elements remain borderless.

### The Ghost Border

When separation is required for accessibility in high-density data views, use `outline_variant` at **15% opacity**. It should be felt, not seen.

### The Glass & Gradient Rule

Floating overlays (map controls, coordinate readouts, node hover cards) must use **Glassmorphism**: semi-transparent `surface_variant` (roughly 60% opacity) with a 20–40px backdrop-blur.

Primary action buttons use a subtle linear gradient from `primary` to `primary_container` at 135° to provide a "luminous" quality that mimics light refracting through a lens.

### Semantic Glow (for confidence states)

Confidence states apply a soft outer glow to the Headline Result section. This replaces what would conventionally be a colored border — keeping the aesthetic intact while still communicating state.

| Confidence | Glow Color | Spec |
|------------|------------|------|
| High (4–5) | `success` | 15% opacity, 24px blur, 0 offset |
| Medium (3) | `warning` | 15% opacity, 24px blur, 0 offset |
| Low (1–2) | `danger` | 15% opacity, 24px blur, 0 offset |

Confidence indicators (dots) take the same color as the glow, reinforcing the state through redundant channels.

---

## 4. Typography

A dual-font system balances editorial authority with technical precision.

### Font Stacks

- **Display & Headlines**: Space Grotesk. Geometric apertures feel architectural and modern.
- **Body & Data**: Inter. Tall x-height ensures readability at small scales.
- **Technical Readouts**: Inter with `font-variant-numeric: tabular-nums` for coordinates, timestamps, and any numeric data in columnar layouts.

### Type Scale

| Token | Font | Size | Line Height | Weight | Use |
|-------|------|------|-------------|--------|-----|
| `display-lg` | Space Grotesk | 3.75rem (60px) | 1.1 | 700 | Hero headlines |
| `display-md` | Space Grotesk | 3rem (48px) | 1.15 | 700 | Page headlines |
| `display-sm` | Space Grotesk | 2.25rem (36px) | 1.2 | 600 | Section headers |
| `headline-lg` | Space Grotesk | 1.875rem (30px) | 1.25 | 600 | Card titles |
| `headline-md` | Space Grotesk | 1.5rem (24px) | 1.3 | 600 | Subsection headers |
| `headline-sm` | Space Grotesk | 1.25rem (20px) | 1.35 | 600 | Component headers |
| `body-lg` | Inter | 1.125rem (18px) | 1.5 | 400 | Lead paragraphs |
| `body-md` | Inter | 1rem (16px) | 1.5 | 400 | Default body |
| `body-sm` | Inter | 0.875rem (14px) | 1.5 | 400 | Secondary content |
| `label-lg` | Inter | 0.875rem (14px) | 1.3 | 500 | Button text |
| `label-md` | Inter | 0.75rem (12px) | 1.3 | 500 | Field labels, small caps |
| `label-sm` | Inter | 0.6875rem (11px) | 1.3 | 500 | Meta labels, badges |
| `mono-md` | Inter tabular-nums | 1rem (16px) | 1.4 | 400 | Coordinates, large readouts |
| `mono-sm` | Inter tabular-nums | 0.875rem (14px) | 1.4 | 400 | Timestamps, small readouts |

Small-caps labels (e.g., "FILTERS", "VIEWPORT STATUS") use `label-md` with `letter-spacing: 0.08em` and uppercase transform.

---

## 5. Spacing Scale

Consistent spacing is more important than any specific value. Commit to the scale.

| Token | Value | Use |
|-------|-------|-----|
| `xs` | 0.25rem (4px) | Icon-to-text gaps, tight inline spacing |
| `sm` | 0.5rem (8px) | Compact padding inside chips, dense list items |
| `md` | 0.75rem (12px) | Default inline gaps, small component padding |
| `lg` | 1rem (16px) | Standard component padding |
| `xl` | 1.5rem (24px) | Section padding, card padding |
| `2xl` | 2.5rem (40px) | Section gaps within a page |
| `3xl` | 4rem (64px) | Major layout gaps, landing page section breaks |

Geospatial data should breathe — prefer `xl` or larger gaps for primary layout sections.

---

## 6. Elevation & Depth

Elevation is an expression of light, not physics.

### Layering Principle

Depth is achieved by stacking surface-container tiers. Place a `surface_container_highest` element on top of a `surface_container` to create a natural lift.

### Ambient Shadows

Shadows should feel like ambient occlusion, not drop shadows.

- Blur: 32px to 64px
- Opacity: 4% to 8%
- Color: Tinted version of `on_surface` (deep blue-gray), never pure black

Standard shadow token: `0 16px 48px rgba(230, 234, 242, 0.06)` for elevated cards.

### Prohibitions

- No pure black (`#000000`). Use `surface_container_lowest` (`#0b0e14`).
- No high-opacity borders. Tonal shifts first; ghost borders only if accessibility requires.
- No harsh, small-radius shadows. They make the UI feel like a generic SaaS template.

---

## 7. Motion Language

Motion is restrained and technical. The system feels precise, not playful.

### Timing & Easing

- **Default transition**: 200ms, `ease-out` for entering, `ease-in` for exiting
- **Micro-interactions** (hover, focus): 150ms, `ease-out`
- **Layout changes** (modal open, panel swap): 250ms, `cubic-bezier(0.2, 0, 0, 1)`
- **Shimmer sweep**: 1500ms, linear, infinite

### Hover Behavior

- Color shifts are preferred over scale or translate
- If scale is used (e.g., map markers expanding on hover), limit to `1.0 → 1.05` max
- Never use bouncy springs or overshoot easing

### Tooltip & Hover Card Timing

- **Hover-in delay**: 200ms (prevents accidental triggers)
- **Hover-out delay**: 100ms (prevents flicker on brief mouseouts)
- **Fade duration**: 150ms

### Loading & Shimmer

Shimmer is the system's unified visual language for "something is processing."

- **Direction**: Left-to-right sweep only (never static pulse)
- **Implementation**: A low-opacity linear gradient (roughly 10% `on_surface`) animates across the element's background
- **Duration**: 1500ms, linear, infinite loop
- **Applied to**: Analyze button during processing, report section placeholders during analysis

### Progressive Reveal

As the pipeline completes stages and SSE events arrive, shimmer sections swap to content:

- **Swap duration**: 200ms fade-in, `ease-out`
- All fields within a section populate simultaneously (section is the atomic unit)
- The Headline Result section swaps last, after the confidence gate has finalized (including any retries)

### Prohibitions

- No parallax effects
- No physics-based motion (springs, inertia)
- No multi-second animations outside of shimmer loops

---

## 8. Components

### Buttons

**Primary**
- Background: linear gradient from `primary` to `primary_container` at 135°
- Text: `on_primary`, `label-lg`
- Padding: `md` vertical, `xl` horizontal
- Radius: `md` (0.375rem)
- No border

**Secondary**
- Background: transparent
- Border: `primary` at 40% opacity (Ghost Border)
- Text: `primary`, `label-lg`

**Tertiary**
- Purely typographic
- Text: `primary`, `label-lg`
- No background, no border
- Used for inline links and low-emphasis actions

### Loading Button State (Analyze Button)

When analysis is running:

- Button remains in its container; no layout shift
- Background opacity: 60%
- Cursor: `not-allowed`
- Click events disabled
- Text changes to "Analyzing..."
- A left-to-right sweep shimmer animates across the button surface (1500ms, linear, infinite)
- A 2px-tall progress bar at the bottom edge of the button fills in `primary` color as SSE stage events arrive (0% → 100% over the pipeline's execution)
- On completion, the button briefly pulses `tertiary` for 300ms, then returns to default state

### Toggle Selectors (Distance, Time)

Avoid standard radio buttons. Toggles are capsules of `surface_container_high` containing their options. The active option is a glass pill in `primary` that slides beneath the text on selection.

- Capsule radius: `md` (0.375rem)
- Active pill: `primary` at 90% opacity, same radius
- Transition: pill slides 200ms, `cubic-bezier(0.2, 0, 0, 1)`
- Inactive text: `on_surface_variant`
- Active text: `on_primary`

### Upload Zone

- Background: `surface_container_lowest`
- Border: dashed Ghost Border at `sm` (0.25rem) radius
- Padding: `2xl` vertical, `xl` horizontal
- Centered upload icon and prompt text
- Hover state: background shifts to a subtle `primary_container` glow, with a `surface_tint` pulse (1s ease-in-out)
- Drag-over state: border strengthens to `primary` at 60% opacity, background shifts to `primary_container` at 20% opacity

### Map Markers (Reticles)

Markers are geometric reticles, not pins.

- Outer ring: `tertiary` stroke, 1px, radius 8px
- Center dot: `tertiary` fill, radius 2px
- Gap between ring and dot: 3px transparent
- Hover state: ring expands to radius 10px (200ms `ease-out`), triggers a glass tooltip

### Glass Cards (Hover Tooltips, Floating Panels)

Used for map marker popups, architecture graph node hover cards, and any floating UI over maps.

- Background: `surface_variant` at 60% opacity
- Backdrop filter: `blur(32px)`
- Border: Ghost Border at 15% opacity (permitted here as a visibility aid on transparent surfaces)
- Radius: `md` (0.375rem)
- Padding: `lg`
- Ambient shadow: `0 16px 48px rgba(230, 234, 242, 0.06)`

### Architecture Graph Node Cards

Hover cards for the architecture page. Content structure:

```
NODE NAME (headline-sm)

One to two sentence function description. (body-sm)

───

INPUTS (label-md, small caps)
• state field names

OUTPUTS (label-md, small caps)
• state field names

BRANCHES (label-md, small caps) [only if conditional edges]
• condition → target node

FAILURE (label-md, small caps)
• failure mode description
```

- Width: 320px fixed
- Positioning: right of hovered node by default; flips to left if off-screen (handled by floating-ui or React Flow's positioning helpers)
- Appears 200ms after hover-in; dismisses 100ms after hover-out
- Fade transition: 150ms

### Confidence Indicator

A horizontal row of 5 dots representing the 1–5 confidence score.

- Filled dots: semantic color (`success`, `warning`, or `danger` based on score)
- Unfilled dots: `on_surface_variant` at 20% opacity
- Dot size: 8px diameter
- Gap between dots: `xs` (4px)
- Paired with a label: "Confidence: High" / "Medium" / "Low"
- Label color matches dot color

The containing section receives the Semantic Glow (Section 3) matching the confidence tier.

### Dialogs & Modals (Coordinate Picker)

Based on shadcn Dialog with Orbital Lens tokens applied.

**Backdrop**
- Full-viewport overlay
- Background: `surface_container_lowest` at 80% opacity
- Backdrop filter: `blur(8px)`

**Dialog surface**
- Width: 60% of viewport, centered
- Max width: 1000px
- Max height: 80vh
- Background: `surface_container`
- Radius: `md` (0.375rem)
- Padding: `xl`
- Ambient shadow: `0 32px 96px rgba(230, 234, 242, 0.08)`

**Coordinate Picker Modal Specifics**
- Map fills the available dialog area (respects padding)
- Manual input fields (lat, lon) positioned in the bottom-right corner of the map, wrapped in a glass panel
- Two-way sync: clicking the map updates the fields; typing valid coordinates in the fields re-centers the map and moves the marker
- Invalid input handling: red `danger` outline on the field, inline error text below, Confirm button disabled until all fields are valid
- Primary action: "Confirm" button in the bottom-right of the dialog (outside the map area)
- Secondary action: "Cancel" as a tertiary button

### Navigation

- Single horizontal top nav
- Logo left, nav items center-left (grouped close to the logo)
- Items: Overview, Analysis, Archive, Architecture
- Active item: `primary` text color with a 1px `primary` underline at 2px offset
- Inactive items: `on_surface_variant`
- Hover: `on_surface`

No vertical nav, no duplicate navigation patterns.

### Empty States

Used in the Archive page when no analyses exist, and similar contexts.

- Centered in the available space
- Glass panel (uses Glass Card spec)
- Contents, in order:
  - Icon in `on_surface_variant`, 48px
  - Headline (`headline-sm`): "No analyses yet"
  - Subtext (`body-sm`, `on_surface_variant`): "Run your first analysis to start building your archive."
  - Tertiary button linking to the relevant action

### Cards & Lists

- Strictly forbid divider lines between list items
- Separate items using `md`–`lg` vertical spacing
- Alternative: alternating subtle background shifts between `surface_container_low` and `surface_container`

---

## 9. Page Specifications

The system has four pages, each with a defined purpose, layout, and set of interactions. Pages are accessed through the single horizontal nav described in Section 8.

Shared across all pages:

- The nav is always present, fixed at the top of the viewport
- `surface` is the default background for all page bodies; individual panels lift to higher surface tiers as appropriate
- The minimum supported viewport is 1280px width; below this, the "desktop only" message from Section 12 is shown

---

### 9.1 Overview Page

**Purpose**

The Overview is the entry point for first-time visitors, especially interviewers arriving from a resume link. Its job is to communicate what the system does in under 30 seconds and direct the visitor to either try it (Analysis) or understand it (Architecture).

**Route**: `/`

**Layout**

A single-column editorial scroll, full viewport width with centered content capped at a max-width of roughly 1200px. No dashboard elements, no persistent sidebars. Background is `surface_container_lowest` to give the page a cinematic depth distinct from the working pages.

**Sections, in scroll order**

*Hero*
- Full-width, `3xl` vertical padding
- Left-aligned headline in `display-lg`, with one emphasis word rendered in `primary`
- Suggested headline: "Zero-shot geospatial classification, **explained**." (or similar — the emphasis word should signal interpretability or transparency, which is the system's real differentiator)
- Body text in `body-lg`, `on_surface_variant`, max-width 56ch
- Body copy describes the system in one to two sentences using the voice guidelines from Section 2
- Two CTAs side-by-side:
  - Primary: "Enter Workspace" → `/analysis`
  - Secondary: "View Architecture" → `/architecture`
- Optional: a subtle ambient background element (the schematic-style image from the original mockup) positioned to the right and partially bleeding off-canvas; kept low-contrast so it does not compete with the headline

*The Intelligence Pipeline*
- Section header: "The Intelligence Pipeline" (`display-sm`)
- Short intro paragraph (`body-md`, `on_surface_variant`, max-width 72ch)
- Three cards in a row, equal width, `xl` gap between them
- Cards use `surface_container_low`, `xl` padding, `md` radius, no borders
- Each card contains: icon (48px, `primary`), card title (`headline-sm`), description (`body-sm`, `on_surface_variant`)
- Card titles: "Visual Reasoning" / "Retrieval-Augmented Context" / "Structured Classification"
- Descriptions are honest summaries of what each stage does, no invented metrics

*Capabilities*
- Two-column layout at approximately 50/50
- Left column: section header ("Designed for Interpretability" or similar) and a bulleted list of real capabilities
- Right column: supporting schematic or visualization
- Capabilities list (examples): "Zero-shot — no task-specific training required", "Configurable class taxonomies per analysis", "Confidence-tiered fallback with CLIP recovery", "Retrieval-augmented from prior analyses at the same location", "Interpretable reasoning surfaced for every classification"
- Each capability is a single line with a `tertiary`-colored checkmark icon

*Footer*
- Minimal footer with links to documentation, GitHub, and any legal text
- `surface_container_lowest` background, `xl` padding
- `label-sm` text in `on_surface_variant`

**Interactions**
- Scroll is standard; no scroll-jacking or section snapping
- CTAs have standard hover states (Section 8)
- No loading states; the Overview is static content

**Empty/error states**
- Not applicable; the page is static

---

### 9.2 Analysis Page

**Purpose**

The Analysis page is the working surface of the system. Users configure a classification task — image, location, class taxonomy, retrieval parameters — and receive a structured report. This is where the core value of the product is delivered and where a live demo will spend most of its time.

**Route**: `/analysis`

**Layout**

Two-column split: 40% left panel (inputs), 60% right panel (report or placeholder). Both panels fill the viewport height below the nav. No map is visible on this page; map interaction is isolated to the coordinate picker modal.

The left panel uses `surface_container_low`; the right panel uses `surface`. The tonal shift defines the division without a border.

**Left Panel: Input Configuration**

Scrollable within its column if content exceeds viewport height. Padding: `xl` on all sides. Components stacked vertically with `xl` spacing between them, in this order:

1. **Page header**
   - Title: "Analysis" (`display-sm`)
   - Subtitle: one line in `body-sm`, `on_surface_variant`, e.g., "Configure a classification task and run the pipeline."

2. **Upload Zone**
   - Full width of the left panel
   - Uses the Upload Zone component (Section 8)
   - Accepts PNG or JPEG, up to 20MB, single file
   - On file selection: the zone transitions to a "file selected" state showing the filename, file size, and a remove (×) action
   - Validation errors (wrong format, too large, too small) display inline below the zone in `danger` color

3. **Select Coordinates button**
   - Full width
   - Before selection: map-pin icon + text "Select Coordinates" in `label-lg`
   - After selection: displays the selected coordinates (e.g., "17.385° N, 78.487° E") in `mono-md` with a small edit icon
   - Clicking opens the Coordinate Picker Modal (see 9.2.1 below)
   - Validation: if the user attempts to Analyze without coordinates, this button shows a `danger` outline and the error appears inline

4. **Class list input**
   - Label: "Classes" (`label-md`)
   - Chip-based input: existing classes render as removable chips in `surface_container_high`, each with an × affordance
   - An inline text input at the end of the chip row accepts new classes; pressing Enter or comma adds a chip
   - Minimum: 2 classes; maximum: 50 classes
   - Validation: fewer than 2 classes shows inline error; excess whitespace is trimmed; exact duplicates are rejected silently (no chip added)

5. **Radial distance**
   - Label: "Retrieval radius" (`label-md`)
   - Toggle Selector with options: 500m / 1km / 5km / 10km
   - Default: 5km

6. **Temporal depth**
   - Label: "Time window" (`label-md`)
   - Toggle Selector with options: 6M / 1Y / 3Y / All
   - Default: All

7. **Analyze button**
   - Full width, primary style
   - Disabled until all required inputs are valid (image uploaded, coordinates selected, class list has at least 2 entries)
   - On click: initiates the pipeline and transitions to the Loading Button State (Section 8)

**Left panel persistence**

Between analyses (after a report has rendered and the user configures a new one):

- Class list persists
- Radial distance and temporal depth persist
- Upload and coordinates reset (each new image is a new location)

**Right Panel: Report Surface**

Padding: `xl` on all sides. Scrollable vertically. Three possible states:

*Idle state (before first analysis)*
- Centered vertically and horizontally within the panel
- Subtle icon (`on_surface_variant`, 48px)
- Headline (`headline-sm`): "No analysis yet"
- Subtext (`body-sm`, `on_surface_variant`): "Configure inputs on the left and run the pipeline to see results here."

*Loading state (analysis in progress)*
- All five report sections render as shimmer placeholders in order
- See Section 11 for progressive reveal behavior and section-to-stage mapping
- Each section has an approximate final shape so layout does not shift when content populates

*Report state (analysis complete)*
- Five sections rendered in order: Headline Result, Visual Evidence, LLM Interpretation, Prior Context, Pipeline Trace
- See Section 10 for the full structure of each section

**State transitions**

- Idle → Loading: user clicks Analyze; right panel clears immediately to shimmer
- Loading → Report: SSE events populate sections progressively; see Section 11
- Report → Loading: user runs a new analysis; right panel clears immediately to shimmer again
- Error during Loading: the affected section(s) show inline error states; Pipeline Trace still renders as a diagnostic surface

#### 9.2.1 Coordinate Picker Modal

Opened from the "Select Coordinates" button. Modal spec inherits from Section 8's Dialogs & Modals.

**Layout**

- Dialog surface: 60% of viewport width, centered, max width 1000px, max height 80vh
- Dialog content area has two regions:
  - The map, filling most of the dialog area (approximately 85% of dialog height)
  - A footer row below the map with Cancel (tertiary) and Confirm (primary) buttons, right-aligned

**Map region**

- CartoDB `dark_matter` tiles (with labels)
- Initial view: if the user has previously selected coordinates, centered there; otherwise, a sensible default (e.g., world view or a pinned default location)
- Single reticle marker placed at the currently selected coordinates (if any)
- Clicking anywhere on the map moves the reticle to that location and updates the manual input fields
- Standard Leaflet zoom controls (top-left); no locate-me button in this context

**Manual input panel (bottom-right of the map region)**

- Positioned absolutely within the map area, bottom-right corner with `lg` offset from the map edges
- Glass panel treatment (Section 8): semi-transparent `surface_variant`, 32px backdrop-blur, Ghost Border at 15%
- Contains two labeled inputs stacked vertically: "Latitude" and "Longitude"
- Inputs use tabular-nums (`mono-md`)
- Validation:
  - Latitude must be a number in [-90, 90]
  - Longitude must be a number in [-180, 180]
  - Invalid input: `danger` outline on the field, inline error in `label-sm` below the field
  - While any field is invalid, the Confirm button is disabled
- Typing a valid value re-centers the map and moves the reticle

**Interactions**

- Map click ↔ input fields are bidirectionally synced
- Esc closes the modal without confirming
- Enter confirms when all inputs are valid
- Cancel reverts to the previously confirmed coordinates (or no selection, if none were previously set)
- Confirm closes the modal and updates the Select Coordinates button on the Analysis page

**Backdrop**

- Page behind the modal receives a `surface_container_lowest` overlay at 80% opacity with an 8px backdrop-blur
- Clicking the backdrop is equivalent to Cancel

---

### 9.3 Archive Page

**Purpose**

The Archive provides a geospatial view of every stored analysis. It lets users revisit prior classifications, compare results across time at the same location, and inspect retrieved context chains. For interview demos, this is where the RAG feature becomes tangible — markers cluster near each other show that prior analyses inform new ones.

**Route**: `/archive`

**Layout**

Two-column split: 65% left panel (map), 35% right panel (list or detail view). Both panels fill viewport height below the nav.

The left panel is full-bleed map (no padding, no surface color — the map tiles are the surface). The right panel uses `surface_container_low` with `xl` padding. The visual boundary is defined by the map's dark tile edge meeting the slightly lighter right panel.

**Left Panel: Map**

- CartoDB `dark_matter` tiles with labels, zoom range roughly 2 to 18
- Reticle markers at every stored analysis location (Section 8)
- If multiple analyses exist at nearly identical coordinates, they visually stack; the marker shows a small count badge (optional; implement if marker overlap is visible in practice)

**Map overlays (glass panels)**

*Zoom controls* — top-left, stacked vertically, Glass Card treatment

*Locate-me control* — below zoom controls, same style, triggers `map.locate()` to pan to the user's location (if permission granted)

*Viewport status readout* — bottom-left, Glass Card treatment, contains:
- "VIEWPORT STATUS" label (`label-md`, small caps)
- Center latitude and longitude (`mono-md`)
- Active analyses count in the current viewport (`label-sm`, `on_surface_variant`)

**Right Panel: List or Detail View**

The right panel has three states: default list view, hover preview (list view with tooltip on map), and detail view.

*Default (no marker selected)*

Top of panel (fixed, does not scroll with the list):
- Header: "Archive" (`headline-lg`)
- Subtitle: total analysis count, e.g., "12 analyses stored" (`body-sm`, `on_surface_variant`)
- Filter controls:
  - Confidence tier: Toggle Selector with All / High (4–5) / Medium (3) / Low (1–2)
  - Class type: dropdown populated from distinct classes across stored analyses; "Any Class" as default
- Optional: sort control (dropdown: Most recent / Nearest to map center)

Scrollable list below:
- Each entry is a card using `surface_container`, `md` radius, `lg` padding, `md` vertical gap between cards
- Card contents:
  - Class name in `headline-sm` paired with a small semantic-colored icon matching confidence tier
  - Confidence Indicator (dots + label) in the card header area
  - First ~120 characters of the synthesized description in `body-sm`, truncated with ellipsis
  - Timestamp in `mono-sm`, `on_surface_variant`
  - Small "Locate" link in `primary` that pans the map to this analysis and opens its detail view
- Card hover: subtle background shift to `surface_container_high`, cursor pointer
- Card click: same as Locate — pans map and switches right panel to detail view

*Hover state (marker on map hovered, no click yet)*

- Right panel remains in list view
- A Glass Card tooltip appears near the hovered map marker showing:
  - Class name (`headline-sm`)
  - Confidence tier label with semantic color
  - Timestamp (`mono-sm`)
  - "Click to view full report" caption (`label-sm`, `on_surface_variant`)
- Tooltip positioned to avoid covering the marker itself; uses edge-aware placement
- Hover-in delay 200ms, hover-out delay 100ms (Section 7)

*Detail view (marker clicked or list card clicked)*

- Right panel header replaces the list header:
  - Back button ("← Back to archive", tertiary button)
  - The panel below shows the full report for the selected analysis, using the same five-section structure from Section 10
- The map remains interactive; the selected marker is visually emphasized (ring expands, slight glow in `primary`)
- Clicking a different marker updates the detail view without returning to the list
- Clicking Back returns to the list view; the emphasis on the previously selected marker is removed

**Empty state (no analyses stored)**

- Map renders normally with CartoDB tiles, no markers
- Empty State component (Section 8) overlaid centered on the map area as a Glass Card:
  - Headline: "No analyses yet"
  - Subtext: "Run your first analysis to start building your archive."
  - Tertiary button: "Start Analysis" → links to `/analysis`
- Right panel shows a shorter version of the same empty state (no map behind it)

**Loading state**

On initial page load, while analyses are being fetched from the backend:
- Map renders with tiles loaded but no markers
- Right panel shows 3–5 card-shaped shimmer placeholders using the section-swap pattern from Section 11
- Once data arrives, markers appear on the map with a brief fade-in (150ms, staggered by ~30ms per marker for visual texture)

---

### 9.4 Architecture Page

**Purpose**

The Architecture page is the project's self-documentation surface. Its audience is anyone who wants to understand how the system works internally — primarily interviewers, but also future contributors. It exposes the LangGraph agent's node structure and the state contract at each node, making the system's design legible rather than hidden.

**Route**: `/architecture`

**Layout**

Full-viewport React Flow canvas below the nav. A minimal page header is overlaid in the top-left corner as a Glass Card:

- "Architecture" (`headline-lg`)
- One-line description (`body-sm`, `on_surface_variant`): "The classification pipeline as executed by the LangGraph agent. Hover a node for details."

No other persistent UI; the graph is the page.

**Graph structure**

Nodes correspond to the LangGraph agent nodes defined in the backend state machine. Approximate node set:

- `validate` — input validation
- `preprocess` — image normalization and tiling
- `decide_cluster` — decision node for hierarchical clustering
- `cluster` — LLM-driven meta-class generation (conditional)
- `describe_patches` — parallel vLLM description per patch
- `synthesize` — LLM synthesis of patch descriptions into a unified image description (conditional — skipped if not tiled)
- `retrieve` — RAG query against Qdrant
- `classify` — LLM classification with structured output
- `retry_vllm_targeted` — conditional retry path
- `clip_fallback` — conditional fallback path
- `store` — write to Qdrant if confidence threshold met
- `format` — build the final response

Edges connect nodes in execution order. Conditional edges (those originating from decision points) are styled distinctly — dashed strokes in `on_surface_variant` — to visually separate branching from linear flow. Solid edges in `primary` indicate the default happy path.

**Node styling**

- Default: `surface_container` background, `md` radius, `lg` padding
- Title: `headline-sm` centered
- Minimum node width: 160px
- Decision nodes (those with conditional outgoing edges): Ghost Border at 30% opacity to mark them as branching points
- Hover: subtle scale to 1.02, glow in `primary` at 15% opacity with 24px blur

**Graph layout**

- Top-down primary flow with horizontal branching where conditional edges diverge
- React Flow's automatic layout (e.g., dagre) is acceptable as a starting point; manual tuning may be needed to keep conditional branches readable
- Canvas supports pan and zoom with mouse drag and wheel
- A minimap in the bottom-right corner (React Flow built-in, styled to match Glass Card treatment)

**Hover interaction**

On hover (200ms delay), a Glass Card appears adjacent to the node with the structured content defined in Section 8 (Architecture Graph Node Cards):

```
NODE NAME

One to two sentence function description.

───
INPUTS
• state field names

OUTPUTS
• state field names

BRANCHES (if conditional edges exist)
• condition → target node

FAILURE
• failure mode description
```

- Card appears to the right of the hovered node by default; flips to the left if this would overflow the viewport
- Hover-out dismisses the card after 100ms
- No click-to-pin in v1

**Default view**

- On page load, the graph is centered and zoomed to fit the full pipeline in the viewport
- A subtle entrance animation: nodes fade in with a slight y-offset (300ms, staggered by ~40ms per node) to give the graph a sense of assembly rather than appearing all at once

**Controls**

- Standard React Flow controls in the bottom-left corner (fit view, zoom in, zoom out), styled to match the Glass Card aesthetic
- No edit controls; this graph is read-only

**Empty/error states**

- Not applicable; the graph is defined statically in the frontend based on the agent's known structure

---

## 10. Classification Report Structure

The report is the core output of the Analysis page. Five sections, rendered in order, each corresponding to a pipeline stage that populates it via SSE events.

### Section 1: Headline Result

- Predicted class in `display-sm`
- Confidence Indicator (5 dots + label)
- Timestamp and coordinates in `mono-sm`, `on_surface_variant`
- Section receives the Semantic Glow matching confidence tier
- Small "Model-generated classification" caption in `label-sm`

### Section 2: Visual Evidence

- The uploaded image, or a grid of patches if the image was tiled
- Synthesized description in `body-md` prose
- If tiled: expandable accordion "Per-patch descriptions" listing each patch's raw description

### Section 3: LLM Interpretation

- Header: "LLM Interpretation" (not "Reasoning")
- The classifier's reasoning text in `body-md`
- If confidence < 4 and alternatives exist: a subsection "Alternatives considered" listing alternative classes and the ambiguity reason
- Caption in `label-sm`: "Model-generated interpretation. Not ground truth."

### Section 4: Prior Context

- Header: "Prior Context"
- Subhead showing retrieval parameters: "Within 5km, past 1 year. 3 prior analyses found."
- If relaxation was applied: "Expanded to 10km after initial search returned no results."
- Row of small cards for each retrieved prior analysis: class, confidence, timestamp, distance, description snippet
- Each card flagged as "Model-generated reasoning from prior analysis"
- Empty state: "No prior analyses within selected range for this class taxonomy."

### Section 5: Pipeline Trace (collapsed by default)

- Header: "Pipeline Trace" with expand/collapse chevron
- When expanded, a list of pipeline metadata:
  - Clustering used: yes (depth N) / no
  - Targeted retry fired: yes / no
  - CLIP fallback fired: yes / no
  - Models used: vLLM name, LLM name, embedding model
  - Total latency
  - Stage-by-stage latencies
- This section is for technical interest; it is the interview demonstration surface

---

## 11. Progressive Reveal Pattern

All five report sections render as shimmer placeholders immediately when the user clicks Analyze. Each section has an approximate final shape so the layout does not shift when content arrives.

### Section-to-Stage Mapping

| Pipeline stage complete | Section that swaps to content |
|-------------------------|-------------------------------|
| Preprocessing | (internal; no visible change) |
| Visual analysis (vLLM per-patch) | Visual Evidence (image + patch descriptions) |
| Synthesis | Visual Evidence (synthesized description added) |
| Retrieval | Prior Context |
| Classification + Confidence gate finalized | Headline Result + LLM Interpretation |
| Full pipeline complete | Pipeline Trace |

### Swap Behavior

- Shimmer continues until the corresponding stage's SSE event arrives
- On event arrival: shimmer fades out over 200ms while content fades in
- All fields within a section populate simultaneously (section is atomic)
- The Headline Result section holds shimmer until the confidence gate has finalized, including any retries or fallbacks. A mid-analysis verdict that later updates would read as unreliable.

### Error Handling

- If a stage errors (SSE emits an error event), the corresponding section displays an inline error state rather than shimmer
- The rest of the pipeline continues where possible; downstream sections that depend on the errored stage also display error states
- The Pipeline Trace section always renders (with whatever metadata is available) as a diagnostic surface

---

## 12. Accessibility Notes

- **Minimum viewport**: 1280px width. Below this, display a message: "This tool is designed for desktop viewing. Please use a larger screen for the best experience." No responsive layout work is in scope.
- **Color contrast**: all text/background pairings must meet WCAG AA. The palette is tuned for this; do not introduce new colors without verifying contrast.
- **Confidence is not communicated by color alone**. Always pair dots with a label ("High", "Medium", "Low") and ensure dot count is visible.
- **Keyboard navigation** in the coordinate picker modal: Tab cycles through inputs and the Confirm/Cancel buttons. Esc closes the modal. Enter submits when valid.
- **Focus states**: use a 2px `primary` outline with 2px offset on all interactive elements. Do not rely on color shift alone for focus indication.

---

## 13. Out of Scope

Features intentionally not addressed in this design system:

- Mobile or tablet layouts
- User authentication, profiles, or settings
- Mid-analysis cancellation
- Real-time multi-user collaboration
- Offline mode
- Accessibility beyond WCAG AA baseline (e.g., screen reader optimization for the interactive graph)
- Internationalization (American English only)

---

## 14. Do's and Don'ts

### Do

- Use intentional asymmetry in layout where it serves editorial purpose
- Prefer tonal shifts over borders for sectioning
- Pair semantic color with semantic text labels
- Give geospatial data room to breathe
- Keep copy honest; let the aesthetic carry the premium feel
- Use shimmer as the unified "processing" visual language, always left-to-right sweep
- Use MD3 naming for tokens consistently

### Don't

- Use pure black; always `surface_container_lowest`
- Use high-opacity borders for sectioning
- Use standard drop shadows
- Invent metrics, capacity claims, or data formats the system does not support
- Label model-generated content as ground truth
- Use static pulses or spinners; always directional sweep
- Communicate state through color alone
