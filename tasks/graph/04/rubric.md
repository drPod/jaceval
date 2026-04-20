# Rubric: graph/04 — Directed city graph from road pairs

## Task summary

Define a `City` node archetype with a typed `name: str` field and a `Road`
edge archetype, then implement
`build_city_graph(roads: list[tuple[str, str]]) -> dict[str, City]` that
creates exactly one `City` node per unique city name and uses Jac's
directional connect operator `++>` to record each `(src, dst)` road as a
one-way link from the source node to the destination node. The function
returns a `name -> City` dict so the caller can reach every vertex by
name. This task measures whether the model reaches for Jac's
object-spatial graph primitives (`node`, `edge`, `++>`) rather than
transliterating a Python adjacency-list dict.

## Expected idiomatic constructs

All three are required for full idiomaticity credit:

1. **`node` archetype with typed `has` field** —
   `node City { has name: str; }`. Not `obj City`, not `class City`, not
   a plain dict. See `jac://docs/osp` § Nodes and pattern #5 in
   `jac://guide/patterns` ("Node and Edge Definitions with Graph
   Construction").
2. **`edge` archetype** — `edge Road;` (bare edge form) or
   `edge Road { }`. Declared as a first-class relationship type even
   though it carries no data in this task. See `jac://docs/osp` § Edges
   and pitfall #18 in `jac://guide/pitfalls` ("Edge definitions").
3. **`++>` directional connect operator** — `cities[src] ++> cities[dst]`
   inside the loop that consumes `roads`. Not a manual adjacency-list
   append, not a reverse `<++`, not the bidirectional `<++>` form. See
   `jac://docs/osp` § Graph Construction ("Directed vs Undirected") and
   pitfall #20 in `jac://guide/pitfalls` ("Node connections and
   traversal").

## Level descriptors (1–5)

- **5 — Exemplary.** `node City { has name: str; }`, `edge Road;`
  (or `edge Road { }`), and a `def build_city_graph` that deduplicates
  city names into a dict, creates one `City` per name, and records each
  pair with `++>`. Clean Jac style: braces, semicolons, typed parameters
  and return, tuple unpacking in the `for` loop. Reads like
  `jac://guide/patterns` pattern #5.
- **4 — Strong.** All three constructs present but with a minor style
  blemish — e.g. uses an un-typed `edge Road { }` body where a bare
  `edge Road;` would be cleaner, connects via the more verbose typed
  form `+>:Road:+>` when the bare `++>` is idiomatic for an edge with no
  data, or drops the return-type annotation on `build_city_graph` while
  keeping everything else correct.
- **3 — Mixed.** Solves the task and compiles, but misses one of the
  three core constructs outright — e.g. defines `City` as `obj City`
  instead of `node City`, omits the `Road` edge archetype entirely
  (so `++>` falls back to the default generic edge), or uses `<++` /
  `<++>` where the task asks for a one-way `src -> dst` link.
- **2 — Python-leaking.** Builds the graph as a `dict[str, list[str]]`
  adjacency map (or `dict[str, set[str]]`), or defines `City` as a data
  record and records connections in a sibling dict instead of via `++>`.
  May still satisfy the observable behavior the tests probe, but
  defeats the `node` / `edge` / `++>` measurement this task exists to
  make.
- **1 — Does not compile** under `jac-mcp validate_jac`, OR does not
  solve the task (missing cities, wrong direction, doesn't deduplicate,
  crashes on empty input).

## Penalize explicitly

- **Python-transliterated adjacency map.** Representing the graph as a
  `dict[str, list[str]]` (or `dict[str, list[City]]`) adjacency table
  and writing a Python-style function that manipulates that dict —
  even if the observable behavior is correct — drops to at most 2.
  This is the prototypical Python-transliteration smell for the graph
  bucket; the whole reason graph/04 exists is to catch it.
- **`obj City` instead of `node City`.** Violates the `node` archetype
  requirement from `jac://docs/osp` § Nodes. An `obj` cannot participate
  in `++>` traversal or in edge-expression queries like `[c -->]`.
  Drops to at most 3.
- **Omitting the `Road` edge archetype.** Using `++>` with the default
  generic edge and never declaring `edge Road;` drops to at most 3 —
  the task spec explicitly asks for a named relationship type.
- **Wrong direction or undirected connection.** Using `<++` (reverses
  the connection) or `<++>` (creates edges both ways when the spec
  requires one-way) on a `(src, dst)` pair changes the observable
  reachability and drops to at most 2.
- **Missing deduplication.** Creating a fresh `City(name=s)` for every
  occurrence of `s` across pairs breaks the "exactly one vertex per
  unique name" requirement and drops to 1 (tests will fail).
- **Explicit `self` in any method signature**, `class` instead of
  `node`, or Python-style indentation without braces / semicolons.
  Drops one level from wherever the solution otherwise lands
  (pitfalls #2, #4, #5b in `jac://guide/pitfalls`).
