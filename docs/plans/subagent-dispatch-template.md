# Subagent dispatch template

Canonical boilerplate the controller uses when dispatching an implementer
subagent via the `Agent` tool. Copy, fill in the task-specific blocks at the
top, and keep the shared sections below intact. If a shared section starts
feeling outdated, revise it here — never drift in individual dispatches.

The template enforces three project invariants that subagents must not violate:
1. **Paired A/B purity** — prompts must not leak Jac syntax into arms.
2. **jac-mcp discipline** — every Jac file is round-tripped through `validate_jac`.
3. **Findings + Journal reporting** — subagents surface discoveries so the
   controller can route them into `docs/findings/` and `docs/journal/`.

---

## Prompt template (copy from here)

```
You are implementing **Task N** of jaceval v0: <one-line purpose>.

## Task row

| Task# | id | bucket | what it measures | expected constructs |
|---|---|---|---|---|
| **N** | **<id>** | **<bucket>** | **<measures>** | **<constructs>** |

Target: `/Users/darshpoddar/Coding/jaceval/tasks/<bucket>/<id>/` with 5 files.
`held_out: <true|false>`.

## Context to read first (MUST read before touching code)

1. `/Users/darshpoddar/Coding/jaceval/docs/journal/research-log.md` — current
   scope framing, calibration protocol, budget constraints, any open
   methodology issues. Do not re-derive what is already settled.
2. `/Users/darshpoddar/Coding/jaceval/docs/findings/jac-pitfalls.md` AND
   `~/.claude/projects/-Users-darshpoddar-Coding-jaceval/memory/ref_jac_pitfalls.md`
   — accumulated Jac gotchas. Do not re-discover what is already logged.
3. Existing sibling tasks under `/Users/darshpoddar/Coding/jaceval/tasks/`
   for file-shape templates (prompt/solution/tests/rubric/meta).
4. <any task-specific files — fill in per dispatch>

## Paired A/B purity — NON-NEGOTIABLE

The `prompt.md` you author is shared across all 4 context arms (`no-skill`,
`llmdocs`, `v0-skill`, `irrelevant-ctrl`). It must **not** teach Jac syntax —
anything Jac-specific in the prompt leaks into the no-skill arm and shrinks
the measurable lift from SKILL.md on exactly the construct this task probes.

Rules:
- Do not name Jac keywords in `prompt.md`: `node`, `edge`, `walker`, `visit`,
  `can`, `here`, `disengage`, `spawn`, `root`, `archetype`, `has`, `obj`,
  `entry`, `++>`, `<++>`, `<-->`, `[-->]`, `:+>`, `<+:`, etc.
- Describe the **problem** in neutral prose (graph, vertex, relationship,
  reachable, outgoing, "mutual" connection). Function/method signatures in the
  prompt are OK — they are problem spec, not language teaching.
- Do **not** add rescue hints if calibration returns 0/n. 0/n is expected for
  Jac with no context and is acceptable per the revised calibration protocol
  in `docs/journal/research-log.md`. Accept, report, commit.

## jac-mcp workflow — MANDATORY per CLAUDE.md

Every Jac file you author or modify is round-tripped through `jac-mcp`'s
`validate_jac` before check-in. Before writing any Jac:

- `mcp__jac-mcp__understand_jac_and_jaseci()`
- `mcp__jac-mcp__get_resource(uri="jac://guide/pitfalls")`
- `mcp__jac-mcp__get_resource(uri="jac://guide/patterns")`
- `mcp__jac-mcp__get_resource(uri="jac://docs/osp")` for graph / walker bucket
- `mcp__jac-mcp__get_resource(uri="jac://docs/cheatsheet")` for syntax
- `mcp__jac-mcp__search_docs(query=...)` when a specific construct is ambiguous

If docs are silent on runtime semantics, write a minimal probe and `jac run`
it. Cite the URI or probe output in your report.

## Calibration — FREE-TIER ONLY

Run:

```
.venv/bin/python scripts/calibrate_task.py tasks/<bucket>/<id>
```

The helper defaults to Gemini 3 Flash + Llama 4 Scout (both free). Do NOT
pass `--include-haiku` — Haiku is paid and is only invoked during the actual
eval run, not calibration. If Gemini returns 429 (daily free-tier cap), use
partial data from Gemini + Llama's full 5. 0/n is acceptable.

## Report format — MANDATORY sections

Your final report MUST include these sections so the controller can route
findings into the right docs. Omitting any of them is an incomplete report.

- **Status:** DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
- **Implementation:** concrete problem chosen + design rationale.
- **Syntax confirmations:** for any Jac construct where the docs were ambiguous
  or runtime behavior differed from prose, cite the `jac://` URI + excerpt
  and/or the `jac run` probe output that confirmed the behavior.
- **Files created:** absolute paths.
- **`validate_jac` state:** solution + tests. Note expected false positives
  (sibling-import warnings, `<Unknown>`-cascade errors) separately from real
  errors.
- **`jac test` output:** 5/5 confirmation or failure detail.
- **Calibration:** per-model rates + aggregate. Note 429s.
- **Commit SHA:** from your `git commit`.
- **Self-review:** A/B purity (did you leak any Jac keyword into the prompt?),
  mcp discipline (did every Jac file validate before commit?), discipline
  (no rescue hints, no emojis).
- **Findings:** NEW Jac pitfalls you discovered. For each: the wrong form,
  the correct form, the source (URI + excerpt or runtime probe). Empty
  section = no new pitfalls. **Do not silently drop findings** — the
  controller needs them to route into `docs/findings/jac-pitfalls.md` and
  session memory.
- **Journal:** methodology or process issues you encountered (calibration
  oddities, budget surprises, scope pressures, doc-vs-runtime discrepancies
  that aren't language pitfalls but affect how the eval runs). Empty section
  = nothing noteworthy.

Work from `/Users/darshpoddar/Coding/jaceval`.
```

---

## Controller checklist (what the controller does after receiving the report)

1. Read the Status. If BLOCKED or NEEDS_CONTEXT, address before proceeding.
2. Verify the commit landed (`git log --oneline -3`).
3. Route the **Findings** section:
   - Append to `docs/findings/jac-pitfalls.md` with the same section shape as existing entries.
   - Mirror to session memory (`ref_jac_pitfalls.md`).
4. Route the **Journal** section:
   - Append to `docs/journal/research-log.md` with a dated header.
5. Commit the routing as a separate `docs(...)` commit (keeps task commits clean).
6. Mark the task complete in TaskList; dispatch the next task.

If the report has Findings or Journal content and the controller forgets to
route them, that is a bug. Grep your own context for `pitfall`, `gotcha`,
`finding`, `journal` before marking a task complete, as a self-check.
