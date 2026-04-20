# Rubric: walker/10 — Sum distances along a chain of roads with an aggregating walker

## Task summary

Define a `node City` archetype with `has name: str;`, an
`edge Road` archetype with `has distance: float;`, and expose one
function:

    def total_distance(start: City) -> float

that walks along the outgoing chain of `Road` edges starting at
`start`, sums each road's `distance` into a running total, and
returns the total. Each road contributes its `distance` exactly
once even when the graph contains a back-link into an earlier
city.

This is the fourth and final walker-bucket task. Walker/07
probed walker-side type-dispatched abilities; walker/08 probed
early termination via `disengage`; walker/09 probed node-side
abilities. Walker/10 probes the **aggregating walker**: a walker
that carries a running scalar in a typed `has` field, accumulates
it across a traversal, and returns the accumulator via
`start spawn Walker()` + field-read on the returned instance.
It is the "sum along a path" idiom — the walker's most common
real-world shape in reporting and analytics code.

The idiomatic solution is:

- A `walker PathSum` with two typed `has`-field states: a
  `total: float = 0.0` accumulator and a `visited: set[str] =
  set()` for cycle safety.
- One `can tick with City entry` ability that: (a) dedupes on
  `jid(here)` to prevent infinite loops on back-links, (b) reads
  the outgoing `Road` edges via `[edge here ->:Road:->]` (the
  typed-edge traversal filter that returns edge objects rather
  than target nodes), (c) sums each edge's `distance` into
  `self.total`, (d) calls `visit [-->]` to continue along the
  chain.
- A function body `w = start spawn PathSum(); return w.total;`
  that spawns from the given start city and reports back the
  accumulator.

### Semantics confirmed by jac-mcp / runtime probe

Probe run 2026-04-20 on the 3-cycle `A → B → C → A` with edge
distances `5.0, 7.0, 3.0`:

