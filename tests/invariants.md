# Invariants and Non‑code Test Cases

Use these as the basis for your automated tests in your chosen language.

## Required invariants
1. Pack validates against `schema/story.schema.json`.
2. Contains exactly one `cover` Page at index 0.
3. For non-empty highlights, `pages[1:]` contain only unique highlights (no exact duplicates).
4. Ordering is stable and deterministic for the same input.
5. When events are empty or no items pass your threshold, include an `info` Page communicating "no highlights".
6. `created_at` is ISO‑8601 (UTC recommended).
7. `source` points to the input file used (e.g., `../data/match_events.json`).

## Suggested tests
- Given events with a goal at minute 90 and a shot at minute 10, the goal ranks higher if `late_minute_bonus` applies.
- If two events are identical except `desc`, deduplicate or resolve according to your rule (document it).
- If an image path is missing, your code either sets a default (`../assets/placeholder.png`) or omits the field—document the choice.

## Negative tests
- Missing required fields should fail validation when `--strict` is enabled.
- A pack without a cover Page should fail a test.
