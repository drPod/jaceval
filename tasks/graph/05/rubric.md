# Rubric: graph/05 — Mutual collaboration graph with typed edges

## Task summary

Define a `Person` node archetype with a typed `name: str` field and a
typed `Collab` edge archetype carrying a `project: str` field, then
implement
`build_collab_graph(collabs: list[tuple[str, str, str]]) -> dict[str, Person]`
that creates exactly one `Person` node per unique name and records each
`(a, b, project)` triple as a single **bidirectional** `Collab` edge
between the two people, with `project` stored on the edge itself. The
function returns a `name -> Person` dict so the caller can reach every
vertex by name. This task measures two complementary OSP affordances
graph/04 did not exercise: (1) **typed edges carrying their own data**
(`has` fields on an `edge` archetype) and (2) the **bidirectional
connect operator `<++>`** (or its typed form `<+: Collab(...) :+>`) for
symmetric relationships.

## Expected idiomatic constructs

All three are required for full idiomaticity credit:

1. **`node` archetype with typed `has` field** —
   `node Person { has name: str; }`. Not `obj Person`, not `class Person`,
   not a plain dict. See `jac://docs/osp` § Nodes and pattern #5 in
   `jac://guide/patterns` ("Node and Edge Definitions with Graph
   Construction").
2. **Typed `edge` archetype with a `has` field** —
   `edge Collab { has project: str; }`. The `project` name lives *on the
   edge*, not on the nodes and not in a side dictionary. See
   `jac://docs/osp` § Edges ("Unlike simple object references, edges can
   carry their own data... Use typed edges when the relationship itself
   has meaningful attributes") and pitfall #18 in
   `jac://guide/pitfalls` ("Edge definitions").
3. **Bidirectional typed connect** —
   `people[a] <+: Collab(project=project) :+> people[b]` inside the loop
   that consumes `collabs`. The `<+: Type(...) :+>` form attaches the
   `Collab` instance at connect time and makes the relationship
   symmetric; `[<-->]` neighbor queries then find the counterpart from
   either endpoint. Not two separate `+>:Collab:+>` calls in both
   directions (duplicates edges and doubles the data), and not a bare
   `<++>` with no `Collab` payload (discards the project data). See
   `jac://docs/osp` § Graph Construction ("Bidirectional typed:
   `alice <+: Colleague(department=\"Engineering\") :+> bob;`") and
   pitfall #20 in `jac://guide/pitfalls` ("Node connections and
   traversal").

## Level descriptors (1–5)

- **5 — Exemplary.** `node Person { has name: str; }`,
  `edge Collab { has project: str; }`, and a `def build_collab_graph`
  that deduplicates names into a dict, creates one `Person` per name,
  and records each triple with a single `<+: Collab(project=project) :+>`
  connection. Clean Jac style: braces, semicolons, typed parameters and
  return, tuple unpacking on the triple in the `for` loop. Reads like
  `jac://guide/patterns` pattern #5.
- **4 — Strong.** All three constructs present but with a minor style
  blemish — e.g. uses the untyped `<++>` form plus a separate mutation
  step to attach the project, writes `for c in collabs` without tuple
  unpacking then indexes `c[0], c[1], c[2]`, or drops the return-type
  annotation on `build_collab_graph` while keeping everything else
  correct.
- **3 — Mixed.** Solves the task and compiles, but misses one of the
  three core constructs outright — e.g. uses `obj Person` instead of
  `node Person`, declares `edge Collab;` as a bare edge and stuffs the
  project onto a node-side dict instead of the edge, or uses
  `+>:Collab(project=...):+>` (directional) once rather than the
  bidirectional `<+: ... :+>` form.
- **2 — Python-leaking.** Represents the graph as a nested
  `dict[str, dict[str, str]]` (name → neighbor-name → project), or
  defines `Person` as a data record and stores collaborations in a
  sibling `dict[tuple[str, str], str]` keyed by pairs. May still
  satisfy some observable behavior but defeats the `node` / typed
  `edge` / `<++>` measurement this task exists to make.
- **1 — Does not compile** under `jac-mcp validate_jac`, OR does not
  solve the task (missing people, wrong or missing project data on the
  edge, doesn't deduplicate, crashes on empty input).

## Penalize explicitly

- **Two directional `+>:Collab(project=...):+>` calls in both directions
  instead of one bidirectional `<+: Collab(project=...) :+>` call.**
  Functionally similar for neighbor queries via `[<-->]`, but creates
  two `Collab` edges per pair, doubles the stored project data, and
  misses the idiomatic symmetric-connect affordance. Drops to at most 3.
- **Bare `edge Collab;` + project name stored on the nodes (or in a
  sibling dict).** Misses the central "data lives on the relationship"
  point of this task — the whole reason graph/05 exists is to exercise
  `has` fields on an `edge` archetype. Drops to at most 2.
- **Python-transliterated `dict[str, dict[str, str]]` adjacency map**
  (name → neighbor-name → project) or equivalent nested-dict
  representation. Correct behavior is possible but bypasses the `node`
  / `edge` archetype measurement. Drops to at most 2.
- **`obj Person` instead of `node Person`.** Violates the `node`
  archetype requirement from `jac://docs/osp` § Nodes. An `obj` cannot
  participate in `<++>` / `<+: :+>` traversal or in edge-expression
  queries like `[edge p <-->]`. Drops to at most 3.
- **Directional `++>` or `+>:Collab(...):+>` used once per pair
  (one-way only).** Breaks symmetric-neighbor semantics — `[b <-->]`
  still works in Jac for a single directed edge, but asymmetric
  traversal (e.g. `[b -->]` from the "target" side returning `a`) will
  not; and the task prose explicitly requires a mutual relationship.
  Drops to at most 3.
- **Missing deduplication.** Creating a fresh `Person(name=s)` for
  every occurrence of `s` across triples breaks the "exactly one vertex
  per unique name" requirement and drops to 1 (tests will fail).
- **Missing `project` assignment at connect time** (e.g.
  `<+: Collab :+>` with no payload, then trying to set the field
  afterwards on a reified edge). Drops to at most 3 — the idiomatic
  form threads the instance into the connect expression.
- **Explicit `self` in any method signature**, `class` instead of
  `node` / `edge`, or Python-style indentation without braces /
  semicolons. Drops one level from wherever the solution otherwise
  lands (pitfalls #2, #4, #5b in `jac://guide/pitfalls`).
