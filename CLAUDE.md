# Jac / Jaseci Project

## Language

Jac is its own language. It compiles to Python bytecode (server), JavaScript (client), and native binaries. Do not guess syntax from training data.

- Run: `jac run <file.jac>`
- API server: `jac start <file.jac>`
- Tests: `jac test`

## MCP Server (jac-mcp)

Configured in `.mcp.json`. Provides Jac-specific tools, resources, and prompts.

### Required Workflow (from server instructions)

1. Call `understand_jac_and_jaseci` to get the knowledge map
2. Call `get_resource` for `jac://guide/pitfalls` and `jac://guide/patterns` before writing any code
3. Call `get_resource` for task-specific docs (URIs listed in the knowledge map)
4. Write code, then call `validate_jac` to verify it compiles
5. If validation fails, use `explain_error`, fix, and re-validate
6. Do NOT present code to the user until it passes validation

### Tools — Use These

| Tool | Purpose |
|---|---|
| `validate_jac` | Full type-check on code strings. Use before presenting any Jac code. |
| `check_syntax` | Parse-only syntax check (no type checking, faster). |
| `format_jac` | Format Jac code to standard style. |
| `lint_jac` | Style violations and unused symbols. Supports `auto_fix`. |
| `py_to_jac` | Compiler-backed transpile Python to Jac. |
| `jac_to_py` / `jac_to_js` | Compiler-backed transpile Jac to Python or JavaScript. |
| `graph_visualize` | Visualize graph as DOT or JSON from a code string. |
| `get_resource` | Fetch doc/guide by URI (e.g. `jac://guide/pitfalls`). |
| `understand_jac_and_jaseci` | Get the full knowledge map with resource URIs for any task. |
| `search_docs` | Keyword search across Jac docs. Returns ranked snippets with URIs. |
| `list_examples` / `get_example` | Browse and fetch example Jac code by category. |

### Tools — Skip, Use Bash Instead

- `run_jac` — Use `jac run <file.jac>` via Bash. Better for project files, real output.
- `execute_command` / `list_commands` / `get_command` — Thin subprocess wrapper around `jac <cmd>`. Just run `jac` commands directly via Bash.
- `explain_error` — Just 6 regex patterns with canned responses. Claude's own reasoning about compiler errors is better. Read the actual error message instead.
- `get_ast` — Rarely needed. Use only for debugging parser issues.

### Key Resources (via `get_resource`)

| URI | Content |
|---|---|
| `jac://guide/pitfalls` | Common mistakes AI models make with Jac syntax (WRONG vs RIGHT) |
| `jac://guide/patterns` | Idiomatic Jac patterns with complete working examples |
| `jac://guide/understand` | Knowledge map: what Jac/Jaseci are, 3 core paradigms, resource lookup |
| `jac://docs/cheatsheet` | Complete syntax reference |
| `jac://docs/osp` | Object-Spatial Programming: nodes, edges, walkers, CRUD, persistence |
| `jac://docs/foundation` | Full language specification |
| `jac://docs/byllm` | AI/LLM integration (`by llm`, `sem`, structured output, tool calling) |
| `jac://docs/jac-client` | Full-stack frontend: React/JSX client components |
| `jac://docs/jac-scale` | Deployment and scaling |

---

## This Project: `jaceval`

v0 of the first published-quality Jac codegen eval — a paired A/B benchmark measuring whether context documents (SKILL.md, LLMDocs) actually help LLMs write idiomatic Jac, and by how much.

### Provenance

