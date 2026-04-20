# jaceval v0 — pre-registration

**Committed 2026-04-20, before any SKILL.md, LLMDocs, or irrelevant-ctrl arm was run.**

This document freezes the claims that will count as "SKILL.md works" in v0 and the controls required to back them, so that seeing the results cannot influence the definition of success. Any change to this document after a non-baseline arm has been executed is p-hacking and must be an explicit, dated revision recorded below the original text (not a replacement).

---

## What has been run when this doc is committed

- Baseline **calibration** of all 10 tasks under `no-skill` + Claude Haiku 4.5 (first pass) and under `no-skill` + Gemini 3 Flash + Llama 4 Scout (second pass, after calibration helper was rewritten for free-tier). Aggregate baseline: **0/10 across every task, every free-tier model**. See `docs/journal/research-log.md` 2026-04-20 entries.
- Judge validation against 15 hand-labeled snippets: **Cohen's κ = 0.500**. See `judge/validation/run_log.md`.

What has **not** been run:
- No `llmdocs` arm, no `v0-skill` arm, no `irrelevant-ctrl` arm, for any task, under any generator.
- No noise-floor re-run of `no-skill`.

The thresholds below are therefore pre-registered in the strict sense: no treatment-arm data has been observed.

---

## Primary hypothesis

A deliberately-authored Jac SKILL.md improves correctness (execution-based) and idiomaticity (hybrid AST + judge) relative to (a) no context, (b) the existing Jaseci LLMDocs, and (c) a length-matched irrelevant-language SKILL.md.

## Thresholds

Claims gated on the 8 non-held-out tasks. Held-out tasks (`syntax/03`, `walker/10`) are revealed only after v0-skill + irrelevant-ctrl arms have been run and results committed.

### Correctness claim (binary pass@1 on `jac test`)

Given that every task calibrates at `0/n` under `no-skill` across all three free-tier generators, the defensible effect size is **floor-breaking**: did SKILL.md move a task from "no completions run" to "at least one completion runs and passes tests" under some generator?

We will claim SKILL.md **improves correctness** iff **all** of:

- [ ] **C1.** `v0-skill` produces `pass@1 > 0` on at least **6 of 8** non-held-out tasks under at least one of the three generators, averaged over 5 samples.
- [ ] **C2.** `no-skill` run #1 vs `no-skill` run #2 (noise floor — same arm, different seed base) does NOT produce `pass@1 > 0` on more than 1 of 8 tasks. (If the floor itself lifts, we can't attribute the SKILL lift to the doc.)
- [ ] **C3.** `v0-skill` exceeds `irrelevant-ctrl` on at least **4 of 8** tasks by at least the binary floor-break. (If a length-matched Gleam SKILL.md also breaks the floor as often, "more tokens" is doing the work, not "Jac content".)
- [ ] **C4.** Direction is positive on all three generators. Statistical significance via McNemar's is required on the aggregate flip table (pooled over generators) at α = 0.05.

We will claim SKILL.md **beats LLMDocs** iff `v0-skill` breaks the floor on **strictly more** of the 8 tasks than `llmdocs` does on the same generator. Paired comparison, McNemar's at α = 0.05.

### Idiomaticity claim (judge median 1–5, hybrid AST+judge composite 0–1)

We will claim SKILL.md **improves idiomaticity** iff **both**:

- [ ] **I1.** Per-task idiomaticity (0.4 × AST + 0.6 × normalized judge median) lifts by at least **+0.20 absolute** from `no-skill` to `v0-skill` on at least **5 of 8** non-held-out tasks, averaged over 3 generators × 5 samples.
- [ ] **I2.** Paired bootstrap 95% CI on the mean Δ over the 8 tasks excludes 0 (strictly positive).

We will claim SKILL.md **beats LLMDocs on idiomaticity** iff `v0-skill`'s mean idiomaticity exceeds `llmdocs`'s on at least 5 of 8 tasks, paired bootstrap 95% CI on Δ excluding 0.

### Stratum claims (descriptive, not primary)

We do **not** pre-commit to per-stratum thresholds because 3-3-2 task counts per stratum are too thin to power any per-stratum test. Per-stratum deltas will be reported in RESULTS as descriptive, not inferential.

### Held-out generalization check

After all claims above have been evaluated on the 8 non-held-out tasks, the 2 held-out tasks (`syntax/03`, `walker/10`) are revealed. They serve as an out-of-sample check:

- If effects on held-outs are **directionally consistent** with non-held-out effects (same sign on ≥1 of 2), we report as a generalization sanity check.
- If effects on held-outs **contradict** (opposite sign, both tasks), we flag it as a potential overfitting concern in RESULTS but do **not** revise the claims above — the primary claims are the primary claims.

---

## Required controls

All must be in place before the primary-claim check is valid.

- [x] **Paired A/B design.** Same tasks under every arm, frozen task order. (Shipped.)
- [x] **Execution-based correctness.** `jac test` subprocess with 30 s timeout. (Shipped: `harness/jac_runner.py`.)
- [x] **LLM judge validated against hand labels.** κ ≥ 0.4 pre-committed. (Met: κ = 0.500.)
- [x] **Per-task rubrics.** (Shipped in `tasks/<bucket>/<id>/rubric.md`.)
- [x] **Different-family judge** than any generator. (Shipped: GPT-OSS 120B via Groq.)
- [x] **Temperature > 0.** (Shipped: 0.2 generator, 0.3 judge.)
- [x] **Unbiased pass@k.** Chen (2021): `1 − C(n−c, k)/C(n, k)`. (To implement in Task 37.)
- [ ] **No-op noise floor run.** `no-skill` arm executed twice with different seed bases; Δ between the two runs bounds the within-arm variance floor. Required before any treatment-arm Δ can be credited. **To implement in Task 38 plan builder.**
- [x] **Irrelevant-context control.** `arms/irrelevant-ctrl/arm.md`. Must be authored as a length-matched Gleam SKILL.md. (Pending Task 43.)
- [x] **Held-out tasks sealed.** (Shipped: tasks `03` and `10` marked `held_out: true`.)

---

## Data handling

- Raw JSONL outputs (per completion) committed to `results/runs/*.jsonl`. No editing post-run.
- Summary statistics committed to `results/summary.jsonl`. Append-only.
- Any post-hoc analysis (not in this pre-registration) is labeled "exploratory" and cannot form the basis of a claim.

---

## Revision log

Revisions below this line must be dated, justified, and must NOT be in response to a significant observed effect in a treatment arm.

(No revisions yet.)
