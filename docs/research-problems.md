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

**Update 2026-04-20 (syntax/02 + syntax/03).** All three syntax tasks now calibrate at 0/5 on no-skill + Haiku. The pattern is confirmed, not task-specific: free-tier Haiku without any Jac context produces nothing that runs for tasks requiring `obj`/`has`/methods or filter-comprehension. This is actually evidence *for* the eval premise — docs should matter a lot here — but means the binary-correctness leg of the analysis will be thin on the syntax bucket.

**Update 2026-04-20 (multi-model calibration + cost fix).** The original `scripts/calibrate_task.py` hardcoded Claude Haiku, burning paid-tier credits on every calibration run. Rewrote it to default to the two free-tier generators (Gemini 3 Flash Preview + Llama 4 Scout via Groq), 5 samples each, with per-model breakdown and aggregate. `--include-haiku` opt-in for paid calibration. Re-ran on all three syntax tasks:

| Task | Gemini 3 Flash | Llama 4 Scout | Aggregate |
|------|----------------|----------------|-----------|
| syntax/01 | 0/5 | 0/5 | 0/10 |
| syntax/02 | 0/5 | 0/5 | 0/10 |
| syntax/03 | 0/5 | 0/5 | 0/10 |

Not a Haiku-specific weakness — it is a **floor across all free-tier frontier-ish models we have access to**. This settles the "weak model?" question from the first postmortem: no, the syntax probes genuinely cannot be solved by current LLMs without some Jac-specific context. Strong pre-registered prediction: the SKILL.md and LLMDocs arms will show discrete non-zero lift on these tasks; the lift itself, not the absolute rate, is the measurement.

**Calibration protocol revision.** The spec's `baseline_pass_target: 0.2-0.8` heuristic is inappropriate for a language-education eval where baseline is expected to be at floor. Treat the aggregate baseline pass rate as *informational* — keep tasks at 0/10 if the SKILL.md arm is expected to lift them. The discrimination check that actually matters is running the SKILL.md arm and observing any non-zero lift; if SKILL.md ALSO produces 0/n, the task is genuinely too hard and should be dropped. This check happens at Task 44, not at calibration time.
