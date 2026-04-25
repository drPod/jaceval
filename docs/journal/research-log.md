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

---

## 2026-04-20 — Arm authorship surfaced a pitfall we hadn't found by task authorship

While authoring `arms/v0-skill/arm.md` from the existing 16-pitfall log, the subagent discovered a pitfall that had not appeared in any eval-task work: **Jac has no `let` keyword**. Local bindings are bare assignments; `let x = 5;` fails with `Missing ';'` at the `=` plus `Name 'let' may be undefined`. Rust/TypeScript intuition makes `let` a default reach for LLMs (and for the subagent — it wrote several `let`s in the first draft before `validate_jac` caught it).

**Methodology implication.** Arm authorship is itself a discovery method, not merely a response to prior-discovered failures. The hand-labeled pitfall corpus was built from authoring 10 eval tasks; writing the teaching doc *about* those tasks revealed a 17th pitfall independent of any task. That suggests there may be more surface-level Jac traps we haven't caught yet, and future v1 work should treat any reference-material authoring (tasks, arm docs, validation snippets) as candidates for discovering new pitfalls — not just as consumers of them.

**Process change.** Every code example embedded in an arm file (not just eval-task `solution.jac`) must `validate_jac` before commit. The subagent-dispatch template should mention this explicitly so arm-authoring and task-authoring have symmetric discipline.

---

## 2026-04-20 — Mini-run scope decided (deeper-than-SKILL-helps)

Decision: before requesting Mars's backing for a full-scale run (3 models × 5 samples × noise-floor = expensive), execute a mini-run that demonstrates methodological rigor rather than the trivial `v0-skill > no-skill` result. Shape:

- **4 arms**: no-skill, llmdocs, v0-skill, irrelevant-ctrl.
- **1 model**: Llama 4 Scout 17B via Groq (most reliable free-tier model, no quota headache).
- **All 10 tasks** (2 held out) — preserves stratum coverage.
- **3 samples** per (arm × task) — 4 × 10 × 3 = 120 generator calls + 360 judge calls.

Four cuts the run is designed to deliver, numbered by interest priority:
1. Per-arm pass rate + Wilson 95% CI + mean idiomaticity (baseline).
2. **v0-skill vs llmdocs**: paired flip table, McNemar, paired-bootstrap 95% CI on idiomaticity Δ — answers "does our doc beat Jaseci's existing doc?"
3. **Per-construct AST breakdown**: which specific Jac idioms does each arm teach? Per-detector activation rate per arm.
4. **Correctness-vs-idiomaticity dissociation**: pass_hi / pass_lo / fail_hi / fail_lo contingency per arm — shows the cases a correctness-only eval would miss. Validates the hybrid AST+judge score.
5. Bonus: **v0-skill vs irrelevant-ctrl** — tokens-don't-matter falsification.

What makes this defensible as a Mars-note deliverable is cuts 2/3/4, not cut 1. Cut 1 is trivially "yes docs help"; cuts 2–4 are where the methodology earns its keep.

---

## 2026-04-20 — Authored v0-skill + irrelevant-ctrl. Known shape-alignment caveat.

`arms/v0-skill/arm.md` (2,761 words) derived from the 17-pitfall log; covers 19/21 authorship-relevant pitfalls. `arms/irrelevant-ctrl/arm.md` (2,818 words, 102% of v0-skill — within ±5% target) pulled from Gleam's tour, cheatsheet, and language reference.

**Shape-alignment caveat.** The v0-skill uses standard OSP teaching archetypes — `Person`, `City`, `Road`, `Post` — as its code examples. `Road` with a `distance: float` edge field directly mirrors graph/06's setup; `Post` with a `views: int` counter mirrors walker/09's. Both are also stock teaching archetypes in Jaseci's own LLMDocs, so the comparison `v0-skill` vs `llmdocs` is not advantaged/disadvantaged by the choice. But `v0-skill` vs `no-skill` should read any walker/09 and graph/06 lift with this in mind — v0-skill may be partly "here's a pattern very close to the one the task needs" rather than purely "here's how Jac works." The per-stratum breakdown (cut 3) will make this visible: if lift concentrates on walker/09 and graph/06 specifically, pattern-proximity is the explanation. v1 SKILL.md authoring should explicitly avoid type names and field shapes used by any eval task to tighten this.