Built in response to an invitation from **Prof. Jason Mars / Jaseci Labs** (2026-04-09) to prototype *"the best .md or skill that makes the model as smart as possible in coding in Jac, and a methodology to evaluate it."* Jason is also the author of the `jac-mcp` server this project builds on. The research direction connects to his broader interest — hinted the same day via [pi.dev](https://pi.dev) — in harnesses for *educating foundation models on niche languages*, which goes beyond any single SKILL.md.

Two deliverables are first-class, not one: a validated evaluation **methodology** and a **SKILL.md** whose quality is measured by that methodology. The SKILL.md is authored *after* the baseline run, targeted at the specific failure modes the baseline reveals, then re-evaluated on the same harness.

### Design foundation

`design-recipe.md` at repo root is the literature review and methodology source (Cassano et al. / MultiPL-E, Miller 2024 / paired analysis, Kim et al. / Prometheus, Pathak 2025 / per-task rubrics, Chen 2021 / unbiased pass@k, and others). The recipe is authoritative; deviations need justification.

### v0 scope

- **10 hand-authored Jac tasks**, stratified 3 syntax/types / 3 graph-construction / 4 walker-traversal. The `by llm()` bucket is deferred (see below).
- **4 context arms**: `no-skill`, Jaseci's canonical `jac-llmdocs.md` (pinned to release v0.12.1), this project's `v0-skill` (SKILL.md), and `irrelevant-ctrl` (a length-matched Gleam SKILL.md as a "more tokens" null). Originally specced as separate LLMDocs-Mini and LLMDocs-Full variants; discovered 2026-04-19 that Jaseci publishes only one canonical artifact, so collapsed to a single `llmdocs` arm.
- **3 generator models**: Claude Haiku 4.5, Gemini 3 Flash Preview (free tier), Llama 4 Scout 17B via Groq (free tier). Choices finalized 2026-04-19 after confirming Gemini 3 *Pro* Preview is not on free tier (429 quota).
- **Judge**: `openai/gpt-oss-120b` via Groq (free tier). Deliberately NOT Anthropic, NOT Google, NOT Meta — so no self-preference bias against any of the three generator families. Single-judge for v0; dual-judge ensemble deferred to v1. 3 runs per snippet, median.
- **Budget ceiling**: ≤ $5 total API spend. Design choices that would push past this are flagged, not assumed.
- **Timeline**: 10–14 days.

### Methodology non-negotiables

1. **Paired A/B design.** Same tasks under every condition, freeze task order, vary only the context arm. Paired-SE reduction is what makes small-N credible.
2. **Execution-based correctness**, LLM-judged idiomaticity — never the reverse. `jac run` in a sandboxed subprocess decides pass/fail.
3. **pass@k with Chen's unbiased estimator** `1 − C(n−c,k)/C(n,k)`. Never `1 − (1−p̂)^k`.
4. **Do not set temperature=0.** Deployment-realistic temp (0.2–0.7), average K samples.
5. **Hybrid idiomaticity score**: deterministic AST detectors (via `jac-mcp`) + Prometheus-format LLM judge. Combine roughly 40% AST / 60% judge.
6. **Judge validation is mandatory.** Target Cohen's κ ≥ 0.4 against labeled snippets before trusting any delta.
7. **Per-task rubrics** beat generic ones.
8. **Explicitly instruct the judge to penalize Python-transliterated patterns** to counteract the perplexity-familiarity bias that would otherwise pull scores toward Python-ish code.
9. **Paired statistics**: McNemar's on binary, paired bootstrap (10k resamples) on ordinal. Bayesian Beta-Binomial or Wilson intervals for small n — never CLT.
10. **Controls**: irrelevant-context arm (non-Jac SKILL.md) + no-op noise floor (baseline twice with different seeds).
11. **Pre-commit the effect-size threshold** before looking at results. Prevents p-hacking.

### Generalization beyond Jac

Design the translator and harness layers so that re-targeting to another niche language (Gleam, Roc, Dylan, etc.) is a matter of filling in a small language-specific module, not rewriting the pipeline. This is a low-cost design choice with high option value: if the work lands, `jaceval` becomes the reference implementation of a harness-for-language-education, not a Jac-only artifact.

### Jac-expertise workflow

Authoring and grading Jac in this project is done by Claude via `jac-mcp`, anchored on Jaseci Labs' own published patterns/pitfalls guides. The workflow at the top of this file is mandatory — never present Jac code that hasn't been round-tripped through `validate_jac`.

When grading idiomaticity, label decisions must cite specific rules from `jac://guide/pitfalls` or `jac://guide/patterns` to be defensible. *"This looks Python-ish"* is not a label; *"this violates pitfall X from jac://guide/pitfalls"* is.

### `by llm()` — why it's deferred to v1

Jac has a language-level primitive for LLM-backed functions. `def summarize(text: str) -> str by llm();` declares a function whose body *is* a prompt to a model: at call time the LLM receives the signature, any `sem` (semantic) annotations, and call context, and produces a typed return value. This generalizes Mars's OOPSLA 2025 MTP paper into the language and is Jac's primary differentiator vs. Python.

Evaluating `by llm()` code is its own research problem: either (a) stub the backing LLM call deterministically — which is a rubric design question on its own, or (b) execute real LLM calls inside the test — which adds cost and introduces second-order variance into correctness measurement. v0 excludes this bucket so that the four-arm × three-model matrix remains fully deterministic in its correctness scoring. v1 is the natural home.

### Writing the README and RESULTS

Write as a peer proposing a research artifact, not as a student submitting homework. Lead with the finding, not the process. Name explicitly what's v0 and what requires scale-up. Assume a technical reader will `git clone` before finishing the README — the quickstart must work on first try using only free-tier credentials.

### Repo layout

- `tasks/<bucket>/<task-id>/` — one directory per task with `prompt.md`, `solution.jac`, `tests.jac`, `rubric.md`.
- `arms/` — the four context documents.
- `harness/` — runner, scorer, orchestration (prefer Inspect AI).
- `detectors/` — AST idiom detectors (prefer `jac-mcp` over rolling our own tree-sitter).
- `judge/` — prompts, validation harness, hand-label corpus.
- `results/` — raw JSONL + `RESULTS.md` writeup.
- `docs/specs/` — design specs.
- `design-recipe.md` — the literature review that underpins this project.
- `docs/research-problems.md` — append-only log of research-process problems encountered during implementation (calibration tensions, methodology trade-offs, prompt-design traps). Record each problem, the decision made, and what to watch for downstream. Consult before making non-obvious methodology calls.
