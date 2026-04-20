# Rubric: walker/07 — Count reachable vertices by type with a walker

## Task summary

Define two `node` archetypes, `Person` and `Organization`, each with a typed
`name: str` field, and expose one function:

    def count_by_type(start: Person | Organization) -> tuple[int, int]

that returns `(num_persons, num_orgs)` reachable from `start` via outgoing
edges, including `start` itself, counting each reachable vertex exactly
once even in the presence of cycles or multiple paths.

This is the first walker-bucket task. It measures Jac's distinctive
**mobile-agent traversal idiom**: a `walker` archetype with `has`-field
state, one `can ... with <NodeType> entry` ability per node type that
fires on arrival, and `visit [-->]` to queue outgoing neighbours for
further traversal. A Python-style manual BFS/DFS using `[-->]` edge
queries from outside any walker solves the task but misses the
OSP affordance the task exists to probe.

One subtlety to grade carefully: Jac walkers **do not auto-dedupe
visited nodes**. A bare `visit [-->]` on a graph with a cycle
`A → B → A` loops forever (confirmed via runtime probe 2026-04-20;
see also `jac://docs/osp` § Walkers, which makes no claim about
automatic visited-set tracking). A correct solution must track
visited node IDs itself — e.g. a `has visited: set[str] = set();`
field on the walker, keyed on `jid(here)`, with an early return
inside each ability when the id is already in the set. A solution
that omits cycle handling and passes only the acyclic tests but
infinite-loops on the cycle test is incorrect at level 1.

## Expected idiomatic constructs

All four are required for full idiomaticity credit:

1. **`node Person` and `node Organization` archetypes** with typed
   `has name: str` fields. Not `obj`, not `class`, not a dict-of-dicts
   adjacency map. See `jac://docs/osp` § Nodes and
   `jac://guide/patterns` § 4 (Walker Definition and Traversal).

2. **`walker` archetype with `has`-field state.** The counts must
   accumulate on the walker itself (`has person_count: int = 0;`,
   `has org_count: int = 0;`), so that `start spawn CountByType()`
   returns the populated walker and the function can read the counts
   off its fields. Counts accumulated in a module-level `glob` or in
   a mutable list threaded through the walker are not idiomatic.
   See `jac://docs/osp` § Walkers ("Walker State").

3. **Two typed `can ... with <NodeType> entry` abilities**, one
   firing on `Person` arrival and one on `Organization` arrival,
   with `visit [-->]` at the end of each to continue traversal.
   This is the type-dispatched node-entry ability — Jac's analog
   to OOP polymorphic dispatch, but on the walker's current
   location rather than on the walker itself. See
   `jac://docs/osp` § Walkers ("Walker Declaration"), pitfall #17
   in `jac://guide/pitfalls` ("Walker definition and visit syntax"),
   and the "Aggregate Walker" example in `jac://docs/osp` §
   Common Walker Patterns.

4. **Explicit cycle handling via a `has visited: set[...] = set();`
   field**, checked and updated at the top of each entry ability
   before incrementing the count. `jid(here)` is the canonical
   node-id accessor for the dedupe key. The cycle test case in
   `tests.jac` infinite-loops without this.

**Spawning from the start node.** The function body must spawn the
walker on the given `start` vertex — idiomatically
`w = start spawn CountByType(); return (w.person_count, w.org_count);`
— not on `root`. The walker state is read back from the returned
walker instance.

## Level descriptors (1–5)

- **5 — Exemplary.** `node Person` / `node Organization`, a
  `walker CountByType` with `has person_count`, `has org_count`, and
  `has visited` fields, two typed `can ... with <NodeType> entry`
  abilities that dedupe on `jid(here)`, increment the matching
  counter, and `visit [-->]`, and a `count_by_type` function that
  does `w = start spawn CountByType()` and returns
  `(w.person_count, w.org_count)`. Clean Jac style: braces,
  semicolons, typed fields and return annotations.

- **4 — Strong.** All four constructs present but with one minor
  style blemish — e.g. uses a single `can tick with entry { ... }`
  ability with an `isinstance`-style `if type(here) == Person`
  branch inside instead of two typed `with <NodeType> entry`
  abilities (works, but flattens the type-dispatch idiom), or
  keeps counts in a dict keyed by type-name string, or uses
  `set()` without a type parameter on `has visited`.

- **3 — Mixed.** Solves the task and compiles, but misses one of
  the core constructs outright — e.g. spawns two separate walkers
  (one to count persons, one to count organizations) instead of a
  single walker that handles both types, or uses a generic
  `can tick with entry` ability with `->Person{...} ->Organization{...}`
  typed context blocks but no type-dispatched abilities, or
  accumulates counts via `report` and reads them back from
  `.reports` instead of off the walker's fields.

- **2 — Python-leaking.** Implements the traversal as a manual
  BFS/DFS in a plain `def count_by_type` function, using `[-->]`
  queries and a Python-style while-queue and visited set, with no
  `walker` archetype at all. May pass observable behavior on these
  tests but defeats the walker-traversal measurement this task
  exists to make.

- **1 — Does not compile** under `jac-mcp validate_jac` or via
  `jac test`, OR does not solve the task — most commonly: the
  cycle test case infinite-loops because the walker has no
  visited-set dedupe.

## Penalize explicitly

- **No walker at all — pure Python-style BFS/DFS with `[-->]`
  edge queries and a manual visited-set tracked outside any walker.**
  The task's primary probe is the walker-as-mobile-agent idiom;
  solving it with a function-level traversal bypasses the probe.
  Drops to at most 2.

- **Walker present but no `can ... with <NodeType> entry`
  ability — e.g. a single generic `can tick with entry` that
  inspects `here` with Python-style `type(here) == Person`
  branching.** Misses the type-dispatched entry ability, which is
  the cleanest expression of Jac's OSP polymorphism. Drops to at
  most 3.

- **Walker with `visit` but counts accumulated via module-level
  `glob` variable, a mutable list passed in, or `report` +
  `.reports` list inspection** instead of `has`-field accumulation
  on the walker itself. Misses the stateful-walker idiom that
  makes `w = start spawn Walker(); w.field` readable. Drops to
  at most 3.

- **Two separate walkers, one per type** (e.g. spawn
  `CountPersons()` then `CountOrgs()`, sum the results) instead
  of a single walker that visits both node types in one
  traversal. Doubles the graph work and misses the multi-ability
  walker idiom. Drops to at most 3.

- **No cycle handling.** The cycle test case infinite-loops.
  The solution fails to run. Drops to 1.

- **Spawning from `root` instead of from the given `start`
  vertex**, then trying to filter for reachable-from-start after
  the fact. The `spawn <node>` syntax in Jac lets the walker
  begin traversal anywhere; using `root` loses the per-start
  scoping the function signature implies. Drops to at most 3.

- **Using `__jac__` or other runtime internals** for node
  identity (e.g. `id(here)` instead of `jid(here)`, or
  `here.__jac__.id`) instead of the public `jid()` accessor.
  Drops one level from wherever the solution otherwise lands.

- **Explicit `self` in method signatures**, Python-style
  indentation without braces / semicolons, or `def __init__`
  instead of `def init`. Pitfalls #2, #5b, #6 in
  `jac://guide/pitfalls`. Drops one level from wherever the
  solution otherwise lands.
