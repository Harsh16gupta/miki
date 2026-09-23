# Miki Design System (DESIGN.md)

> **Design Directive for AI Coding Agents & Engineers**  
> This document defines the visual language, design tokens, layout hierarchy, and component rules for **Miki**. All UI changes must adhere strictly to these principles. Avoid generic "AI-generated" tropes (overdone purple gradients, low-contrast washed-out text, nested cards-within-cards). Strive for the clean, minimal, and utilitarian elegance of **Cal.com**, **Linear**, and modern open-source devtools.

---

## 1. Core Design Philosophy

* **Cal.com-Inspired Minimalism**: Crisp hairline borders, deep neutral surfaces, high typographic contrast, and thoughtful whitespace.
* **Refined Dark Surfaces (Not Muddy Glass)**: If glass or blur is used, keep it subtle (`backdrop-blur-md` with `rgba(255,255,255,0.03)` to `0.06` fill and a clean `1px border-neutral-800/80`). Avoid murky layered gradient glows and washed-out text.
* **Stage-Driven Application Architecture**: Rather than dumping Setup, Interview, and Report into one endless vertical scroll of cards, Miki is a **stepped workspace** with 3 distinct, focused stages:
  1. `Setup`: Profile & requirement ingestion.
  2. `Interview`: Immersive, focused arena with voice/text interaction and live claim telemetry.
  3. `Report`: Executive debrief with rubric scoring, cited evidence, and actionable feedback.
* **Zero AI Clutter**: No gratuitous animations, no decorative spinning orbs that distract from the interview, and no unreadable low-contrast gray text.

---

## 2. Color System & Semantic Tokens

Miki uses the editorial technical palette (see
`docs/frontend-rebuild/DESIGN-TOKENS.md` — law; reference image
`reference/01-design-system.png` wins on any conflict). **No other hex
values may be introduced.**

### A. Surfaces & Backgrounds
* **Canvas / Base Background**: `#06090A`.
* **Surface (Panels, Cards)**: `#0E1223` with `border rgba(255,255,255,0.08)`.
* **Dividers & Hairlines**: `rgba(255, 255, 255, 0.08)`.

### B. Typography & Text Contrast
* **Text Primary (Headlines, body, scores, filled bars)**: sage `#83DDDA`.
* **Text Secondary (Meta, hints, sublines)**: muted sage `#8FA3A0` — never
  drop below `4.5:1` contrast ratio on canvas. Placeholders dimmest.
* **Numbers / Timers / Scores**: mono + `tabular-nums`.

### C. Semantic & Functional Accents
* **Accent (ONE italic headline word per viewport max, primary CTA,
  form-panel offset shadow, required dots, mic button)**: `#E4621F`.
* **Teal (secondary stamp, checked states, LIVE pill, upload-hover border,
  strengths chips)**: `#3AA99E`.
* **Danger / Error only**: `#f87171` (Red-400, unchanged).

---

## 3. Typography Rules

* **Display serif with true italic** (headlines, body prose, input values,
  placeholders): `Newsreader:ital,opsz,wght` via Google Fonts `<link>`
  (fallback Georgia, serif). Italic accent word in `#E4621F` — max one per
  viewport.
* **`JetBrains Mono`** (ALL labels, buttons, nav, breadcrumbs, meta,
  timers, IDs): uppercase + wide tracking (`0.14em+`) for micro-labels.
* **Numbers / Metrics / Citations**: mono + `tabular-nums`.
* **Body measure**: < 80 chars per line; serif body gets generous line-height.

---

## 4. Layout & Information Architecture

### App Shell
* **Top Navigation Bar**: Fixed or sticky `h-14` or `h-16`, subtle bottom border (`border-b border-white/[0.08]`), featuring:
  - Miki logo & status pill (`Evidence-Grounded Trainer`).
  - **Stage Stepper** (`1. Setup` → `2. Interview` → `3. Evaluation Report`), allowing clear orientation.
  - Quick session reset button (`New Session`).
* **Main Content Stage**:
  - Full-height flex workspace (`min-h-[calc(100vh-4rem)]`).
  - No awkward empty spaces or endlessly stacked disabled cards.

