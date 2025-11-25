# Highlights → Stories Mini‑Builder (Tech‑agnostic Scaffold)

**Goal:** Ingest sports match events and produce a **Story Pack** (a JSON bundle of Pages) plus a **minimal preview** to step through Pages.

You can implement the builder in any language (Python / Node/TS recommended) as a **CLI** or **small HTTP service**. This scaffold includes:
- A **data contract** for events.
- A **JSON Schema** for the output pack.
- A **preview** (`preview/index.html`) that loads a `story.json` via a file picker.
- Templates for `DECISIONS.md`, `AI_USAGE.md`, and test invariants.

## Minimal deliverable
- A script or service that converts `data/match_events.json` into `out/story.json` following `schema/story.schema.json`.
- The pack must include at least:
  - A **cover** Page.
  - **N highlights** chosen by your heuristic.
  - Stable ordering, no exact duplicates, and required fields present.
  - A sensible fallback: if no highlights, include a "no highlights" Page.
- A minimal preview: open `preview/index.html` and load your `out/story.json` to step through Pages.
- At least **3 tests** (in your chosen language) that enforce key **invariants** from `tests/invariants.md`.

## Optional stretch ideas (not required to pass)
- Tunable ranking with `weights.json` and page explanations.
- Smarter captions (LLM + evaluation script that checks factual fields).
- Better preview UX (progress dots, keyboard nav are already included; feel free to enhance).
- understanding of what's contained in the files in `/assets` and selection of those to match the events in the Pages

## How to run the preview (no server needed)
1) Build your `out/story.json` using your implementation.
2) Open `preview/index.html` in your browser.
3) Click "Load pack.json" and select the file from `out/`.

> Images referenced by Pages should be placed in `assets/`. The preview uses standard `<img>` tags relative to `preview/`.

## Repository layout
- `data/` — You put `match_events.json` here (see `data/events_schema.md`).
- `assets/` — Images used by Pages. A tiny placeholder is included.
- `out/` — Your output pack(s). Add `.gitkeep` to keep the folder.
- `schema/pack.schema.json` — JSON Schema for validating the output pack.
- `preview/index.html` — Minimal viewer that loads a pack via file picker.
- `tests/invariants.md` — Non‑code test cases and invariants to enforce.
- `templates/DECISIONS.md`, `templates/AI_USAGE.md`, `templates/EVALS.md` — Templates to fill in.
- `weights.example.json` — Optional ranking weights you can adopt.

Good luck, and have fun! Keep it simple, explain decisions, and show how you **verify** correctness (tests, assertions, small experiments).
