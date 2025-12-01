# DECISIONS

## Heuristic and ranking

Events are selected as highlights using a custom, explainable scoring system composed of two parts:

- Base scores: a fixed value per event type (defined in `story_builder/core.py` under `BASE_SCORES`). Examples: `goal=100`, `penalty goal=95`, `yellow card=30`, etc.
- Context bonuses: extra points for match context (computed by `compute_context_bonus`). Examples: `first_goal`, `equalizer`, `go_ahead`, `late_game`, `tight_game_chance`, penalty-related bonuses, and so on.

Selection flow:

1. Compute final score for every event: `score = base + sum(context bonuses)` (returned as a breakdown dict so the reason is explainable).
2. Keep only events with `score > 0`.
3. Sort to pick top-N by score, breaking ties by original event order (stable ranking).
4. Reorder the selected top-N chronologically for the final story (minute/second order) so the narrative reads naturally.

Image matching: for each highlight we try to resolve involved player names (from `team`/`playerRef` fields), then match against `assets/asset_descriptions.json` via `story_builder/asset_picker.py`. If no suitable asset exists we use `assets/placeholder.png`.

## Data handling (duplicates, missing fields, out‑of‑order minutes)
-
This project expects somewhat noisy input; here are the defensive choices made:

- Duplicate messages: events are treated as individual messages. The selection process uses the event's index and minute/second to preserve stability; exact duplicate pages are unlikely to both be selected because scoring is deterministic and based on distinct indecies of the sorted event array.

- Missing fields: code defensively parses `minute`/`second` with `int()` guarded by try/except (`_flatten_events` and `_parse_minute`). Missing or unparseable minutes default to `0` so they sort to the start of the match rather than crashing.

- Out‑of‑order minutes: messages are flattened and sorted by `(minute, second)` before scoring (`_flatten_events`) so the builder is resilient to out-of-order messages in the raw feed.

- Unknown event types: `get_base_score` returns `0` for unknown types so they are ignored by the highlight selection (no highlight created for unknown/irrelevant messages).

## Pack structure and invariants
-
The pack follows `schema/story.schema.json`. Important decisions and guarantees:

- Cover page: always present and placed at index 0. It contains `headline`, `image`, and `created_at`.
- Highlights: pages of type `highlight` include `minute`, `headline`, `caption`, and (when available) `image` and `explanation`.
- No‑highlights fallback: if no events score above zero, the pages will be `cover` then a single `info` page (the "No highlights available" page).
- Closing slide: when there are highlights, the builder appends a final page that announces the final score. To keep the pack valid (schema only allows `cover`, `highlight`, `info`) and ensure the image shows in the preview, the closing slide is implemented as a `highlight` with `minute: 120`, `caption: "Match ended"`, and `image: ../assets/final.png`. It is appended after ordinary highlights so it is always the last page.

- Schema compatibility: the pack uses `pack_id` (UUID) as the top-level identifier and otherwise adheres to the schema's required fields. See "Known bug" below for a schema-related fix we made.

## What I would do with 2 more hours
-
If I had two more hours I'd prioritize the following:

1. add stronger protection by maintaining a seen set of events keyed by (`type`,`minute`,`second,...`) to skip exact duplicates 
2. make the UI more advanced and modern
---

Known bug (fixed):

During development there was a schema mismatch: the JSON Schema expected a top-level `pack_id` but some code and earlier tests used `story_id` — this caused validation failures. I updated the schema/code to consistently use `pack_id` and adjusted tests accordingly.
---