---

## 2026-04-21 — PR target for the `<++>` doc bug is upstream, not jaseci-llmdocs

**Context.** After the mini-run landed, the plan was to capitalize on one of the 17 pitfalls as an upstream PR — concretely, to fix the `<++>` "Bidirectional" wording in `jac-llmdocs.md` and use it as a legitimate re-engagement hook with Mars. Pre-PR investigation changed the target.

**What we found.**
- `jaseci-labs/jaseci-llmdocs` is an internal build artifact, not a community project. 0 stars, 0 forks, 0 external PRs ever, no README, no CONTRIBUTING, no LICENSE. `release/jac-llmdocs.md` is *auto-generated* by `python run_pipeline.py` on every push touching `config/`, `src/`, or `config/rag_rules.txt`. Generation is an LLM call (Claude Opus 4.6, `temperature: 0.0, seed: 42`) that assembles the final doc from (a) upstream `jaseci-labs/jaseci` at `docs/docs/**.md`, plus (b) the in-repo prompt rules at `config/rag_rules.txt`. A PR that edits the generated `.md` directly would be overwritten on the next pipeline run.
- The wrong "Bidirectional" wording for `<++>` lives verbatim in three upstream files in `jaseci-labs/jaseci`:
  - `docs/docs/quick-guide/syntax-cheatsheet.md` (`a <++> b; # Bidirectional a <-> b`)
  - `docs/docs/reference/language/osp.md` § Edges.3 (`a <++> b; # Undirected: a ↔ b (creates edges both ways)`)
  - `docs/docs/reference/language/foundation.md` § Graph Operators (`node1 <++> node2; # Bidirectional`)
  - plus the same framing applied to the typed form in `osp.md` § Graph Construction.2 (`Bidirectional typed`)
- `config/rag_rules.txt` never mentions `<++>` / "bidirectional" / "undirected" / "symmetric" at all. The rag rules only prescribe typed-edge syntax. So the wrongness is inherited 1:1 from upstream docs, not invented by the assembly step.
- `jaseci-labs/jaseci` is the *right* target and it is *very* active. 10+ PRs merged on 2026-04-21 alone, same-day turnaround. Has `CONTRIBUTING.md` at root, no CLA, fork-and-PR flow. Requires a release-note fragment at `docs/docs/community/release_notes/unreleased/<package>/<PR#>.<category>.md` (category `docs` fits).

**Skeptical check on the fix.** Pre-PR worry: maybe the Jaseci team defends "undirected storage" as a conceptual stance elsewhere, and the right PR is a doc-clarification not a correction. Verdict: no. The `osp.md` that claims `<++>` "creates edges both ways" in § Edges.3 itself treats `[<-->]` as a query-time direction-agnostic traversal in § Walkers.3 (`visit [<-->]; # Visit both directions`) and § Data Spatial Queries.1 (`both = [<-->]; # Both directions`). The Edges.3 section is the outlier. Fixing it aligns it with the framing the rest of the doc already uses — not a semantic change, a consistency correction.

**Decision.** PR goes to `jaseci-labs/jaseci`, bundling the three files (syntax-cheatsheet, osp.md § Edges.3, foundation.md Graph Operators), plus the `<+: Type :+>` "Bidirectional typed" label in osp.md § Graph Construction.2. One PR, four files. Include a runtime-probe snippet (`a <++> b; print([b -->]);` → `[]`) in the PR body as evidence. Add release-note fragment under `docs/docs/community/release_notes/unreleased/jaclang/<PR#>.docs.md`.

