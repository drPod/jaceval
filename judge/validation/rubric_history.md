# Judge rubric history

## 2026-04-20 — initial rubric

Initial judge prompt at `judge/prompt.md`. Prometheus format with explicit Python-penalty instruction. Hand-label corpus: 15 snippets across score tiers 1–5 (3 per tier). See `judge/validation/hand_labels.jsonl`.

## 2026-04-20 — validated at κ = 0.500

First validation run against the 15-snippet corpus produced κ = 0.333 (below gate). Root cause: `judge_once` parser defaulted `score=1` whenever the `[RESULT] X` marker was missing, silently down-biasing 3-run medians. Fix in commit `ef82d34` preferred the JSON `"score"` field before falling back to the marker. Re-run produced **κ = 0.500**, which clears the ≥ 0.4 gate. **No rubric revisions needed**; the failure was in the text parser, not the prompt. Per-snippet scores + full diagnostic discussion in `judge/validation/run_log.md`.
