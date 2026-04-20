# jaceval v0 — preliminary results

**Run date**: 2026-04-20
**Status**: pre-judge phase. Correctness + AST-detector results on a 100-entry mini-run are below. Idiomaticity (judge) scoring and the remaining 20 `irrelevant-ctrl` entries land on 2026-04-21 after Groq's daily token budget resets.

---

## TL;DR

1. **Free-tier Llama-4-Scout writes 0% valid Jac without context. Writes 40% with Jaseci's existing LLMDocs. Writes 57% with our v0-skill.** All 10 tasks, 3 samples per task per arm, same seed base.
2. **Length-matched irrelevant content does not help.** A 2,818-word Gleam SKILL.md (word-matched to our v0-skill) leaves Llama at 0%. "More tokens" is not the mechanism.
3. **Paired v0-skill vs LLMDocs is directional (+17 pp pass rate, flip table 7–2), not significant at this N** (McNemar p ≈ 0.18 on 9 discordant pairs). A full 3-model × 5-sample run would power this cleanly.

---

## What we built, why it's worth looking at

Mars's ask on 2026-04-09: *"the best .md or skill that makes the model as smart as possible in coding in Jac, and a methodology to evaluate it."* The methodology is the primary deliverable — the Jac skill is the worked example.

A defensible LLM-codegen eval for a niche language has to answer four things, not one:

1. **Does the context doc help at all?** Measurable with any baseline comparison. (Trivial; everyone gets this right.)
2. **Is the help about content, or about tokens?** Needs a length-matched irrelevant-language control. Most context-doc claims skip this and are unfalsifiable.
3. **Does the doc beat the pre-existing community doc?** Comparative: a new SKILL.md only earns its place if it outperforms what's already shipped. Requires a paired A/B against the real incumbent.
4. **Is the help on correctness, on idiomaticity, or both?** Hybrid AST + judge scoring because test-passing doesn't imply idiomatic. Requires a judge whose agreement with human labels is actually measured, not assumed.

jaceval v0 implements all four, at pilot scale. The preliminary mini-run below delivers clear results on (1)–(3); the judge-driven idiomaticity arm of (4) arrives tomorrow.

---

## Experimental setup