**What to watch for downstream.**
- **Framing of the Mars note changes.** We can no longer say "we found a bug in your jac-llmdocs and submitted a fix." The honest framing is: "we found a bug in your canonical docs (upstream of the LLM-assembled llmdocs) and submitted a fix there." The upstream attribution is *more* impressive, not less — it means the bug has been propagating to every LLM-generated doc downstream of your canonical source. But the wording must be accurate.
- **Any future `jac-pitfalls.md` entry that names `jac://docs/...` as the wrong source** should also point to the upstream `jaseci-labs/jaseci/docs/docs/**.md` path, since that's what actually ships the wrongness. Default hypothesis for any llmdocs.md vs. runtime contradiction: look upstream first; `rag_rules.txt` only shapes a narrow set of topics it chose to pin (typed-edge syntax, a handful of idiom rules).
- **Zero external-PR history on jaseci-llmdocs** is worth remembering if we ever need to contribute to the assembly pipeline itself (e.g. expanding `rag_rules.txt` to cover more pitfalls). We'd be the first external PR there, which could be faster or slower than a normal repo depending on who's on call for the bot.

**Process note.** This is the first time in v0 that an investigation changed a downstream plan (PR target) materially. The five-minute check — "is the artifact I'm about to fix actually the source?" — paid for itself. Worth making it standard for any future "upstream" contribution: verify the repo accepts community PRs AND that the file is hand-maintained, before writing a single line of the PR.

---

## 2026-04-22 — PR #5665 review state and wording revision