### Stage 1: Setup Workspace
* Clean 2-column or grid layout comparing **Candidate Resume** and **Target Job Description**.
* High-visibility dropzones with drag-over highlights, supported formats, and instant extraction chip counts ("14 claims extracted", "8 skills required").
* Prominent "Begin Interview" launch bar.

### Stage 2: Interview Arena
* **Immersive Workbench**:
  - **Main Area**: Chat transcript with clear visual distinction between Interviewer (Miki) and Candidate (You).
  - Smooth auto-scroll with keyboard accessible input and voice toggle button.
  - **Voice Waveform / Pulse State**: Clean, rhythmic visualizer when mic is listening or AI is answering.
  - **Context Drawer / Telemetry**: Collapsible sidebar or drawer showing live detected claims, current evaluation focus, and interview state.

### Stage 3: Evaluation Report Dashboard
* Structured, executive-grade summary:
  - Overall performance & score cards.
  - Dimension breakdown with clean progress bars and expandable evidence citations.
  - 4-quadrant grid: Strengths, Areas for Improvement, Vulnerable Claims, and Recommended Study Topics.
  - Action bar: "Download Report", "Practice Again", "Reset Session".

---

## 5. Component Style Guide

### Buttons
* **Primary**: solid `#E4621F`, black text, mono uppercase + `→`.
  One orange button per viewport.
* **Secondary / Outline**: `1px` sage outline (`#83DDDA`).
* **Ghost / Danger**: ghost quiet text; danger uses `#f87171` (errors only).

### Panels & Surfaces
* **Panels**: sharp corners (`rounded-none` to `rounded-sm`), `1px` border,
  near-black fill. `rounded-xl` only on small inner elements.
* **Form panel**: `1px` light border + hard solid offset shadow
  `box-shadow: 10px 10px 0 #E4621F` (no blur). Header row: mono title left
  + form number right (e.g. `SESSION SETUP` / `FORM · SES-001`).

### Badges / Stamps
* **Stamp badges**: `2px` border (accent `#E4621F` or teal `#3AA99E`),
  `rotate-[-2deg]`, mono uppercase (e.g. `EVIDENCE-GROUNDED`,
  `VOICE-FIRST`, `LIVE`, `SETUP`).

### Inputs & Uploads
* **Underline inputs**: transparent bg, bottom hairline only, mono
  uppercase label, serif value, accent required dot.
* **Upload zones** (3 states): default dashed sage/40 + format hint;
  hover/dragover teal border + "Release to upload"; filled filename + size
  + "Uploaded" + × remove.
* **Checkboxes**: square outline, teal fill + check when on.

### Chrome
* **Background**: faint blueprint grid over canvas (`.blueprint-grid`) +
  frame lines with corner `+` registration marks.
* **Footer strip**: hairline rule, mono microcopy left
  (`TURN CONVERSATIONS INTO CONFIDENCE`) / right (`BUILT FOR ENGINEERS`).
* **Icons**: Lucide, 24px, 1.5px stroke.
* **Motion**: 150–200ms ease-out hovers, message entry fade + 8px rise
  (`.msg-in`), single recording pulse only (`.voice-live`), full
  `prefers-reduced-motion` calm.

---

## 6. Rules & Guardrails for AI Coding Agents

1. **NEVER use low-contrast text**: Ensure all primary text is sage `#83DDDA` and secondary `#8FA3A0` or brighter on canvas. Never below `4.5:1`.
2. **NEVER stack full-page views vertically**: Respect `interview.stage`. If the user is in `setup`, show the Setup workspace. If in `interview`, show the Interview Arena. If in `report`, show the Evaluation Report.
3. **DO NOT invent arbitrary CSS utility classes**: Stick to standard Tailwind classes plus the named utilities in `frontend/src/index.css` (blueprint-grid, stamp, panel-hard, input-underline, upload-zone).
4. **DO NOT add decorative visual noise**: Avoid drifting neon orbs, heavy radial gradients, or bouncing animations that compete with user attention.
5. **Always provide responsive layouts**: Use `flex-col sm:flex-row`, `grid-cols-1 md:grid-cols-2`, and ensure mobile accessibility.
6. **Ensure interactive feedback**: Every clickable element must have hover, active, focus-visible, and disabled states.
