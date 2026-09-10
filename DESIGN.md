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

Miki uses a refined dark palette anchored on zinc/neutral tones with purposeful semantic accents.

### A. Neutral Surfaces & Backgrounds
* **Canvas / Base Background**: `#09090b` (Deep Obsidian / Zinc-950).
* **Surface 1 (Cards, Panels)**: `#121215` / `rgba(18, 18, 21, 0.75)` with `border border-white/[0.08]`.
* **Surface 2 (Elevated / Nested containers / Inputs)**: `#18181b` / `rgba(24, 24, 27, 0.6)` with `border border-white/[0.06]`.
* **Surface Hover**: `rgba(255, 255, 255, 0.04)`.
* **Dividers & Hairlines**: `rgba(255, 255, 255, 0.08)` or `border-neutral-800`.

### B. Typography & Text Contrast
* **Text Primary (Headings, active labels, body)**: `#fafafa` (Zinc-50) — high contrast, 100% readable.
* **Text Secondary (Subtitles, descriptions, hints)**: `#a1a1aa` (Zinc-400) — never drop below `4.5:1` contrast ratio.
* **Text Muted (Timestamps, metadata, disabled)**: `#71717a` (Zinc-500).

### C. Semantic & Functional Accents
* **Primary Action / CTA**: Solid `#fafafa` with `#09090b` text, font-medium/semibold, sharp rounded pill (`rounded-lg` or `rounded-full`).
* **Evidence & Claims Accent (Gold / Amber)**:
  - Text / Badges: `#f59e0b` / `#fbbf24` (Amber-400 / 500).
  - Background: `rgba(245, 158, 11, 0.1)`.
  - Border: `rgba(245, 158, 11, 0.25)`.
* **Voice & Live Activity (Cyan / Emerald)**:
  - Voice active: `#06b6d4` (Cyan-500) or `#10b981` (Emerald-500).
  - Ambient pulse: Clean 2px ring / subtle glow.
* **Danger / Error**:
  - Border: `rgba(239, 68, 68, 0.3)`.
  - Background: `rgba(239, 68, 68, 0.08)`.
  - Text: `#f87171` (Red-400).

---

## 3. Typography Rules

* **Font Family**: Inter, Geist, or system sans-serif (`font-sans`).
* **Headings**:
  - `h1`: `text-2xl sm:text-3xl font-semibold tracking-tight text-white`
  - `h2`: `text-lg sm:text-xl font-medium tracking-tight text-white`
  - `h3`: `text-sm sm:text-base font-medium text-neutral-200`
* **Body**: `text-sm leading-relaxed text-neutral-300`
* **Labels / Micro-copy**: `text-xs font-medium uppercase tracking-wider text-neutral-400`
* **Numbers / Metrics / Citations**: Tabular numerals (`tabular-nums font-mono text-xs`) for scores, timestamps, and claim IDs.

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
* **Primary**: `bg-white text-zinc-950 hover:bg-neutral-200 font-medium px-4 py-2 rounded-lg text-sm transition-colors shadow-sm disabled:opacity-50`
* **Secondary / Outline**: `border border-white/10 bg-white/[0.03] text-neutral-200 hover:bg-white/[0.08] hover:text-white px-4 py-2 rounded-lg text-sm transition-colors`
* **Ghost**: `text-neutral-400 hover:text-white hover:bg-white/[0.05] px-3 py-1.5 rounded-lg text-sm transition-colors`

### Cards & Panels
* **Container**: `rounded-xl border border-white/[0.08] bg-zinc-900/60 backdrop-blur-md p-5 sm:p-6 shadow-xl`
* **No triple nested cards**: Use subtle separator lines or muted background fills (`bg-black/30`) instead of repeating full card borders.

### Badges & Status Pills
* `inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium`
* Default: `bg-white/[0.06] text-neutral-300 border border-white/[0.08]`
* Success / Ready: `bg-emerald-500/10 text-emerald-400 border border-emerald-500/20`
* Amber / Claims: `bg-amber-500/10 text-amber-300 border border-amber-500/20`
* Cyan / Live: `bg-cyan-500/10 text-cyan-400 border border-cyan-500/20`

---

## 6. Rules & Guardrails for AI Coding Agents

1. **NEVER use low-contrast text**: Do not use `#a8a29e` on dark translucent backgrounds without checking readability. Ensure all primary text is `#fafafa` or `#f4f4f5`.
2. **NEVER stack full-page views vertically**: Respect `interview.stage`. If the user is in `setup`, show the Setup workspace. If in `interview`, show the Interview Arena. If in `report`, show the Evaluation Report.
3. **DO NOT invent arbitrary CSS utility classes**: Stick to standard Tailwind classes.
4. **DO NOT add decorative visual noise**: Avoid drifting neon orbs, heavy radial gradients, or bouncing animations that compete with user attention.
5. **Always provide responsive layouts**: Use `flex-col sm:flex-row`, `grid-cols-1 md:grid-cols-2`, and ensure mobile accessibility.
6. **Ensure interactive feedback**: Every clickable element must have hover, active, focus-visible, and disabled states.