- **Tasks**: 10 hand-authored Jac tasks, stratified 3 syntax / 3 graph / 4 walker, 2 held out (syntax/03, walker/10). Each task: HumanEval-style prompt (zero Jac keywords in prompt — all arms see the same task description), hidden `tests.jac`, per-task rubric, `meta.yaml`.
- **Arms**: `no-skill` (minimal preamble), `llmdocs` (Jaseci's canonical `jac-llmdocs.md` v0.12.1, 3,387 words), `v0-skill` (ours, 2,761 words, derived from 17 empirically-discovered Jac pitfalls), `irrelevant-ctrl` (Gleam SKILL.md, 2,818 words — within 5% of v0-skill).
- **Generator (mini-run)**: Llama 4 Scout 17B via Groq. Temperature 0.2. 3 samples per (arm × task).
- **Correctness**: binary pass/fail from subprocessing `jac test` against the hidden tests, in an isolated temp directory.
- **Idiomaticity (planned, pending tomorrow)**: hybrid 0.4 × AST-detector subscore + 0.6 × LLM-judge median of 3 runs. Judge is GPT-OSS 120B via Groq (deliberately non-Anthropic, non-Google, non-Meta). Judge κ against 15 hand-labeled snippets validated yesterday at **κ = 0.500** (Landis–Koch "moderate"), clearing the pre-registered ≥ 0.4 gate.
- **Pre-registered thresholds**: `docs/specs/2026-04-20-pre-registration.md`, committed before any treatment-arm data was observed.

---

## Mini-run — what actually happened

We executed a 4-arm × 1-model × 10-task × 3-sample plan (120 entries) on 2026-04-20. 100 entries completed successfully on the generator side. The remaining 20 hit Llama's daily TPD quota mid-arm and are deferred to 2026-04-21. The three primary arms are complete (30/30 each); the `irrelevant-ctrl` arm landed only its first 10 entries — all syntax-bucket.

We are also deliberately deferring the judge phase to 2026-04-21 because Groq's gpt-oss-120b daily TPD budget was exhausted by yesterday's judge-validation run (κ = 0.500 against hand labels — see `judge/validation/run_log.md`). Rather than swap the judge family mid-experiment, which would invalidate the pre-registered judge choice, we split the pipeline: `harness/run.py --skip-judge` for the generator pass today, `--judge-only` to fill in idiomaticity tomorrow.

Practical consequence: this document reports correctness and AST-detector findings only. Idiomaticity deltas (cuts 2-idiom and 4) land tomorrow.

---

## Cut 1 — per-arm pass rate

| arm              |  n | pass rate |   95% CI (Wilson) |
|------------------|---:|----------:|------------------:|
| no-skill         | 30 |       0 % | [0.00, 0.11]      |
| irrelevant-ctrl  | 10 |       0 % | [0.00, 0.28]      |
| llmdocs          | 30 |      40 % | [0.25, 0.58]      |
| v0-skill         | 30 |      57 % | [0.39, 0.73]      |

Read: a single free-tier 17B-parameter model cannot produce a single runnable Jac snippet on 10 varied tasks with no context. Any doc that points it in the right direction lifts it 40–60 pp.

---

## Cut 2 — v0-skill vs Jaseci's LLMDocs

Paired at the sample level (same plan-seed per sample index within task):

```
flip table
                       llmdocs     llmdocs
                         pass        fail
  v0-skill  pass           10           7    ← v0-skill_only
  v0-skill  fail            2          11
                            ↑
                      llmdocs_only
```

- **v0-skill flips 7 samples that llmdocs missed**; llmdocs flips 2 that v0-skill missed.
- McNemar exact two-sided p = **0.180** on 9 discordant pairs. Directional, not significant at α = 0.05.
- Unpaired pass-rate Δ = **+17 pp** (57 % − 40 %), Wilson CIs overlap.

The direction is defensible; the N needed for significance is not reached at 30 samples per arm. Miller (2024) paired-SE math says we'd want ~80 tasks per arm to detect a 10 pp effect at 80 % power. v0 pilots 10 tasks, 30 samples per arm — scale-up to the plan's 3-models × 5-samples × noise-floor-control is where the question gets statistical teeth.

Cut 2 verdict at this N: **v0-skill is better than LLMDocs on correctness by the direction of the flip table, but the evidence does not clear a paired significance test.** The full-scale run is where this gets decided.

---

## Cut 3 — per-construct AST detector activation

Fraction of completions where each detector fires. Detectors are the 6 binary idiom detectors in `harness/detectors.py`.

| detector                         | irrelevant-ctrl | llmdocs | no-skill | v0-skill |
|----------------------------------|----------------:|--------:|---------:|---------:|
| uses_walker                      |             0 % |    27 % |      0 % |     20 % |
| uses_visit                       |             0 % |    27 % |      0 % |     20 % |
| uses_typed_edge_archetype        |             0 % |    40 % |      0 % |     40 % |
| uses_connect_op (`++>` / `<++>`) |             0 % |     3 % |      0 % |      0 % |
| has_type_annotations             |            90 % |    60 % |     80 % |     70 % |
| uses_abilities_on_nodes          |             0 % |     0 % |      0 % |      0 % |

Three findings from this table, in order of how non-obvious each is.

**Finding 3a.** `uses_abilities_on_nodes` is **0 % across every arm**. Neither LLMDocs nor our v0-skill reliably teaches node-side abilities, and Llama without prompting never uses them. Of our 10 tasks, only walker/09 probes this construct, and every model on every arm wrote walker-side abilities instead. This is a concrete per-construct gap, independently of the overall pass-rate story.

**Finding 3b.** `has_type_annotations` is ~80 % **even on no-skill**. Llama's default output style already carries type annotations; it is not something docs need to teach. Interestingly, `irrelevant-ctrl` (Gleam) is *the highest* at 90 % — Gleam is aggressive about types and the style bleeds through. This is a nice cross-check that the irrelevant-ctrl arm is changing model behavior in the ways you'd predict, just not in Jac-helpful ways.

**Finding 3c.** LLMDocs slightly out-teaches v0-skill on `uses_walker` / `uses_visit` (27 % vs 20 %). The bulk of the 17 pp pass-rate advantage for v0-skill therefore cannot be coming from "more walker syntax in training" — it must be coming from tighter rules that let the walker code that *is* written actually run (semicolons, braces, no `let`, idiomatic `obj`/`has` — the surface-syntax cluster). We will verify this against a fuller AST suite when v1 expands the detector set.

---

## Cut 5 — v0-skill vs irrelevant-ctrl (tokens-don't-matter falsification)

Partial: only the 10 overlapping `irrelevant-ctrl` samples (syntax-bucket tasks 01–03 plus task 04 sample 0). Even so:

- Paired flip table: **v0-skill 10, irrelevant-ctrl 0, both_pass 0, both_fail 0.** Every discordant pair is a v0-skill win.
- McNemar exact two-sided **p = 0.002**.

At this N this is uncontroversial: a length-matched Gleam SKILL.md does not lift performance; v0-skill does. **The mechanism is Jac content, not context length.**

The remaining 20 irrelevant-ctrl entries (graph + walker strata) are expected to strengthen this finding rather than weaken it — we'll confirm tomorrow, and update this document in place.

---

## Cuts 2-idiom and 4 — pending

- **Cut 2 idiomaticity delta** (paired bootstrap CI on hybrid score, v0-skill vs llmdocs) — blocked on the judge pass.
- **Cut 4** (correctness-vs-idiomaticity dissociation contingency: pass_hi / pass_lo / fail_hi / fail_lo per arm) — blocked on the judge pass.

These are the cuts that land tomorrow and close the story. In particular, cut 4 is where the hybrid AST + judge idiomaticity score earns its keep over a correctness-only eval: the cases where tests pass but the code is Python-transliterated are exactly the cases a conventional codegen eval would miss.

---

## Methodology — what makes this scalable to v1

The v0 harness is **generator-agnostic and language-retargetable by design**. Specifically:

- `harness/generators.py` dispatches to Claude, Gemini, and Groq via three thin wrappers — swapping in paid-tier Claude Opus, Gemini 3 Pro, or Llama 405B is a one-line change per wrapper. No other harness code changes.
- Task format (`tasks/<bucket>/<id>/{prompt,solution,tests,rubric,meta}`) is language-neutral. Retargeting to, say, Gleam or Roc is authoring a new task set and swapping the runner's `jac` subprocess for the target CLI. Detectors and judge format carry over with substitutions.
- The arm format follows Anthropic's Agent Skills spec — `arms/<name>/arm.md` with YAML frontmatter + Markdown body. Any new doc drops in as a fifth, sixth, seventh arm without code changes.
- Pre-registration (thresholds, controls, held-outs) and judge validation (κ ≥ 0.4 gate) are explicit gates in git history — every result produced is auditable against the commitments made before the run.

The sticking point on v0 was resource budget, not methodology. Free-tier Gemini caps at 20 requests/day; free-tier Groq at 200k tokens/day on gpt-oss-120b and 500k on Llama. A full-scale run (3 models × 5 samples × 4 arms × 10 tasks + noise-floor) is feasible with modest paid-tier backing — our estimated budget is under $15 for the full eval inclusive of judge.

---

## What we want to learn from the full run

At a full 3-generator × 5-sample × noise-floor configuration the claims we'd make or not make are those pre-committed in `docs/specs/2026-04-20-pre-registration.md`. Briefly:

- **Correctness:** SKILL.md helps iff it breaks the 0/n floor on ≥ 6 of 8 non-held-out tasks, AND exceeds irrelevant-ctrl on ≥ 4 of 8, AND passes the paired McNemar on pooled flips at α = 0.05.
- **Idiomaticity:** SKILL.md helps iff hybrid score lifts ≥ +0.20 absolute on ≥ 5 of 8 tasks, paired bootstrap 95 % CI excludes 0.
- **SKILL.md > LLMDocs:** iff v0-skill breaks the floor on strictly more tasks than llmdocs on the same generator (paired McNemar α = 0.05), AND mean idiomaticity is strictly higher (paired bootstrap 95 % CI excludes 0).

The directional evidence from this mini-run suggests the claims will land, but we do not call them at this N.

---

## Known limitations (honest accounting)

This is a v0 pilot, not a published benchmark. Material limitations, with pointers to how v1 addresses each:

1. **Single generator, single model tier** — Llama-4-Scout-17B via Groq free tier. The harness supports 3 generators; this mini-run uses 1 because Gemini-3-Flash's 20-req/day cap and paid-tier Haiku were out of mini-scope. v1 runs all three at paid tier.
2. **Judge validation κ = 0.500** on 15 snippets — at the low end of "moderate agreement." v1 expands the validation corpus to 30–50, adds an ensemble second judge, and reports judge κ with bootstrap CI.
3. **Shape-alignment in v0-skill examples** — the `Post`/`views` and `Road`/`distance` teaching examples in v0-skill align with walker/09 and graph/06 task shapes (same archetypes also appear in Jaseci's LLMDocs, so cut 2 is unaffected; cut-1 v0-skill-vs-no-skill on those two tasks should be read with pattern-proximity in mind). v1 authors arm content with explicit no-overlap on task type names.
4. **10 tasks is below Miller's 25-task floor for detecting 20 pp effects paired.** v0 is powered to detect floor-breaking; v1 scales to 40–60 tasks per the design recipe.
5. **Judge deferred.** Cuts 2-idiom and 4 land tomorrow.

---

## Reproducing

```bash
git clone <this repo>
cd jaceval
python -m venv .venv && .venv/bin/pip install -e .
cp .env.example .env  # fill in ANTHROPIC_API_KEY, GOOGLE_API_KEY, GROQ_API_KEY

# Build the mini plan (all 4 arms, Llama, 10 tasks, 3 samples = 120 entries)
.venv/bin/python -m harness.run --build-plan \
    --plan .eval_cache/mini_plan.jsonl \
    --arms no-skill llmdocs v0-skill irrelevant-ctrl \
    --models meta-llama/llama-4-scout-17b-16e-instruct \
    --tasks 01 02 03 04 05 06 07 08 09 10 \
    --n-samples 3

# Phase 1: generator + tests + AST (fast, no judge)
.venv/bin/python -m harness.run \
    --plan .eval_cache/mini_plan.jsonl \
    --out .eval_cache/mini_results.jsonl \
    --skip-judge

# Phase 2: judge (tomorrow, after Groq quota reset)
.venv/bin/python -m harness.run \
    --out .eval_cache/mini_results.jsonl \
    --judge-only

# Analyze
.venv/bin/python scripts/analyze_mini.py \
    --results .eval_cache/mini_results.jsonl \
    --out results/mini/summary.json
```

The only paid call in the above is none, if you're careful with free-tier budgets.

---

## Changelog

- **2026-04-20 20:00 CT** — v0 preliminary results drafted. Generator + test + AST pass complete for 100 / 120 entries. Judge and irrelevant-ctrl tail pending 2026-04-21.