- Visit order: A (sum += 5.0), B (sum += 7.0), C (sum += 3.0,
  attempts to visit A, dedupe kicks in at A's ability, return).
- Final `w.total = 15.0` — the back-edge's distance IS summed
  (it is incident on C's outgoing list, read before the walker
  tries to re-enter A), but the walker terminates because A's
  ability early-returns on the duplicate `jid(here)`.
- This is the deterministic "each road counted once" semantics:
  three edges, three distances, three additions.

On the static-analysis side, `validate_jac` flags
`self.total += e.distance;` as `<Unknown> to float` unless the
edge list is annotated: `roads: list[Road] = [edge here
->:Road:->];`. The annotation is not a runtime requirement —
it is a concession to the type-checker's inability to infer
the element type of a typed-edge comprehension. Solutions that
omit the annotation but pass `jac test` should not be
penalized for the static-analysis gap; solutions that fail
both should be (level 1).

## Expected idiomatic constructs

All four are required for full idiomaticity credit:

1. **`node City` and `edge Road` archetypes** with typed
   `has` fields. Not `obj`, not `class`, not a dict-of-
   tuples adjacency map with distances as dict values. The
   `edge Road { has distance: float; }` form is the
   task-specific probe — distances must be first-class
   edge data, not sidecar lookup tables. See
   `jac://docs/osp` § Edges and `jac://guide/patterns` § 4.

2. **`walker` archetype with typed `has`-field state** for
   the accumulator: `has total: float = 0.0;` (plus a
   visited-set for cycle safety). The total must accumulate
   on the walker itself, so that
   `w = start spawn PathSum(); return w.total;` returns
   the populated walker and the function reads the total
   off its field. Accumulation in a module-level `glob`, a
   mutable list threaded through as a parameter, or
   `report` + `.reports` list inspection is not idiomatic
   for a single scalar return. See `jac://docs/osp` §
   Walkers ("Walker State") and `jac://guide/patterns` § 4.

3. **One `can ... with City entry` ability** that fires on
   arrival at each reachable city and issues
   `visit [-->]` to continue along the chain. This is the
   walker-side type-dispatched entry ability — Jac's
   mechanism for "do X on arrival at any City". See
   `jac://docs/osp` § Walkers § 1 ("Walker Declaration")
   and pitfall #17 in `jac://guide/pitfalls`.

4. **Edge-data reads via typed edge filter**:
   `[edge here ->:Road:->]` to get the list of outgoing
   `Road` edge objects, then iterate and sum each `.distance`.
   This is the canonical way to reach an edge's typed `has`
   fields from a walker ability — the un-`edge`-prefixed
   form `[here ->:Road:->]` returns target *nodes*, not
   edges, and cannot reach `.distance`. See
   `jac://docs/osp` § Edges § "Filter by edge type" and
   `docs/findings/jac-pitfalls.md` § "Typed-edge traversal
   filter syntax".

**Cycle safety.** A bare `visit [-->]` on a graph with a
back-edge to the start loops forever — Jac does not
auto-dedupe visited nodes (`docs/findings/jac-pitfalls.md`
§ Walkers). A correct solution must maintain a
`has visited: set[str] = set();` on the walker and
early-return on duplicate `jid(here)` at the top of the
entry ability.

**Spawning from the start city.** The function body must
spawn the walker on the given `start` vertex —
idiomatically `w = start spawn PathSum(); return w.total;`
— not on `root`. The walker state is read back from the
returned walker instance.

## Level descriptors (1–5)

- **5 — Exemplary.** `node City` with `name: str`,
  `edge Road` with `distance: float`, a
  `walker PathSum` with `has total: float = 0.0` and
  `has visited: set[str] = set()` fields, one
  `can tick with City entry` ability that (a) dedupes on
  `jid(here)`, (b) iterates `[edge here ->:Road:->]` and
  sums `e.distance` into `self.total`, (c) calls
  `visit [-->]`, and a `total_distance` function that
  does `w = start spawn PathSum(); return w.total;`.
  Clean Jac style: braces, semicolons, typed fields and
  return annotation. Optional but tasteful: explicit
  `list[Road]` annotation on the edge-list local
  variable to clear `validate_jac`'s element-type
  inference gap.

- **4 — Strong.** All four constructs present but with
  one minor blemish — e.g. sums the distances via
  `sum(e.distance for e in [edge here ->:Road:->])` in
  one line instead of a loop (idiomatic Python, still
  works in Jac, but obscures the `self.total +=` per-
  edge update); or declares the visited set without
  the `[str]` type parameter; or accumulates into a
  local variable inside the ability and assigns
  `self.total = self.total + local` at the end; or
  names the accumulator `sum` / `acc` / `running`
  rather than the semantically clearer `total`.

- **3 — Mixed.** Solves the task and compiles, but
  misses one of the core constructs outright:
  - **Plain-edge `a ++> b` default edges with distances
    stored somewhere else** (e.g. a parallel
    `dict[(str, str), float]` or on the destination node
    as `here.incoming_dist`). Loses the "distances are
    first-class edge data" probe. Capped at 3.
  - **Walker with `report` + `.reports` list inspection**
    of per-edge distances that the caller then `sum()`s,
    instead of accumulating in a `has total: float` field
    on the walker. Obscures the stateful-walker idiom
    that makes `w = start spawn PathSum(); w.total`
    readable. Capped at 3.
  - Spawns the walker on `root()` and then mutates /
    sums everything reachable from `root` rather than
    from the given `start`, losing the per-start
    scoping the signature implies. Capped at 3.
  - Reads edge distances by walking the target-node
    list `[here ->:Road:->]` and indexing back into a
    sibling adjacency dict keyed by
    `(jid(here), jid(target))` instead of using
    `[edge here ->:Road:->]` directly. Technically
    correct but hand-rolls a lookup for data already on
    the edge object. Capped at 3.

- **2 — Python-leaking.** Implements the traversal as a
  manual while-loop in a plain `def total_distance`
  function: `curr = start; total = 0.0; while curr:
  nexts = [curr -->]; ...`. Represents the graph
  correctly with `node City` / `edge Road` but bypasses
  the walker-as-mobile-agent measurement entirely. Or:
  represents the graph as a
  `dict[str, tuple[str, float]]` chain with no Jac
  OSP constructs at all. Drops to 2.

- **1 — Does not compile** under `jac-mcp validate_jac`
  or via `jac test`, OR does not solve the task — most
  commonly: the cycle test case infinite-loops because
  the walker has no visited-set dedupe; or
  `[here ->:Road:->]` (target nodes) is iterated as if
  it were an edge list and `.distance` access fails at
  runtime; or an import / archetype / syntax error
  prevents tests from running.

## Penalize explicitly

- **No walker at all — pure Python-style loop or BFS
  with `[-->]` edge queries from outside any walker.**
  The task's primary probe is the aggregating walker
  idiom; a function-level traversal bypasses the
  probe entirely even if the graph itself uses
  `node City` / `edge Road`. Drops to at most 2.

- **Walker present but no typed `has` state for the
  accumulator.** Accumulation via a module-level
  `glob`, a mutable list threaded through the walker,
  a `report` + `.reports` list that the caller
  `sum()`s, or an outer closure variable. Misses the
  "typed walker state" construct this task exists to
  probe. Drops to at most 3. See
  `jac://docs/osp` § Walkers ("Walker State").

- **Distances not on the edge — stored on the node,
  in a parallel dict, or passed in as a separate
  argument.** The `edge Road { has distance: float; }`
  form is the task-specific probe. Storing distances
  off the edge loses the first-class-edge-data
  affordance. Drops to at most 3. See
  `jac://docs/osp` § Edges.

- **Reading edges via `[here -->]` adjacency without
  the typed `->:Road:->` filter.** `[here -->]`
  returns *target nodes*, not edges; the edge's
  `distance` field is not reachable through that
  form. Correct access is `[edge here ->:Road:->]`
  (edge objects) — documented in
  `docs/findings/jac-pitfalls.md` § "Typed-edge
  traversal filter syntax". Drops to at most 2 if the
  solution actively hand-rolls an adjacency-dict
  lookup to work around the missing edge access.

- **No cycle handling.** The cycle test case
  infinite-loops. The solution fails to run. Drops
  to 1. See `docs/findings/jac-pitfalls.md` § Walkers
  ("Walkers do NOT auto-dedupe visited nodes").

- **Spawning from `root` instead of from the given
  `start` city**, then summing everything reachable
  from `root`. Loses the per-start scoping. Drops to
  at most 3.

- **Using `__jac__` or other runtime internals** for
  node identity (e.g. `id(here)` instead of
  `jid(here)`, or `here.__jac__.id`) instead of the
  public `jid()` accessor. Drops one level from
  wherever the solution otherwise lands.

- **Explicit `self` in method signatures**, Python-
  style indentation without braces / semicolons,
  `def __init__` instead of `def init`, or lowercase
  `false`/`true` for boolean literals (pitfalls #2,
  #5b, #6, #14 in `jac://guide/pitfalls`). Drops
  one level from wherever the solution otherwise
  lands.