**What happened.** PR [jaseci-labs/jaseci#5665](https://github.com/jaseci-labs/jaseci/pull/5665) opened 2026-04-21 with replacement wording describing `<++>` as creating a single directed edge. Two rounds of review pushback on 2026-04-22:

1. **kiptuidenis (maintainer)** pointed at [#5575](https://github.com/jaseci-labs/jaseci/pull/5575) ("Ensure bidirectional traversal for undirected edges"), suggesting "upgrade to jac 14.0 fixes it." Factually off on the release timing — #5575 merged 2026-04-17 at commit `c0496f79`, and `jaclang-v0.14.0` was tagged 2026-04-16. `git tag --contains c0496f79` returns empty; no released jaclang has the fix. Pre-upgrade and post-upgrade probes both reproduced `[b -->] == []` on 0.13.5 and 0.14.0.
2. **Copilot** flagged 5 inline threads objecting that, on current `main`, `<++>` creates a single *undirected* edge (`is_undirected=True`), not a directed `a → b` edge. Copilot is correct about main — the revised wording originally described pre-#5575 behavior.

**What we learned.** #5575 changes storage: `<++>` now stores a single edge with `is_undirected=True`, and the runtime's `get_edges` / `edges_to_nodes` treat `effective_dir = ANY` when the edge is undirected. Still one edge. The docs' "creates edges both ways" wording has never been accurate — not on pre-fix (one directed edge) and not on post-fix (one undirected edge). PR target is `main`, so the accurate replacement describes post-#5575 single-undirected-edge semantics. Revised commit `11824d87f` pushed; kiptuidenis reply and 5 Copilot inline replies posted; inline threads resolved.

**What to watch for downstream.**

- **Harness version drift.** jaceval's `.venv` is on jaclang **0.14.0**. `pyproject.toml` pins no jaclang version directly (only `jac-mcp>=0.1.10`, which pulls jaclang transitively). For v0's runs, `<++>` semantics are pre-#5575 (single directed edge; `[b -->]` → `[]`). If the venv is ever rebuilt or someone bumps jaclang past whatever release first includes #5575, the pitfall regime flips. Any task solution that relies on `<++>` asymmetric traversal would score differently.
- **v0 scope stance.** Do not touch `tasks/**` in response to this. Controller to decide whether any task rubric should shift — flagged separately.
- **Methodology implication for the llmdocs arm.** The llmdocs arm is pinned to the pre-fix llmdocs (v0.12.1). When the next jaclang release ships with #5575 and upstream docs get re-generated, the llmdocs arm will be evaluating against *pre-fix* semantics while the runtime exhibits *post-fix* semantics. Pre-registration shields us — the arm was locked before #5575 merged, and cross-arm paired comparisons still hold — but the absolute idiomaticity number for the `<++>` task under llmdocs should be interpreted as "idiomatic for the runtime the arm documents," not "idiomatic for current jaclang." First observed case of a pinned-arm doc going stale due to a runtime fix in flight during v0.
- **Doc PR framing for the Mars note.** We now have a substantive story beyond "your docs say two edges and the runtime stores one." The richer story: the docs described two-edge storage on a runtime that never stored two edges; even after #5575 improved traversal symmetry, storage stayed at one edge. Our PR is the first time either set of wording aligns with either runtime regime. That's a cleaner hook than the original framing.

**Skeptical check.** Could the reviewer be right in a way I'm missing — e.g., does `c0496f79` appear in some tag I overlooked? Verified: `git fetch upstream --tags` pulled everything; `git tag --contains c0496f79` returns empty on all of (`jaclang-v*`, `v*`, `jaseci-v*`) tag families. `pip install --upgrade jaclang` lands on 0.14.0, post-upgrade probe reproduces the bug. The fix is genuinely unreleased.

**Process note.** "Upgrade to latest and re-run the probe" caught the review pushback cleanly — the upgrade itself was the evidence. Worth preserving as a default response to any reviewer claim of the form "X is fixed in version Y": install Y, re-run the probe, attach the output. Reviewer claims about release timing are especially easy to get wrong by a tag or a day.

---

## 2026-04-24 — PR #5665 superseded by maintainer-authored #5672

**What happened.** kiptuidenis (the same maintainer who had pushed back two days earlier) opened [#5672](https://github.com/jaseci-labs/jaseci/pull/5672) on 2026-04-22 with the comment *"you are absolutely right; since `<++>` stores a single undirected edge at the runtime level, describing it as 'two edges' or 'both ways' was misleading"* — and asked us to review. After two days of silence on our end (gap is on us, not him), we approved #5672 with one non-blocking suggestion (add a `[<-->]` query-side cross-reference in `osp.md`), and closed #5665 as superseded.

**What #5672 does differently.** Smaller-scope, conservative wording fixes — pure label/gloss swaps, no rewrite of `osp.md` § Edges.3. But three files we missed: `appendices.md` (operator table), `library-mode.md` (the `build_edge(is_undirected, ...)` API doc), and `tutorials/language/coding_primer.md`. Net: better coverage, shallower per-site rewrite. Trade-off lands on the side of the maintainer's PR.

**What this changes for the Mars-note framing.** Stronger story than "our PR merged." The actual sequence is: (1) we found the bug while building jaceval, (2) opened a doc PR with a runtime probe as evidence, (3) the maintainer initially pushed back citing #5575, (4) we caught the version-timing gap (#5575 merged one day after v0.14.0 was tagged) and revised our wording to match post-#5575 semantics, (5) the maintainer accepted the substantive point, opened a broader fix on their own initiative, and asked us to review. That's a collaboration outcome, not an external contribution. Worth foregrounding in the writeup over "we landed a doc PR" — same finding, more credible scaffolding.

**What to watch for downstream.** None directly from this. The pinned-arm staleness watchpoint from the 2026-04-22 entry still stands: when the next jaclang release ships #5575, the llmdocs arm (frozen at v0.12.1) will be evaluating against pre-fix semantics while users running current jaclang will see post-fix behavior. Rubric/pitfall re-check trigger remains the same.

**Process note.** Two-day silence after a maintainer asks for review is the worst state — reads as either flaky or passive-aggressive, neither of which is true here. Default rule: if a maintainer engages substantively, respond inside 24h even if the response is just "looking — back to you by EOD tomorrow." The cost of a holding-pattern reply is zero; the cost of two days of silence is non-zero on the relationship.

---

## 2026-04-24 (later) — #5672 closed over internal naming dispute; doc bug stays live

**What happened.** ~5h after we approved #5672, [Thamirawaran](https://github.com/Thamirawaran) (a different Jaseci collaborator, not kiptuidenis) commented and the PR was closed within 6 minutes. The comment, in full:

> As we can traverse bidirectionally through bidirectional edge, it should be bi directional. why we need to name it as undirected?
> Let me clarify
> Initially there was a bug in creation of bidirectional edges. This issue is fixed in #5575. and PR naming has conflict. But anyway it is bidirectional edge. therefore this issue is currently outdated. And make sure in all of our documentation we keep the naming as bidirectional edge.

This is two Jaseci collaborators publicly disagreeing on internal terminology:

- **kiptuidenis** (opened #5672, accepted our framing): post-#5575 it's a "single **undirected** edge" — CS-standard terminology matching the runtime's `is_undirected=True` flag.
- **Thamirawaran** (closed #5672): keep the historical "**bidirectional**" branding because user-facing traversal is bidirectional. Considers #5575 to have resolved the issue and the PR therefore "outdated."

**What didn't get addressed.** Thamirawaran's comment defends the *label* but doesn't address the original wrong wording — `osp.md` § Edges.3 currently says `<++>` "creates edges both ways" (plural — implying two-edge storage). That's wrong under either naming convention. No version of the runtime ever stored two edges. By closing without re-scoping, the misleading prose stays in the docs.

**Decision: don't re-engage on the closed PR.** Two reasons:

1. **Path-dependence on the lab affiliation.** Onboarding paperwork is in flight; May 2026 in-person kickoff. Re-opening a closed PR to argue terminology with a soon-to-be-colleague is the wrong way to enter — the expected value is negative regardless of who's right on the merits.
2. **The substantive point survives.** "Creates edges both ways" being wrong is independent of the bidirectional-vs-undirected dispute. Once onboarded, raise it through internal channels: small ask, both collaborators would likely agree on the prose fix, just need someone with insider standing to mediate. That person isn't us yet.

**What this means for the Mars-note framing.** Genuinely *more* interesting research material than a clean merge would have been. The story it tells:

- LLM-facing docs at Jaseci have inherited terminology that two of the lab's own collaborators disagree about.
- "Is the doc accurate" is downstream of "is the org aligned on what the operator IS called."
- For a SKILL.md or LLMDocs to be reliable on a niche language, the **upstream-org alignment problem** has to be solved first — or at minimum surfaced and worked around.
- jaceval's methodology *can* detect this kind of inconsistency (probe-based pitfall discovery + cross-arm comparison), even though it can't fix it. That's a methodology win, not a methodology gap.

**What to watch for downstream.**

- **Pitfall-log wording.** `docs/findings/jac-pitfalls.md` currently calls out "Bidirectional connect is misleading" using "undirected" as the contrasting term. With the lab apparently preferring "bidirectional" as the label, the *finding* still stands (one edge, not two; storage vs. traversal distinction) but the framing should not editorialize on the label dispute. Keep the pitfall about runtime behavior; don't take a side on what to call it.
- **README "Where things stand" section** — needs the closure noted so future-self isn't surprised that #5672 isn't merged.
- **Mars writeup** — the closure is a feature of the story, not a bug. Don't apologize for it; lead with it as evidence that the methodology surfaces upstream-org problems that LLM-docs work alone can't solve.

**Process note.** When a closed-PR outcome isn't a clean win or a clean loss but a "the upstream org disagreed with itself," the right artifact to update is the journal, not the PR. Re-engaging on the PR re-litigates; updating the journal preserves the evidence and lets the next conversation start from a clean position.
