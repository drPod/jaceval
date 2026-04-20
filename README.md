# jaceval

A paired-A/B harness for measuring whether context docs (LLMDocs, SKILL.md, etc.)
actually help frontier LLMs write idiomatic code in a niche language. Jac is the
v0 target; the harness is generator-agnostic and language-retargetable by design,
so dropping in Gleam / Roc / Dylan / any-other-niche-language is authoring a new
task set — not rewriting the pipeline.

Built in response to an invitation from Prof. Jason Mars / Jaseci Labs to prototype
*"the best .md or skill that makes the model as smart as possible in coding in Jac,
and a methodology to evaluate it."*

---

## tl;dr preliminary results (2026-04-20, pre-judge phase)

10 hand-authored Jac tasks, 3 samples per arm, Llama-4-Scout-17B via Groq:

| arm                                                     |  n | pass rate |  95 % CI     |
|---------------------------------------------------------|---:|----------:|-------------:|
| `no-skill`  (minimal preamble)                          | 30 |       0 % | [0.00, 0.11] |
| `irrelevant-ctrl` (2,818-word Gleam SKILL.md)           | 10 |       0 % | [0.00, 0.28] |
| `llmdocs`  (Jaseci's canonical `jac-llmdocs.md` v0.12.1) | 30 |      40 % | [0.25, 0.58] |
| `v0-skill` (ours, 2,761 words, derived from 17 pitfalls) | 30 |      57 % | [0.39, 0.73] |

- **Tokens-don't-matter falsification holds**: a length-matched Gleam doc does
  not lift performance. McNemar two-sided p = 0.002 vs `v0-skill` on overlapping
  samples.
- **`v0-skill` vs `llmdocs`**: paired flip table 7–2 in `v0-skill`'s favour,
  McNemar p = 0.18. Directional at N = 30, not significant; scale-up is where
  this decides.
- **Per-construct AST**: every arm is 0 % on `uses_abilities_on_nodes`. Neither
  doc reliably teaches node-side abilities. Concrete per-idiom gap.
- **`has_type_annotations`** is 80–90 % *without any context* — model default,
  not something docs earn.

Idiomaticity deltas (hybrid AST + judge) and the remaining 20 `irrelevant-ctrl`
entries land 2026-04-21 after Groq's daily quota resets. Full writeup in
[`results/RESULTS.md`](results/RESULTS.md). Pre-registered claim thresholds
(frozen before results were observed) in
[`docs/specs/2026-04-20-pre-registration.md`](docs/specs/2026-04-20-pre-registration.md).

---

## Why this eval is worth looking at

A defensible LLM-codegen eval for a niche language has to answer four things,
not one:

1. **Does the context doc help at all?** Measurable with any baseline comparison.
   Trivial; everyone gets this right.
2. **Is the help about content, or about tokens?** Needs a length-matched
   irrelevant-language control. Most "docs help" claims skip this and are
   unfalsifiable.
3. **Does the doc beat the pre-existing community doc?** A new SKILL.md only
   earns its place if it outperforms what's already shipped. Requires a paired
   A/B against the real incumbent.
4. **Is the help on correctness, on idiomaticity, or both?** Hybrid AST +
   LLM-judge scoring because test-passing doesn't imply idiomatic. Requires a
   judge whose agreement with hand labels is actually measured, not assumed.

jaceval v0 implements all four, at pilot scale.

---

## Architecture at a glance

```
tasks/<bucket>/<id>/        10 hand-authored Jac tasks
                            (prompt.md, solution.jac, tests.jac, rubric.md, meta.yaml).
                            2 held-out (sealed during iteration).
                            Prompts are Jac-keyword-free so all arms see identical problem statements.

arms/                       Context docs prepended to each task prompt.
├── no-skill/               Minimal preamble.
├── llmdocs/                Jaseci's canonical `jac-llmdocs.md` v0.12.1 (3,387 words).
├── v0-skill/               This project's SKILL.md (2,761 words), derived from 17 empirically-confirmed pitfalls.
└── irrelevant-ctrl/        Length-matched Gleam SKILL.md (2,818 words) — the tokens-don't-matter null.

harness/
├── prompts.py              Assemble `arm + task` into the model input.
├── generators.py           Unified LLM-client interface. Swap providers by editing three thin wrappers.
├── jac_runner.py           Subprocess `jac test`, parse stdout/stderr into TestResult.
├── detectors.py            6 pattern-based AST idiom detectors + run_all aggregation.
├── judge.py                GPT-OSS-120B via Groq, Prometheus-format, 3-run median.
├── scorer.py               0.4 × AST + 0.6 × judge_median/5 → idiomaticity ∈ [0, 1].
├── stats.py                Cohen's κ, Chen (2021) unbiased pass@k, exact McNemar, paired bootstrap, Wilson.
├── plan_builder.py         Cross-product (arm × model × task × sample), deterministic seeds, optional noise-floor group.
└── run.py                  Read plan → generate → test-in-tempdir → AST → judge → score → append JSONL.
                            `--skip-judge` and `--judge-only` modes for split pipelines.

judge/
├── prompt.md               Prometheus-format judge prompt with explicit Python-penalty instruction.
└── validation/
    ├── snippets/01..15.jac 15 hand-labeled Jac snippets (3 per score tier 1–5).
    ├── hand_labels.jsonl   Every justification cites a specific jac://guide URI or docs/findings entry.
    ├── rubric_history.md   Dated log of rubric revisions (none needed so far — κ met on first pass).
    └── run_log.md          Per-run judge-validation record (Cohen's κ = 0.500, clears ≥ 0.4 gate).

scripts/
├── calibrate_task.py       Per-task pilot-sample helper (free-tier by default).
├── validate_judge.py       Run judge on corpus, compute Cohen's κ, gate at ≥ 0.4.
└── analyze_mini.py         Analysis for the 5 methodological cuts.

docs/
├── specs/                  Frozen design specs. Pre-registration lives here.
├── plans/                  Implementation plans + the subagent dispatch template.
├── findings/               Empirical research artifacts.
│   └── jac-pitfalls.md     17+ concrete Jac gotchas discovered while authoring the eval.
│                           Candidate upstream bug-report list for Jaseci's docs.
├── journal/                Running process log.
│   └── research-log.md     Calibration tensions, methodology decisions, scope reframings.
└── deliverables/           Mars note, paper draft, public writeups (written near the end).

results/
└── RESULTS.md              Preliminary mini-run writeup.
```

---

## Methodology — the non-negotiables

From `design-recipe.md` + `docs/specs/2026-04-19-jaceval-v0-design.md`:

- **Paired A/B across arms**, same tasks, frozen order. Miller (2024) paired-SE
  reduction is how a small eval produces credible deltas.
- **Execution-based correctness**, LLM-judged idiomaticity. Never the reverse.
  `jac test` in a sandboxed subprocess decides pass/fail.
- **Chen (2021) unbiased pass@k** — `1 − C(n−c, k) / C(n, k)`. Never the
  biased `1 − (1 − p̂)ᵏ`.
- **Temperature > 0.** Deployment-realistic 0.2 for generator, 0.3 for judge.
  Averaging K samples kills noise without biasing results (Miller §3.3).
- **Hybrid idiomaticity**: 0.4 × AST detectors + 0.6 × normalized judge median.
- **Judge validation is mandatory**: Cohen's κ ≥ 0.4 against hand labels
  before trusting any delta. v0 lands at **κ = 0.500** (Landis–Koch "moderate").
- **Per-task rubrics** (Pathak et al. 2025 style) beat generic rubrics.
- **Different-family judge**: GPT-OSS-120B via Groq. Not Anthropic, not Google,
  not Meta — so no self-preference bias against any of the three generator
  families this eval supports.
- **Paired statistics**: McNemar exact on binary, paired bootstrap (10k
  resamples) on ordinal, Wilson intervals for small n. Never CLT at N = 30.
- **Controls**: irrelevant-context arm + no-op noise-floor re-run of
  `no-skill` with a different seed base (noise-floor runs live in v1).
- **Pre-commit the effect-size threshold** *before* looking at results.
  Prevents p-hacking. Ours:
  [`docs/specs/2026-04-20-pre-registration.md`](docs/specs/2026-04-20-pre-registration.md).

---

## The 17 Jac pitfalls the pitfall log catches

Discovered while authoring 10 eval tasks + the SKILL.md itself.
`docs/findings/jac-pitfalls.md` carries the full list; short version:

- `pass` is not a Jac statement (use `continue`).
- `test "name" { assert ...; }` — no `def` wrapper, trailing semicolons on
  assertions.
- `jac test` writes its summary to **stderr**, not stdout.
- `obj` / `node` / `edge` / `walker` archetypes. `has` fields require type
  annotations.
- Cross-file imports: `import from solution { sym }`. `validate_jac` emits
  a "Module not found" warning for sibling imports — it's a false positive.
- **`<++>` is a query-time affordance, not symmetric storage.** Both
  `a <++> b` and `a <+: Type :+> b` create a *single* directed edge. Prose
  in `jac://docs/osp` is misleading; runtime-confirmed.
- Typed-edge traversal filters: `->:Type:->` only. `[edge src -->:Road:->]`
  and `[<-:Type:->]` are parse errors.
- Edges have no first-class `.source` / `.target` accessor. Use tandem
  iteration of `[src ->:Type:->]` (targets) and `[edge src ->:Type:->]`
  (edges); lists are index-aligned at runtime.
- Edge mutation persists without `save()` / `commit()` inside a `with entry`
  block.
- Spatial assign comprehension: `[edge src -->][?:Road](=distance=X)` —
  bulk-mutation idiom.
- Walkers do **not** auto-dedupe visited nodes. A bare `visit [-->]` on a
  cycle loops indefinitely. Solutions need `has visited: set[str] = set();`
  keyed on `jid(here)`.
- Generic `can ... with entry` (no type) only fires at the spawn location.
  Typed-node-entry abilities are needed for the walker to continue.
- `<node> spawn <Walker>()` returns the walker instance with accumulated
  state. Read `has`-fields off the returned value.
- Type filters are capitalized: `with Root entry`, `with Foo entry`.
  Never lowercase `root` or `foo`.
- `here` is **not** valid inside node-side abilities. Use `self` for the
  node, `visitor` for the walker. `with <Type> entry` polarity flips
  between walker-side and node-side contexts.
- `visit [-->]` works from inside a node-side ability (undocumented but
  runtime-valid).
- Bare `root` is deprecated; use `root()`.
- Jac persists root-level graph state across `jac run` / `jac test`
  invocations via `.jac*` / `jac.lock` files. Tests that attach to `root`
  leak across runs; orchestrator isolates each generation in a temp dir.
- `#` line comments and `#* *#` block comments. NOT `//` or `/* */`.
- **No `let` keyword**. Locals are bare assignments; module globals use
  `glob`. Rust/TypeScript intuition fails here.

Several of these are concrete doc-vs-runtime discrepancies in `jac://docs`
that would probably merit upstreaming to `jac-llmdocs`.

---

## Reproducing

Prereqs: Python 3.12, `jac` CLI installed, API keys for Anthropic / Google /
Groq in `.env`.

```bash
git clone https://github.com/drPod/jaceval.git
cd jaceval
python -m venv .venv && .venv/bin/pip install -e .
cp .env.example .env    # fill in ANTHROPIC_API_KEY, GOOGLE_API_KEY, GROQ_API_KEY

# Build the mini plan (120 entries)
.venv/bin/python -m harness.run --build-plan \
    --plan .eval_cache/mini_plan.jsonl \
    --arms no-skill llmdocs v0-skill irrelevant-ctrl \
    --models meta-llama/llama-4-scout-17b-16e-instruct \
    --tasks 01 02 03 04 05 06 07 08 09 10 \
    --n-samples 3

# Phase 1: generator + tests + AST (fast, no judge calls)
.venv/bin/python -m harness.run \
    --plan .eval_cache/mini_plan.jsonl \
    --out .eval_cache/mini_results.jsonl \
    --skip-judge

# Phase 2 (after judge-provider quota reset): fill in idiomaticity
.venv/bin/python -m harness.run \
    --out .eval_cache/mini_results.jsonl \
    --judge-only

# Analyze the 5 cuts
.venv/bin/python scripts/analyze_mini.py \
    --results .eval_cache/mini_results.jsonl \
    --out results/mini/summary.json
```

All calls in the above are free-tier if you respect Gemini's daily cap (20
req/day) and Groq's daily TPD cap (500k on Llama-4-Scout, 200k on
GPT-OSS-120B). If either is exhausted, split the run across days — the
orchestrator is fully resumable (keyed by `(group, arm, model, task_id,
sample_idx)`).

