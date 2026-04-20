# Rubric: graph/06 — Mutate typed-edge distance in place

## Task summary

Define a `City` node archetype with a typed `name: str` field and a typed
`Road` edge archetype carrying a `distance: float` field, then implement
two functions:

    def build_road_graph(roads: list[tuple[str, str, float]]) -> dict[str, City]
    def update_road_distance(cities: dict[str, City], src: str, dst: str, new_distance: float) -> None

`build_road_graph` creates one `City` per unique name and attaches the
`distance` to each directional `Road` edge at connect time.
`update_road_distance` locates the specific `src → dst` `Road` edge in
the existing graph and mutates its `distance` field in place, so any
subsequent read on that edge reflects the new value. This task measures
an OSP affordance not exercised by graph/04 or graph/05: **in-place
mutation of a typed edge's `has` field, using a traversal filter to
select the target edge and direct assignment to its attribute**. The
persistence-across-requeries property (the update sticks in the graph,
not just on a local copy) is the core probe.

## Expected idiomatic constructs

All four are required for full idiomaticity credit:

1. **`node City` + typed `edge Road` with a `has distance: float`
   field.** Not an `obj`, not a `class`, not a plain dict. See
   `jac://docs/osp` § Edges ("Unlike simple object references, edges
   can carry their own data... Use typed edges when the relationship
   itself has meaningful attributes") and pitfall #18 in
   `jac://guide/pitfalls` ("Edge definitions").
2. **Typed-edge connect with payload at construction time.** Inside
   `build_road_graph`, each triple produces exactly one
   `cities[src] +>:Road(distance=distance):+> cities[dst]`. Not a bare
   `++>` plus a separate assignment afterwards, and not two edges for a
   single triple. See `jac://docs/osp` § Graph Construction
   ("`alice +>: Friend(since=2020) :+> bob;`").
3. **Typed-edge traversal filter to access edge objects.** Inside
   `update_road_distance`, use `[edge src_city ->:Road:->]` (or the
   composed form `[edge src_city -->][?:Road]`) to materialise the
   `Road` edge objects reachable from `src_city`. See
   `jac://docs/osp` § Data Spatial Queries ("`edges = [edge -->];` —
   Get edge objects") and the pitfall-log entry on typed-edge filters
   (composed `[edge X -->][?:Type]` form).
4. **Direct field assignment on the edge reference.** Having located
   the correct edge, assign `edge_ref.distance = new_distance`. The
   mutation must persist: tests re-query the edge and expect the new
   value. See `jac://docs/osp` § Common Walker Patterns (CRUD Walker
   Update variant: `here.name = self.new_name;` — the same direct-
   assignment pattern, applied to an edge instead of a node).

Pairing the filter in (3) with a parallel typed-node filter
`[src_city ->:Road:->]` and iterating in tandem (index-aligned) is one
working way to match each edge to its target node; using `__jac__`
internals (e.g. `e.__jac__.target`) is not idiomatic Jac and should
lose a level.

## Level descriptors (1–5)

- **5 — Exemplary.** `node City { has name: str; }`,
  `edge Road { has distance: float; }`, `build_road_graph` deduplicates
  names into a dict and uses
  `cities[src] +>:Road(distance=distance):+> cities[dst]` for each
  triple, `update_road_distance` picks out the correct edge via the
  typed traversal filter and mutates `edge.distance = new_distance`
  directly. Clean Jac style throughout: braces, semicolons, typed
  parameters and returns, tuple unpacking in the build loop.
- **4 — Strong.** All four constructs present but with one minor
  style blemish — e.g. uses `[edge src_city -->][?:Road]` (composed
  form) instead of the inline `[edge src_city ->:Road:->]`, splits the
  connect into an untyped `++>` plus a separate post-connect
  `edge.distance = distance`, or drops the `-> None` return annotation
  on `update_road_distance` while keeping everything else correct.
- **3 — Mixed.** Solves the task and compiles, but misses one of the
  core constructs outright — e.g. maintains a sibling
  `dict[tuple[str, str], float]` alongside the graph and "mutates" by
  updating the dict, implements `update_road_distance` by deleting the
  old edge and spawning a new one instead of assigning to the field,
  or uses `obj City` / `obj Road` with a dict-of-dicts adjacency map.
- **2 — Python-leaking.** Represents the whole graph as a nested
  `dict[str, dict[str, float]]` (no `node`/`edge` archetypes at all)
  and updates via `adj[src][dst] = new_distance`. May pass observable
  behavior on these specific tests but defeats the `node` / typed
  `edge` / edge-mutation measurement this task exists to make.
- **1 — Does not compile** under `jac-mcp validate_jac` or via
  `jac test`, OR does not solve the task (update fails to persist,
  wrong road mutated, crashes on the multi-road cases, or doesn't
  deduplicate city names).

## Penalize explicitly

- **Parallel dict of distances maintained alongside the graph.**
  `distances: dict[tuple[str, str], float]` updated in lockstep with
  the graph, with `update_road_distance` mutating only the dict.
  Misses the entire point of typed edges — the relationship payload
  must live on the `Road` edge, and the update must mutate *that*
  field, not a side-map. Drops to at most 2.
- **Storing `distance` on the `City` node keyed by destination name**
  (`has out_distances: dict[str, float]` on `City`, updated by writing
  to `city.out_distances[dst]`). Same miss as above in a different
  shape — the data belongs on the edge, not the source node. Drops to
  at most 2.
- **Implementing the update by deleting the old `Road` edge and
  spawning a new one with the new distance.** Functionally equivalent
  for these tests but misses the "access-edge-then-assign-attribute"
  affordance this task exists to probe. The CRUD-update pattern in
  `jac://docs/osp` for nodes is `here.field = self.new_value`; the
  same direct-assignment must be applied to the edge. Drops to at
  most 3.
- **Reaching into `__jac__` internals** (e.g. `e.__jac__.target` to
  identify an edge's endpoint) instead of composing a Jac-level
  traversal filter. It works, but it's a runtime-internals leak, not
  a language-level Jac idiom. Drops one level from wherever the
  solution otherwise lands.
- **Mutating inside `build_road_graph` in a second pass** (e.g.
  connect with a placeholder distance, then immediately iterate and
  assign) instead of threading `Road(distance=distance)` into the
  connect expression at construction time. The idiomatic form
  attaches data at connect time. Drops to at most 4.
- **Untyped `++>` with all data stored on the nodes instead of the
  edge.** Violates the typed-edge requirement. Drops to at most 2.
- **Missing deduplication of city names** in `build_road_graph`
  (re-creating a fresh `City` per occurrence of a name across
  triples). Tests build multi-triple graphs and expect shared
  vertices — they will fail. Drops to 1.
- **Using `obj` or `class` instead of `node` / `edge` archetypes.**
  Breaks all of the traversal-filter idioms the task requires. Drops
  to at most 2.
- **Explicit `self` in method signatures**, or Python-style
  indentation without braces / semicolons, or `def __init__` instead
  of `def init`. Pitfalls #2, #5b, #6 in `jac://guide/pitfalls`.
  Drops one level from wherever the solution otherwise lands.
