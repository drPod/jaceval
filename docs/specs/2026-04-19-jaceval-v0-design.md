# jaceval v0 — design spec

**Status:** pre-registered. Numeric thresholds below are frozen as of 2026-04-19 and will not be revisited after any result is visible.
**Design foundation:** `design-recipe.md` at repo root.
**Scope gate:** single implementation plan; sub-projects are explicitly deferred to v1 and listed in §17.

---

## 1. One-line summary

A paired A/B benchmark that measures, for three generator models, whether each of three Jac context documents (Jaseci's `LLMDocs-Mini`, Jaseci's `LLMDocs-Full`, this project's v0 `SKILL.md`) improves correctness and idiomaticity of generated Jac code over a no-skill baseline — under a fixed budget of ≤ $5 and a 10–14 day implementation window.

## 2. Motivation

No published Jac codegen benchmark exists. Jaseci Labs ships `LLMDocs` artifacts (Mini and Full) optimized for LLM context windows, but no public measurement of their effect on LLM Jac output has been published. Without a benchmark, claims about "the best SKILL.md for Jac" are unfalsifiable. jaceval v0 is the smallest artifact that makes such claims measurable, and by design remains extensible to other niche languages — the translator and harness layers are language-agnostic, with Jac filling in the language-specific slot.

## 3. Goals

**Primary (must hit for v0 to be considered complete):**

1. A runnable, publicly-clonable harness that produces paired per-task correctness and idiomaticity scores across five arms × three models × ten tasks.
2. A validated LLM-based idiomaticity judge with Cohen's κ ≥ 0.4 against a hand-labeled set of 15 Jac snippets.
3. A written `RESULTS.md` reporting paired deltas, 2×2 flip tables, per-stratum breakdown, and bootstrap confidence intervals, with pre-committed effect-size thresholds applied as the decision rule.
4. A v0 `SKILL.md` authored *after* the baseline run, targeting failure modes observed in the baseline, and evaluated on the same harness.

**Secondary (nice-to-have, do not block shipping):**

5. A structure that makes "add another language" a clean module-replacement, not a rewrite.
6. Reproducibility: `make eval` (or equivalent) reproduces the entire pipeline from scratch, free-tier credentials only.

## 4. Non-goals

- `by llm()` task bucket (deferred to v1 — see CLAUDE.md for rationale).
- Dual-judge ensemble (single judge for v0; ensemble is a v1 hardening).
- Inspect AI integration (bespoke Python for v0; Inspect AI is a v1 refactor candidate if needed).
- CodeBLEU or other structural-similarity metrics.
- Fine-tuning. jaceval measures inference-time context effects only.
- N > 10 tasks. Expansion to 40–60 tasks is v1.

## 5. Experimental design

### 5.1 Arms (five total)

| Arm | Purpose | Content |
|---|---|---|
| `no-skill` | Baseline; anchors the paired deltas | Empty context block (just the task prompt) |
| `llmdocs-mini` | Tests Jaseci's existing compact doc | Verbatim copy of `LLMDocs-Mini` from docs.jaseci.org, with a citation header |
| `llmdocs-full` | Tests Jaseci's existing full doc | Verbatim copy of `LLMDocs-Full` from docs.jaseci.org, with a citation header |
| `v0-skill` | Our hypothesis | `SKILL.md` authored after baseline, targeting observed failures |
| `irrelevant-ctrl` | Controls for "more tokens" effect | A SKILL.md for Gleam, authored on Day 10 to length-match `v0-skill` within ±10%, and run only at that point |

Noise-floor check: the `no-skill` arm is also run a second time with a different random seed for every (model, task). Any SKILL.md effect that does not exceed this floor is not a real effect.

**Run order:** the baseline matrix on Day 9 executes arms `{no-skill, llmdocs-mini, llmdocs-full}` plus the `no-skill` noise-floor re-run. On Day 10, after `v0-skill` is authored from the baseline failure analysis, `v0-skill` and the length-matched `irrelevant-ctrl` are run together so the two are directly comparable.

### 5.2 Generator models (three)

| Model | Access | Role |
|---|---|---|
| `claude-haiku-4-5` | Anthropic API (cheap paid, estimated ~$0.40 total) | Frontier-small Claude |
| `gemini-3-flash-preview` | Google AI Studio free tier | Frontier-small Google (current gen) |
| `meta-llama/llama-4-scout-17b-16e-instruct` | Groq free tier | Open-weights MoE (current gen) |

Rationale: three models spanning (Claude-family, Google-family, open-weights) so we can ask *"does context help weaker models more than stronger ones"* — the headline foundation-model framing.

**Revision note (2026-04-19, before any eval ran):** original spec named `gemini-2.5-pro` and `llama-3.3-70b-versatile`. Confirmed via live API check that Gemini 3 Pro Preview is not on Google's free tier (429 `limit:0`), so generator slot moved to Gemini 3 Flash Preview. Open-weights slot upgraded from Llama 3.3 70B to current-generation Llama 4 Scout for consistency with "current-gen across the board." No results were produced under the earlier names; pre-registration integrity is intact.

### 5.3 Task set (ten tasks, stratified)

Ten tasks across three buckets:

- **Syntax/types (3 tasks):** Jac-over-Python features — type annotations on `has`, `obj`/`node`/`edge` archetypes, filter-assign comprehensions, walker-less programs.
- **Graph construction (3 tasks):** build and mutate typed graphs using `node`/`edge` archetypes and the `++>`/`<++>` connect operators.
- **Walker traversal (4 tasks):** define walkers with `visit`, `disengage`, `skip`, and per-archetype abilities.

Skip `by llm()` bucket for v0.

Each task lives in `tasks/<bucket>/<id>/` and contains:
- `prompt.md` — the prompt shown to the generator: task description, function or walker signature, return/behavior contract. Written in HumanEval style (signature + docstring + one small input/output example).
- `solution.jac` — reference idiomatic solution. Hand-authored by Claude via `jac-mcp`, round-tripped through `validate_jac` and `jac run` against `tests.jac` before check-in. Used as anchor for judge pointwise-reference mode.
- `tests.jac` — hidden unit tests using Jac's native `test` blocks. The generator never sees this file.
- `rubric.md` — per-task idiomaticity rubric (Pathak 2025): which Jac constructs the task is meant to exercise, and what a 1-vs-3-vs-5 answer looks like for this task specifically.
- `meta.yaml` — `{task_id, bucket, created_at (2026-04-DD), jac_constructs_expected[], baseline_pass_target}`.

**Calibration rule:** before committing a task to the suite, pilot-run `no-skill / claude-haiku-4-5` on it five times. Reject if pass rate is 0/5 or 5/5 — such tasks cannot discriminate between arms. Target 1/5 to 4/5 baseline pass rate.

**Held-out set:** tasks `03` (last syntax) and `10` (last walker) — 20% of the suite, stratified across two buckets — are reserved as a sealed evaluation set. We do not look at their results while iterating the judge rubric or the `v0-skill` content. They are scored only at the end of Day 12 and reported separately alongside the main result.

### 5.4 Sampling protocol

- **K = 5 samples** per (task, arm, model, seed).
- **Temperature = 0.2** for all generation (HumanEval convention; within deployment-realistic range; not 0.0 — Miller §3.3).
- **Max output tokens = 2048** (enough for a full task solution; tasks are sized so solutions fit).
- **Prompt template** (identical across arms, only the arm block varies):

  ```
  <arm-context-block>

  ---

  <task-prompt>

  ---

  Return only the Jac code, no prose, no fences.
  ```

- **Order freeze:** task order, arm order within each task, model order within each arm, and seed sequence are fixed in a single `run_plan.jsonl` generated before any API call. The same plan is re-used when adding the `v0-skill` arm post-baseline.

Total generations per full run: 5 arms × 3 models × 10 tasks × 5 samples = **750** experimental generations, plus 150 noise-floor re-generations = **900 total**.

## 6. Measurement

### 6.1 Correctness (execution-based)

For each sample:
1. Write the generated code to a temp dir alongside the task's `tests.jac`.
2. Run `jac run tests.jac` as a subprocess with a **30-second wall-clock timeout** and a **256 MB memory cap**.
3. Parse the Jac test runner's output: `pass` iff all tests pass and exit code is 0; else `fail`. Timeouts and crashes count as `fail`.
4. Record `stdout`, `stderr`, `exit_code`, and `elapsed_ms` for the audit log.

Per-task, per-arm, per-model correctness metric: **pass@1 using Chen's unbiased estimator** `pass@k = 1 − C(n−c, k) / C(n, k)` with `n=5, k=1`. Also report `pass@5` as a secondary metric.

### 6.2 Idiomaticity (hybrid AST + LLM judge)

**Stage 1 — AST detectors (40% weight)**

Six deterministic binary detectors applied per-sample. For v0 the detectors are **pattern-based** (regex over source code that has been stripped of comments and normalized via `jac-mcp`'s `format_jac`). Patterns target Jac-specific tokens and operators that Python cannot incidentally produce (e.g., the literal `walker` keyword, the `++>`/`<++>` connect operators, `can ... with <archetype> entry`). Each detector is unit-tested on one known-positive and one known-negative Jac snippet before being trusted. v1 may upgrade to AST-based detection via `jac-mcp`'s `get_ast` if pattern-based detection proves fragile; for v0 the pattern approach is sufficient because normalized source is already being fed to the judge.

The six detectors:

1. `uses_walker` — at least one `walker` archetype defined.
2. `uses_visit` — at least one `visit` statement inside a walker.
3. `uses_typed_edge_archetype` — graph edges declared as `edge` archetypes, not as dict-of-lists or ad-hoc dataclasses.
4. `uses_connect_op` — edges created via `++>` or `<++>`, not direct field assignment.
5. `has_type_annotations` — all `has` fields, parameters, and returns are type-annotated.
6. `uses_abilities_on_nodes` — node-side logic lives in abilities defined on the archetype, not in external functions.

Detector subscore: fraction of detectors that return "yes" among those the task's rubric marks as *expected* for that task (from `meta.yaml.jac_constructs_expected`). A detector not expected for a task is neither credit nor penalty.

**Stage 2 — LLM judge (60% weight)**

- Judge model: `openai/gpt-oss-120b` via Groq (free tier). Deliberately non-Anthropic, non-Google, and non-Meta — so no self-preference bias when judging output from any of the three generator families. 120B params is large enough for structured rubric-grading tasks. Originally specified as Gemini 2.5 Pro; changed 2026-04-19 (before any eval ran) for the same free-tier reason as the generator change and to eliminate Gemini self-preference when judging Gemini generations.
- Prompt format: Prometheus-style (Kim et al. ICLR 2024). System block contains the task's `rubric.md` and the reference `solution.jac`. User block contains the generated code. Instruction explicitly:
  - Lists which idiomatic Jac constructs appear in the candidate first, citing line numbers.
  - Evaluates each rubric item.
  - Penalizes Python-transliterated patterns explicitly (direct language — "if this reads like Python with Jac syntax, not Jac, score 1–2 regardless of test pass status").
  - Emits structured JSON: `{"constructs_present": [...], "per_criterion": {...}, "feedback": "...", "score": <1-5>}` followed by a final `[RESULT] X` line.
- Runs per sample: **3 judgments, report median** (self-consistency, Zheng 2023).
- Normalization: before sending to judge, strip comments and run `format_jac` on the candidate ("Don't Judge Code by Its Cover," arXiv:2505.16222).

**Combined idiomaticity score per sample:**
```
idiom_score = 0.4 * ast_subscore + 0.6 * (median_judge_score / 5.0)
```
Range: 0.0 to 1.0.

### 6.3 Judge validation (mandatory gate)

Before trusting any idiomaticity delta:
1. Claude hand-labels **15 Jac snippets** spanning the 1–5 quality spectrum, drawing from existing Jaseci example repos and deliberately-Python-transliterated foils. Each label cites specific rules from `jac://guide/pitfalls` or `jac://guide/patterns` as justification. Labels are committed to `judge/validation/hand_labels.jsonl` before the judge runs on them.
2. Run the judge (3 runs, median) on each snippet.
3. Compute **Cohen's κ** on the 1–5 ordinal labels.
4. **Gate: κ ≥ 0.4** (Landis-Koch "substantial"). If κ < 0.4, iterate the rubric and re-validate. Do not run the main matrix until the gate passes. Document every rubric revision in `judge/validation/rubric_history.md`.

## 7. Analysis

### 7.1 Paired statistics

- **Correctness deltas** (`skill-arm − no-skill`, per-task): **McNemar's test** on the 2×2 flip table (pass→pass / pass→fail / fail→pass / fail→fail). Report exact p-values given small N.
- **Idiomaticity deltas** (`skill-arm − no-skill`, per-task): **paired bootstrap**, 10,000 resamples, 95% percentile intervals.
- **Small-N CIs on pass rates:** Bayesian Beta-Binomial (Jeffreys prior) or Wilson score intervals. Never CLT (Bowyer 2025).
- **Correlation between arms:** report Pearson ρ of per-task scores between `no-skill` and each skill arm. Confirms whether paired analysis actually bought power.

### 7.2 Required report sections

`RESULTS.md` contains, in this order:

1. **Headline table** — pass@1 and mean idiomaticity, per (arm, model), with CIs.
2. **Paired deltas** — Δ(arm, no-skill) per model and per stratum, with paired bootstrap CIs.
3. **2×2 flip tables** — one per (skill-arm, model) pair.
4. **Per-stratum breakdown** — syntax / graph-construction / walker-traversal, separately.
5. **Cross-model interaction** — does the best arm for Claude Haiku differ from the best for Llama? Is the skill-vs-no-skill delta larger for weaker models?
6. **Judge validation evidence** — Cohen's κ, plus confusion matrix on the 15 hand labels.
7. **Noise-floor and irrelevant-context controls** — deltas for `no-skill(seed-A) vs no-skill(seed-B)` and for `irrelevant-ctrl vs no-skill`. Any claimed effect must exceed both.
8. **Decision** — pre-committed thresholds (§7.3) applied to the observed data.
9. **Honest caveats** — N=10, stratum sizes, judge κ, what v1 needs.

### 7.3 Pre-committed effect thresholds (frozen 2026-04-19)

A skill arm is declared *"useful"* iff **both** hold when compared against `no-skill`, averaged across the three models:

- **Idiomaticity:** paired mean Δ in idiom_score ≥ **+0.10** (on the 0–1 combined scale), AND
- **Correctness:** paired mean Δ in pass@1 ≥ **+10 percentage points**, OR paired Δ in idiomaticity ≥ **+0.15** with correctness at least directionally positive (≥ 0 pp).

A skill arm is declared *"better than the LLMDocs baselines"* iff its paired Δ vs. the stronger of `llmdocs-mini`/`llmdocs-full` meets the same thresholds.

Any claimed effect must also **exceed the noise-floor and irrelevant-context control deltas** by at least 2× on whichever metric is being claimed.

## 8. Controls (already listed above, consolidated here)

- **Irrelevant-context arm** — a Gleam SKILL.md of comparable length to `v0-skill`. Rules out "more tokens" null.
- **Noise-floor re-run** — `no-skill` with a different seed. Rules out "this is just stochasticity" null.
- **Held-out tasks** — tasks 9 and 10 are not inspected during iteration. Their results are reported separately and compared to tasks 1–8.

## 9. Architecture

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ Task + Arm +     │───▶│ Generator        │───▶│ Jac runner       │
│ Model → Prompt   │    │ (Claude/Gemini/  │    │ (subprocess,     │
│ builder          │    │  Llama APIs)     │    │  jac run)        │
└──────────────────┘    └──────────────────┘    └─────────┬────────┘
                                                           │
                                                           ▼
                                           ┌──────────────────────────┐
                                           │ Correctness scorer       │
                                           │ (pass@1 unbiased, flip)  │
                                           └───────────┬──────────────┘
                                                       │
                               ┌───────────────────────┼─────────┐
                               ▼                       ▼         ▼
                    ┌──────────────────┐    ┌──────────────────┐ ┌─────────────┐
                    │ AST detectors    │    │ LLM judge        │ │ Audit log   │
                    │ (via jac-mcp)    │    │ (GPT-OSS 120B    │ │ (JSONL,     │
                    │                  │    │  via Groq,       │ │  one per    │
                    │                  │    │  3-run median)   │ │  sample)    │
                    └─────────┬────────┘    └────────┬─────────┘ │             │
                              │                      │            └─────────────┘
                              └──────────┬───────────┘
                                         ▼
                               ┌──────────────────┐
                               │ Idiom score      │
                               │ (0.4*AST + 0.6*J)│
                               └─────────┬────────┘
                                         ▼
                               ┌──────────────────┐
                               │ Stats & report   │
                               │ (paired bootstrap│
                               │  McNemar, Wilson,│
                               │  per-stratum)    │
                               └──────────────────┘
```

Each box maps to one Python module with one clear responsibility and well-defined inputs/outputs. No module reaches across boundaries.

## 10. Data flow

All intermediate state is JSONL, written to `.eval_cache/` (gitignored) with one line per unit-of-work:

- `run_plan.jsonl` — one line per (arm, model, task, sample_idx, seed) tuple. Generated once, before any API call. Committed to the repo so runs are reproducible.
- `generations.jsonl` — one line per sample: the tuple above plus `{prompt, completion, finish_reason, usage, wall_ms}`.
- `correctness.jsonl` — generation id plus `{passed, exit_code, stdout, stderr, elapsed_ms}`.
- `ast_scores.jsonl` — generation id plus `{per_detector: {...}, ast_subscore}`.
- `judge_scores.jsonl` — generation id plus `{three_runs: [{...}, {...}, {...}], median_score, feedback}`.
- `final_scores.jsonl` — generation id plus `{pass_at_1, idiom_score}`.

Final report (`results/RESULTS.md`) and a committed summary JSONL (`results/summary.jsonl`) are tracked; intermediate JSONL is not.

## 11. Repo layout (final)

```
jaceval/
├── CLAUDE.md                 # project instructions for Claude Code
├── README.md                 # public-facing; written last
├── design-recipe.md          # literature review / methodology source
├── .mcp.json                 # jac-mcp wiring (committed)
├── .gitignore
├── tasks/
│   ├── syntax/{01,02,03}/{prompt.md,solution.jac,tests.jac,rubric.md,meta.yaml}
│   ├── graph/{04,05,06}/...
│   └── walker/{07,08,09,10}/...
├── arms/
│   ├── no-skill/arm.md          # empty-ish base prompt
│   ├── llmdocs-mini/arm.md      # verbatim LLMDocs-Mini
│   ├── llmdocs-full/arm.md      # verbatim LLMDocs-Full
│   ├── v0-skill/arm.md          # our SKILL.md (written post-baseline)
│   └── irrelevant-ctrl/arm.md   # Gleam SKILL.md (control)
├── harness/
│   ├── prompts.py               # prompt assembly
│   ├── generators.py            # thin clients for Claude/Gemini/Groq
│   ├── jac_runner.py            # subprocess jac run + pass/fail parsing
│   ├── detectors.py             # AST idiom detectors (jac-mcp-backed)
│   ├── judge.py                 # Gemini judge client + 3-run median
│   ├── scorer.py                # combined idiom score
│   ├── stats.py                 # McNemar, paired bootstrap, Wilson, Cohen's κ
│   └── run.py                   # orchestrator; reads run_plan.jsonl, writes all outputs
├── judge/
│   ├── rubric.md                # generic rubric scaffold (per-task rubrics live in tasks/)
│   ├── prompt.md                # Prometheus-format prompt template
│   └── validation/
│       ├── snippets/*.jac       # 15 hand-labeled Jac snippets
│       ├── hand_labels.jsonl    # labels with justifications
│       └── rubric_history.md    # every rubric revision during validation
├── results/
│   ├── RESULTS.md               # the writeup
│   └── summary.jsonl            # committed summary of final run
└── docs/specs/
    └── 2026-04-19-jaceval-v0-design.md   # this file
```

## 12. Timeline (14 days including buffer)

- **Day 1 — Harness skeleton.** `jac_runner.py` plus one throwaway task. `jac run` produces pass/fail reliably, with timeout and memory cap. Smoke-test on a known-good and a known-bad Jac file.
- **Day 2 — Generator clients.** `generators.py` for Claude, Gemini, Groq. Prompt assembly in `prompts.py`. Smoke-test one generation per model.
- **Days 3–5 — Task authoring.** 10 tasks with `prompt.md`, `solution.jac`, `tests.jac`, `rubric.md`, `meta.yaml`. Each solution round-tripped through `validate_jac` + `jac run tests.jac` before check-in. Pilot each task with `no-skill / claude-haiku-4-5 × 5` to calibrate to 1–4 / 5 baseline pass rate. Tasks failing calibration are revised or rejected.
- **Day 6 — AST detectors.** Six detectors in `detectors.py` driven by `jac-mcp`. Unit-test each on a known-positive and a known-negative Jac snippet.
- **Days 7–8 — Judge + validation.** `judge.py` with Prometheus prompt. Hand-label 15 snippets into `judge/validation/`. Run judge 3×, compute Cohen's κ. Iterate rubric until κ ≥ 0.4. Record every revision in `rubric_history.md`.
- **Day 9 — Baseline matrix.** Write `run_plan.jsonl` for arms `{no-skill, llmdocs-mini, llmdocs-full}` × 3 models × 10 tasks × 5 samples, plus the `no-skill` noise-floor re-run with a different seed. Execute; collect everything into JSONL. Held-out tasks 03 and 10 are generated in this run too but their scores are not inspected yet.
- **Day 10 — `v0-skill` authoring + irrelevant-ctrl.** Inspect failure modes from Day 9 on tasks 01–02, 04–09 (dev set only). Author `arms/v0-skill/arm.md` targeting those failures. Author `arms/irrelevant-ctrl/arm.md` as a Gleam SKILL.md length-matched to `v0-skill` within ±10%. Run both arms across 3 models × 10 tasks × 5 samples. Held-out tasks still not inspected.
- **Days 11–12 — Stats and writeup.** `stats.py`, `RESULTS.md` draft. Apply pre-committed thresholds. Run the held-out tasks 9–10 last, report them separately.
- **Day 13 — README, polish, quickstart verification.** Clean-room clone of the repo, run `make eval` on free-tier credentials, confirm it reproduces.
- **Day 14 — Buffer.** Something will break; this is where it gets fixed.

Scope gate checks: at end of Day 5, if fewer than 10 tasks pass calibration, drop the scope to `N=8` rather than slip. At end of Day 8, if κ < 0.4 after three rubric revisions, drop to an AST-only idiomaticity score (no LLM judge) and note the limitation explicitly in `RESULTS.md`.

## 13. Budget

| Line item | Estimate |
|---|---|
| Claude Haiku 4.5 generation (900 gens × ~2K in + 500 out) | ~$0.40 |
| Gemini 3 Flash Preview generation (free tier) | $0.00 |
| Llama 4 Scout 17B via Groq (free tier) | $0.00 |
| GPT-OSS 120B via Groq judge (2,700 judgments, free tier) | $0.00 |
| Dev-loop iteration overhead (~2× above) | ~$0.80 |
| **Total projected** | **~$1.20** |
| Hard ceiling | $5.00 |

If any design change would push past $5, flag before spending.

## 14. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Judge κ < 0.4 after iteration | Pre-committed fallback: AST-only score, documented as a limitation |
| Free-tier rate limits (Gemini, Groq) stall Day 9 matrix | `run.py` implements exponential backoff and resumable JSONL; can run overnight |
| Tasks cluster at 0/5 or 5/5 baseline pass | Day-3-5 calibration gate; reject non-discriminating tasks |
| `jac run` flakiness on specific constructs | All solutions round-tripped before check-in; `jac-mcp`'s `validate_jac` gates task check-in |
| Judge self-preference leaks in despite non-family rule | Prompt explicitly penalizes Python-transliterated patterns; 3-run median stabilizes |
| Scope creep into `by llm()` bucket | Hard "out of scope" in §4; logged as v1 feature |
| Held-out-set surprise — tasks 9–10 behave very differently from 1–8 | Reported separately; part of the honest caveats |

## 15. Success criteria (restated for the decision gate)

v0 ships when:

- [ ] All 10 tasks pass calibration and their `solution.jac` passes `jac run tests.jac` on check-in.
- [ ] Judge κ ≥ 0.4 on 15 hand-labeled snippets (or the AST-only fallback is invoked and documented).
- [ ] The full 5-arm × 3-model × 10-task × 5-sample matrix completes cleanly with all JSONL written.
- [ ] `RESULTS.md` includes every section listed in §7.2.
- [ ] `make eval` reproduces the pipeline from a clean clone using free-tier credentials only.
- [ ] Pre-committed thresholds (§7.3) are applied as stated — the decision rule was not changed after seeing results.

## 16. Related prior art (short)

- **Cassano et al., MultiPL-E (IEEE TSE 2023)** — per-language Translator/Runner pattern. We reuse the shape, not the code.
- **Miller 2024 "Adding Error Bars to Evals" (arXiv:2411.00640)** — paired-SE reduction; source of the N=10 defensibility argument.
- **Kim et al., Prometheus (ICLR 2024)** — judge prompt format. We reuse, we do not use the fine-tuned model itself.
- **Pathak et al., "Rubric Is All You Need" (ICER 2025)** — per-task rubrics outperform generic. Shapes our per-task `rubric.md` design.
- **Chen et al. 2021** — unbiased pass@k estimator.
- **"Don't Judge Code by Its Cover" (arXiv:2505.16222)** — normalize formatting before judging.

## 17. v1 (explicitly out of this spec)

- `by llm()` task bucket with stub design or real LLM execution.
- Expansion to 40–60 tasks (recipe §51 of `design-recipe.md`).
- Dual-judge ensemble with agreement reporting.
- CodeBLEU or tree-sitter-jac structural metrics as a secondary idiomaticity signal.
- Inspect AI migration for audit-grade logging.
- Additional generator models (Claude Sonnet, GPT-5, DeepSeek-Coder).
- Second niche language target to validate generalization claim.