Tests:

```bash
.venv/bin/python -m pytest -q
```

---

## Known limitations (honest)

This is a v0 pilot, not a published benchmark. What the full run needs to
be credible:

1. **Scale to 3 generators × 5 samples** (Claude Haiku + Gemini 3 Flash +
   Llama), paid-tier. Current mini-run is 1 generator × 3 samples.
2. **Add the no-op noise-floor arm** (baseline twice, different seed base).
   Architecturally supported (`--noise-floor` on the plan builder); not run
   in the mini.
3. **Scale tasks from 10 → 40–60** for Miller's paired-A/B power at 10 pp.
   10 is powered only for floor-breaking / large effects.
4. **Expand judge validation corpus from 15 → 30–50 snippets** and add an
   ensemble second judge. Current κ = 0.500 is at the low end of "moderate."
5. **Re-author v0-skill examples** to explicitly avoid type names (`Post`,
   `Road`) used by the eval tasks. The current SKILL.md shares teaching
   archetypes with both the tasks and Jaseci's LLMDocs; the cut-2
   comparison is unaffected, but cut-1 v0-skill-vs-no-skill on walker/09
   and graph/06 should be read with pattern-proximity in mind.
6. **`by llm()` bucket** (Jac's LLM-backed-function primitive) deferred to
   v1. Its evaluation is its own research problem.

Everything above is scope-for-v1, not bugs in v0.

---

## Credit

- Jason Mars / Jaseci Labs — the original invitation on 2026-04-09, the
  `jac-mcp` server this eval anchors on, and the underlying language.
- [MultiPL-E](https://github.com/nuprl/MultiPL-E) (Cassano et al., IEEE TSE
  2023) — the translator-and-runner template every niche-language eval
  should fork.
- Miller, "Adding Error Bars to Evals," arXiv:2411.00640 — paired design
  is where small-N evals recover statistical teeth.
- Kim et al., Prometheus (ICLR 2024) — judge prompt format.
- Pathak et al., "Rubric Is All You Need" (ICER 2025) — per-task rubrics
  beat generic ones.
- Chen et al. (2021), arXiv:2107.03374 — unbiased pass@k.
