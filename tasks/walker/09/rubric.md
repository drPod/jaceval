# Rubric: walker/09 — Increment reachable posts via a node-side ability

## Task summary

Define one `node` archetype, `Post`, with two typed fields
`title: str` and `views: int = 0`, and expose one function:

    def increment_views_reachable(start: Post) -> int

that traverses every post reachable from `start` by following
outgoing edges zero or more times (including `start` itself),
increments each reachable post's `views` by exactly `1`, and
returns the number of posts it bumped. The function must
terminate on graphs with cycles and must never increment a post
more than once per call.

This is the third walker-bucket task. Walker/07 probed
walker-side typed entry abilities (`can count_person with Person
entry` on the walker). Walker/08 probed `disengage` for
early-termination. Walker/09 probes Jac's **node-side ability**
construct: the `can ... with <WalkerType> entry` ability
**declared inside the `node` body**, where the behavior of what
to do on arrival lives with the node — not the walker — and the
walker becomes a near-empty mobile-agent carrying only the
cross-node state needed to orchestrate traversal.

The idiomatic solution is:

- A nearly-empty `walker ViewBumper { has visited: set[str] = set(); }`
  carrying only the visited-set so dedupe is shared across nodes.
- A `can tick with ViewBumper entry { ... }` ability **inside
  the `node Post` body** that reads `visitor.visited` to dedupe,
  mutates `self.views`, and issues `visit [-->]` to continue
  traversal.
- A `def increment_views_reachable(start: Post) -> int { w = start
  spawn ViewBumper(); return len(w.visited); }` that spawns from
  the given `start` and reports the bump count via the walker's
  visited-set size.

### Semantics confirmed by jac-mcp / runtime probe

From `jac://docs/osp` § Walkers § 8 "Special References":

| Reference | Valid Context | Description |
|-----------|---------------|-------------|
| `self` | Any method/ability | Current instance (walker, node, object) |
| `here` | Walker ability | Current node the walker is visiting |
| `visitor` | Node ability | The walker that triggered this ability |

And explicitly for node abilities:
> "In node abilities, the type in `with Type entry` refers to
> the *walker* type visiting this node, NOT the node type."

So inside `can tick with ViewBumper entry` on `node Post`:
- `self` = the `Post` instance being visited
- `visitor` = the `ViewBumper` walker that arrived here
- `here` is NOT valid in this context — use `self` for the node

Runtime probe 2026-04-20 on a 3-cycle `A → B → C → A`:
- `visit [-->]` *from inside a node-side ability* correctly queues outgoing
  neighbors and the walker continues traversing.
- Dedupe on `visitor.visited` (walker-owned set) correctly prevents
  re-entry on the cycle. Each of the three posts ended with `views == 1`
  and `w.visited` had 3 entries.

## Expected idiomatic constructs

All three are required for full idiomaticity credit:

1. **`node Post` archetype** with `has title: str;` and
   `has views: int = 0;` fields. Not `obj`, not `class`, not a
   dict-of-dicts. See `jac://docs/osp` § Nodes § 1 (Node
   Declaration).

2. **Node-side entry ability** declared inside the `node Post`
   body: `can <name> with <WalkerType> entry { ... }`. This
   ability is the core construct probed by this task — the
   behavior "on arrival at a Post" lives *with the Post*, not
   with the walker. The mutation on `self.views` and the
   `visit [-->]` call both happen in the node's own body. See
   `jac://docs/osp` § Nodes § 2 ("Node Entry/Exit Abilities"),
   which documents the syntax:
   > `can ability_name with [TypeExpression] (entry | exit) { ... }`
   > where `TypeExpression` is the walker type visiting this node.

3. **Use of `visitor` to access walker state** from inside the
   node-side ability, and **`self` to mutate the node's own
   fields**. This is the node-side dual of the walker-side
   `here`/`self` pattern. See `jac://docs/osp` § Walkers § 8
   ("Special References"). An example from
   `jac://docs/first-app` shows the canonical pattern:
   > `can respond with listtasks entry { visitor.results.append(self); }`

**Spawning from the start post.** The function body must spawn
the walker on the given `start` vertex — idiomatically
`w = start spawn ViewBumper(); return len(w.visited);` — not on
`root`. The walker state is read back from the returned walker
instance.

**Cycle dedupe lives on the walker, not the node.** A visited-set
field on the walker (`has visited: set[str] = set();`) is shared
across all `Post` nodes visited in a single traversal. Putting
the dedupe on the node (e.g. a per-node `has seen_by: set[str];`
keyed on `jid(visitor)`) technically works but creates per-node
state that persists across runs when any `Post` gets attached to
`root` (see `docs/findings/jac-pitfalls.md` § Runtime persistence).
The walker-owned set is the idiomatic location.

## Level descriptors (1–5)

- **5 — Exemplary.** `node Post` with typed `title` and `views`
  fields; a nearly-empty `walker ViewBumper` with
  `has visited: set[str] = set();` as its only state; a single
  node-side ability `can tick with ViewBumper entry` inside
  `node Post` that (a) computes `vid = jid(self)` and early-returns
  if `vid` is in `visitor.visited`, (b) adds `vid` to
  `visitor.visited`, (c) increments `self.views`, (d) calls
  `visit [-->]`; and a `increment_views_reachable` function that
  does `w = start spawn ViewBumper(); return len(w.visited);`.
  Clean Jac style: braces, semicolons, typed fields and return
  annotation.

