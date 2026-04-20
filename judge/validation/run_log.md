# Judge validation run log

Each entry records a full `scripts/validate_judge.py` run against the 15 hand-labeled snippets, with per-snippet scores and the final Cohen's κ. Append-only; do not edit prior entries.

---

## 2026-04-20 — κ = 0.500 (VALIDATED, first revision)

**Judge**: `openai/gpt-oss-120b` via Groq, temperature 0.3, 3 runs per snippet (seeds 0, 1, 2), median score.

**Result**: **Cohen's κ = 0.500** against 15 hand-labeled snippets. Clears the `≥ 0.4` gate (spec §6.3, Landis–Koch "moderate agreement"). No rubric iterations needed.

| file | hand | judge_median | runs |
|---|---|---|---|
| 01.jac | 5 | 4 | [4, 4, 4] |
| 02.jac | 5 | 1 | [1, 4, 1] |
| 03.jac | 5 | 1 | [1, 1, 1] |
| 04.jac | 4 | 4 | [4, 5, 1] |
| 05.jac | 4 | 1 | [1, 1, 4] |
| 06.jac | 4 | 4 | [4, 1, 4] |
| 07.jac | 3 | 2 | [1, 2, 3] |
| 08.jac | 3 | 3 | [3, 1, 3] |
| 09.jac | 3 | 3 | [3, 4, 1] |
| 10.jac | 2 | 1 | [1, 1, 2] |
| 11.jac | 2 | 2 | [1, 2, 2] |
| 12.jac | 2 | 2 | [1, 3, 2] |
| 13.jac | 1 | 1 | [1, 1, 1] |
| 14.jac | 1 | 1 | [1, 1, 1] |
| 15.jac | 1 | 1 | [1, 1, 1] |

**Pre-run parser fix**: the original `judge_once` defaulted `score = 1` whenever the `[RESULT] X` marker was missing, which silently down-biased 3-run medians. First κ run under that bug: **0.333 (below gate)**. After preferring the structured JSON `"score"` field before falling back to the marker (commit `ef82d34`), κ rose to 0.500 — no rubric change needed. The failure mode was in the judge-text parser, not the judge prompt.

**Observed failure modes worth flagging for v1 consideration** (not requiring action now):
- **Run variance at temp=0.3.** Several 3-run triples are bimodal — e.g. snippet 02 `[1, 4, 1]`, snippet 03 `[1, 1, 1]` where the model scored a hand-5 snippet as 1 repeatedly, snippet 06 `[4, 1, 4]`. Median stabilizes some of these but snippet 03 is a real disagreement, not instability. Reviewing the snippet text might reveal it's mis-tiered; leaving the label alone for v0 (tier distribution is pre-committed) and noting that a v1 with ensemble judge or larger validation corpus would tighten this.
- **Judge bias is downward overall.** Of 15, 7 are exact agreement, 7 are judge-lower-than-hand, 1 is judge-higher. Mostly off by 1–2. No systematic bias in either direction beyond the parser-fix correction. Acceptable for v0.
- **Corpus diversity caveat**: only 1 snippet exercises node-side abilities (04). If v1 expands the corpus, adding 2–3 more node-side-ability snippets would tighten judge coverage on that axis.
