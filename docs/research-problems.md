# Research problems log

Append-only log of problems encountered during jaceval v0. Each entry: what happened, what was decided, what to watch for downstream. Ordered by date.

---

## 2026-04-20 — syntax/01: calibration floor vs. A/B cleanliness

**What happened.** Authored Task 16 (syntax/01: `total_cost` over `list[Item]`). First calibration with no-skill + Haiku was 0/5. Implementer subagent added a Jac-syntax hint to `prompt.md` ("Remember Jac requires `has` before every field...") to clear the 20% floor; got 1/5 and committed. Spec reviewer caught that the hint contaminates the shared prompt — every arm (including `no-skill` and `irrelevant-ctrl`) now gets free Jac teaching on the exact construct this task probes, shrinking measurable SKILL.md lift. Hint removed in a follow-up commit. Re-calibration: 0/5 twice.

**The tension.** Two spec rules collided: (1) no Jac-specific teaching in the shared task prompt; (2) baseline pass rate in [0.2, 0.8] for task inclusion.

**Decision.** Keep syntax/01 at 0/5 baseline. Rationale: the 20–80% band is a conservative heuristic to avoid floor/ceiling effects, not a hard law. With n=5 it's noise-dominated anyway (Wilson 95% CI on 0/5 ≈ [0, 0.52]). A 0→non-zero lift with SKILL.md is still strong signal — arguably stronger than a 30→40% lift. Paired bootstrap on the ordinal judge score survives regardless, since the LLM judge grades 1–5 whether the code runs or not. Flag in RESULTS.

**What to watch for downstream.**
- If multiple tasks land at 0/5 baseline, the binary-correctness leg of the analysis (McNemar, pass@k deltas) becomes thin. Consider whether the task mix is calibrated to the *right* frontier model — Haiku may just be weaker than the eval assumes.
- Calibration against only Haiku may understate the true baseline distribution. Gemini 3 Flash and Llama 4 Scout run as generators but not as calibration probes. If baseline across all three generators is meaningfully higher than Haiku-only, the 20–80% rule is being applied to the wrong number.
- Watch for prompt drift: during task authoring, the implementer's instinct is to add hints when calibration fails. That instinct is dangerous for paired A/B. Prompt edits during calibration must only clarify the *problem*, never the *language*.

**Process learning.** The subagent-driven workflow caught this: implementer ran a failing-calibration loop that the spec reviewer later caught as contamination. Keep the spec-review gate strict — do not accept "close enough" even when calibration passes. Fair benchmark design > calibration hygiene.

**Update 2026-04-20 (syntax/02 + syntax/03).** All three syntax tasks now calibrate at 0/5 on no-skill + Haiku. The pattern is confirmed, not task-specific: free-tier Haiku without any Jac context produces nothing that runs for tasks requiring `obj`/`has`/methods or filter-comprehension. This is actually evidence *for* the eval premise — docs should matter a lot here — but means the binary-correctness leg of the analysis will be thin on the syntax bucket. Revisit calibration protocol in v1: probably calibrate against the full 3-generator set, or use a stronger baseline model (e.g., Sonnet) so the 20–80% heuristic applies to a model that's near the frontier of what free-tier Jac authors would actually use.