- **4 — Strong.** All three constructs present (node-side ability,
  `visitor`/`self`, walker archetype) but with one minor blemish —
  e.g. uses `here` instead of `self` inside the node-side ability
  (runtime may tolerate this via an alias, or may not; per the
  docs `here` is specifically reserved for walker abilities); or
  declares the visited set without the `[str]` type parameter; or
  stores the bump count in a separate walker `has count: int = 0`
  field incremented inside the ability instead of returning
  `len(w.visited)` — both work but the latter is slightly less
  DRY; or names the ability something verbose like
  `handle_viewbumper_arrival` rather than a semantically clearer
  name.

- **3 — Mixed.** Solves the task and compiles, but misses the
  core construct outright:
  - **Walker-side ability** (`can bump with Post entry` on the
    *walker*, mutating `here.views` from the walker body)
    instead of a node-side ability. Functionally equivalent and
    tests all pass, but misses the "node-side ability" construct
    this task exists to probe. The `node Post` body carries no
    behavior in this variant — all the logic lives on the
    walker. Capped at 3.
  - **Dedupe on the node, not the walker** (e.g. `node Post
    { has seen: bool = False; ... if self.seen { return; }
    self.seen = True; ... }`). Creates per-node state that can
    leak across runs if the node ever becomes attached to
    `root`, and breaks if the same node appears in multiple
    independent traversals. See `docs/findings/jac-pitfalls.md`
    § Runtime persistence. Capped at 3.
  - Spawns the walker on `root()` and then traverses, mutating
    posts reachable from `root` rather than posts reachable
    from the given `start` argument — loses the per-start
    scoping the function signature implies. Capped at 3.

- **2 — Python-leaking.** Implements the traversal as a manual
  BFS/DFS in a plain `def increment_views_reachable` function,
  using `[-->]` edge queries and a Python-style while-queue and
  visited set, with no `walker` archetype and no node-side
  ability. May pass observable behavior on these tests but
  defeats both the walker-as-mobile-agent idiom AND the
  node-side-ability dispatch this task probes. Or: represents
  the graph as a `dict[str, list[str]]` of post-dicts instead
  of using `node Post` at all. Drops to 2.

- **1 — Does not compile** under `jac-mcp validate_jac` or via
  `jac test`, OR does not solve the task — most commonly: the
  cycle test case infinite-loops because there is no visited-set
  dedupe; or an import / archetype / syntax error prevents tests
  from running; or the ability-body uses `here` in a node
  context where Jac rejects it.

## Penalize explicitly

- **Walker-side ability instead of node-side** (`can bump with
  Post entry` declared on the walker, mutating `here.views`).
  This is the most natural walker-07-pattern extension and will
  pass every test — but it entirely sidesteps the probe. The
  node-side ability is what puts the "on arrival at me, do X"
  behavior *on the node itself*, which is the OSP affordance
  unique to Jac. Drops to at most 3. See
  `jac://docs/osp` § Nodes § 2 ("Node Entry/Exit Abilities")
  and § Walkers § 1 ("Walker Declaration") for the two
  alternatives; this task specifically probes the former.

- **Mutation from outside any walker** (plain function with
  `[start -->]` traversal loops and manual visited-set). No
  walker archetype, no node-side ability. Drops to at most 2.

- **Dedupe on the node, not the walker.** Per-node state leaks
  across runs when nodes are attached to `root`, and breaks
  re-entrant traversals. The visited-set belongs on the walker.
  Drops to at most 3.

- **Python-transliteration** (dict of post-dicts, for-loop
  over a handrolled adjacency list, no Jac OSP constructs).
  The task's primary probe is the node-side ability idiom;
  representing the graph as plain Python containers bypasses
  the entire measurement. Drops to at most 2.

- **Walker uses `report` + `.reports` list inspection**
  instead of returning `len(w.visited)` or reading a `has
  count` field directly. The return value is a single int —
  a reporting array is overkill and obscures the
  stateful-walker idiom. Drops to at most 4.

- **No cycle handling.** The 3-cycle test infinite-loops.
  The solution fails to run. Drops to 1. See
  `docs/findings/jac-pitfalls.md` § Walkers
  ("Walkers do NOT auto-dedupe visited nodes").

- **Spawning from `root` instead of from the given `start`
  post**, then mutating everything reachable from `root`
  rather than just posts reachable from `start`. The
  `spawn <node>` syntax lets the walker begin traversal
  anywhere; using `root` loses the per-start scoping the
  function signature implies. Drops to at most 3.

- **Using `__jac__` or other runtime internals** for node
  identity (e.g. `id(self)` instead of `jid(self)`, or
  `self.__jac__.id`) instead of the public `jid()` accessor.
  Drops one level from wherever the solution otherwise lands.

- **Explicit `self` in method signatures**, Python-style
  indentation without braces / semicolons, `def __init__`
  instead of `def init`, or lowercase `false`/`true` for
  boolean literals (pitfalls #2, #5b, #6, #14 in
  `jac://guide/pitfalls`). Drops one level from wherever the
  solution otherwise lands.
