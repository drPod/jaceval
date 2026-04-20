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

---

## 2026-04-20 — Scope reframing: bounty → publishable methodology

**Context.** The original Mars conversation was casual ("a few hours a week / or set it up as a bounty") and his follow-up mentioned planning "a competition on methodologies for building the best harness for educating foundation models." Initial reading: v0 is a bounty-scope prototype, rigor should follow.

**Reframe.** Mars is a professor with a publication track record on Jac (OOPSLA 2025, OSP arXiv, SemTexts, MTP). A methodology-as-competition-entry frame naturally wants a publishable-quality artifact, not a throwaway prototype. Correct internal posture: **build v0 as the pilot slice of what could be scaled into a conference/workshop paper**. Keep the full rigor of `design-recipe.md` — paired A/B, execution-based correctness, hybrid AST+judge, Prometheus format, pre-committed thresholds, irrelevant-ctrl and no-op noise-floor controls, bootstrap CIs, McNemar — and don't downscope to "just a demo."

**What does NOT change for v0 scope.** Still 10 tasks, still 15 hand-labeled judge snippets, still 3 generators × 4 arms × 5 samples. v0 ships what the plan says it ships. v1 is where task-count and judge-corpus scale for full statistical power.

**What DOES change is the internal framing.**
- RESULTS.md leads with methodology contribution, not Δ numbers. "Here is a reusable harness for measuring whether context docs lift LLM performance on a niche language; Jac is the v0 target; here is what we found."
- README.md positioned for outside researchers, not just Mars. Quickstart must work on free-tier creds.
- Generalization hooks in harness (task schema, detectors, judge rubric, translator) treated as first-class design goals. v0 Jac must be the first-of-N instantiations, not an inseparable monolith.
- Write-up discipline: effect-size threshold pre-committed before looking at results, irrelevant-ctrl + noise-floor controls run, judge κ reported with CI — all non-negotiable for paper-readiness.

**What to watch for downstream.** Avoid scope creep that bloats v0 beyond the plan's 51 tasks, but also avoid shortcuts in the harness abstractions that would make v1 scaling painful. The methodology is the deliverable; cutting corners on the methodology is the mistake to guard against.

---

## 2026-04-20 — Free-tier budget pressure: Gemini 3 Flash quota is tight

**What happened.** Gemini 3 Flash Preview free tier = **~20 requests/day**. Today's calibration runs (syntax/01 redo + syntax/02 + syntax/03 + graph/04 + the cost-fix reruns) already hit the daily cap mid-way through graph/04 calibration. Llama 4 Scout on Groq free tier is looser and hasn't been a problem.

**Budget math.** Remaining calibrations: 6 tasks × 5 samples × 1 generator = 30 Gemini requests ⇒ ≥2 more days. Full eval run: 10 tasks × 4 arms × 5 samples = 200 Gemini requests ⇒ ≥10 days if we insist on one generator at a time. Cannot complete v0 in a single-day run. The actual eval will need to be split across multiple days or we change strategy.

**Decision.** Accept calibration may partial-fail. Harden `scripts/calibrate_task.py` to catch 429/quota errors, print what's collected, and move on to the next model/task rather than crashing. For the actual eval (Task 39 orchestrator), build in per-provider quota awareness and resumability via the append-only JSONL state — which the plan already specifies, good. Budget-wise we can also consider: (a) spending modest $ on paid-tier Gemini for the eval proper (≤$5 total spec allows it), (b) reducing K from 5 to 3 on Gemini only, (c) accepting multi-day run windows.

**What to watch for downstream.** Do NOT pass `--include-haiku` to the calibration script except when explicitly instructed. Haiku is paid per-call and calibration doesn't need it. Reserve Haiku invocations for the actual eval run where it's a generator-under-test, not a calibration probe.

**v1 generator-tier note (2026-04-20).** If Mars backs this work with resources, the actual eval run in v1 will use stronger generators (Sonnet/Opus tier, Gemini 3 Pro, Llama 405B, etc.) — not the free-tier models pinned here for v0. The free-tier choice is a v0 budget constraint, not a methodological commitment. The harness's model-dispatch interface (`harness/generators.py`) already abstracts this cleanly: swap the `ModelName` literal and the three `_call_*` functions and the rest of the pipeline is untouched. Keep that abstraction clean as we build downstream.

---

## 2026-04-20 — Milestone: all 10 v0 paired tasks authored (Phase 5 complete)

**State.** Tasks 16–25 landed. 10 tasks across 3 strata:
- **Syntax (3):** 01 typed list-agg, 02 obj with methods, 03 filter-comprehension *HELD OUT*.
- **Graph (3):** 04 directional build, 05 bidirectional with typed edges, 06 typed-edge mutation.
- **Walker (4):** 07 count-by-type, 08 disengage-early, 09 node-side abilities, 10 path-aggregation *HELD OUT*.

All 10 solution.jac files validate clean, all 10 tests.jac pass 5/5. Baseline calibration aggregate **0/10 across Gemini 3 Flash + Llama 4 Scout for every task** — the floor-across-free-tier-models pattern held throughout, not Haiku-specific. This is the strongest pre-registered evidence we have that context docs should produce large, discrete lift on this eval (vs. marginal quantitative lift).

**Pitfalls log state.** `docs/findings/jac-pitfalls.md` now carries 16+ distinct empirically-confirmed Jac gotchas across statements, tests, imports, graph/OSP, and walkers. Several are doc-vs-runtime discrepancies suitable for upstream bug reports to Jaseci. These are first-class research artifacts alongside the task set.

**Methodology invariants held.** Paired A/B purity maintained in every prompt (no Jac keyword leaks in any of the 10 `prompt.md` files). `validate_jac` round-trip executed on every solution. HELD OUT tasks (03, 10) marked `held_out: true` in meta.yaml. Calibration protocol (free-tier default, no rescue hints for 0/n baselines) followed throughout. Subagent-driven development with routing discipline enforced via `docs/plans/subagent-dispatch-template.md`.

**What's next.** Phase 6: Tasks 26–31 implement 6 pattern-based AST idiom detectors (`uses_walker`, `uses_visit`, `uses_typed_edge_archetype`, `uses_connect_op`, `has_type_annotations`, `uses_abilities_on_nodes`) per the plan. Each is ~5–15 lines of regex over comment-stripped Jac source. Small, mechanical work — plan to dispatch as a batch to one subagent rather than six separate dispatches, to minimize overhead.

---

## 2026-04-20 — Phase 7 complete. Judge validated at κ = 0.500

**State.** Tasks 32–35 landed.
- **Task 32** — Prometheus-format judge prompt at `judge/prompt.md`. Explicit "penalize Python-transliterated patterns" instruction per design-recipe.md recommendation.
- **Task 33** — `harness/judge.py` wraps GPT-OSS 120B via Groq (deliberately non-Anthropic, non-Google, non-Meta so no self-preference bias on any generator family). 3-run median via `judge_median()`. Exponential-backoff retries on Groq `APIConnectionError` / `RateLimitError` (added after the first validation run hit a transient DNS failure mid-corpus).
- **Task 34** — 15 hand-labeled snippets at `judge/validation/snippets/01..15.jac`, 3 per tier (5/4/3/2/1). Every `hand_labels.jsonl` justification cites a specific `jac://` URI or `docs/findings/jac-pitfalls.md` entry.
- **Task 35** — Cohen's κ in `harness/stats.py`. Validation runner at `scripts/validate_judge.py`.

**Validation result: κ = 0.500** — moderate agreement per Landis–Koch, clears the 0.4 gate. Detailed per-snippet scores + run diagnostics in `judge/validation/run_log.md`.

**One real bug caught**: the original `judge_once` parser defaulted `score = 1` whenever the `[RESULT] X` marker was missing, silently down-biasing 3-run medians. First κ run under that bug: **0.333 (below gate)**. Parser fix (prefer structured JSON `"score"` field before falling back to the marker) took us to 0.500 with **no rubric revisions needed**. The rubric_history.md log captures that the failure was in the parser, not the prompt — important for the writeup.

**Methodology health.** Three design-recipe non-negotiables are now in place:
1. Execution-based correctness (Phase 3 jac_runner — shipped).
2. Hybrid AST + LLM judge idiomaticity (Phase 6 detectors + Phase 7 judge — shipped; 0.4 × AST + 0.6 × judge composition lands in Phase 8 scorer).
3. **Judge validated against hand labels at κ ≥ 0.4** — done, κ = 0.500.

**What's next.** Phase 8 (Tasks 36–37): scorer combines AST + judge into per-task idiomaticity, then the statistics module (unbiased pass@k via Chen, McNemar's on paired binary, paired bootstrap on ordinal, Wilson intervals — the full statistical backbone the design recipe calls for). Then Phase 9 (plan builder + orchestrator), then the actual eval run.
