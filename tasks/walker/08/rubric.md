# Rubric: walker/08 — Search a user graph for a reachable admin, stopping on first match

## Task summary

Define one `node` archetype, `User`, with two typed fields
`name: str` and `is_admin: bool`, and expose one function:

    def has_admin_reachable(start: User) -> bool

that returns `True` iff at least one admin user is reachable from
`start` by following outgoing edges zero or more times (including
`start` itself if `start.is_admin`), and `False` otherwise. The
implementation must stop exploring the graph as soon as the first
admin is found, and must terminate on graphs that contain cycles.

This is the second walker-bucket task. Where walker/07 probed the
vanilla `walker + visit + typed-entry` pattern with exhaustive
traversal, walker/08 probes Jac's **early-termination primitive**:
`disengage`, the keyword that immediately halts a walker mid-
traversal. The idiomatic solution is a walker that checks
`here.is_admin` inside a `can ... with User entry` ability, flips
a `has found: bool` state field to `True` on match, and calls
`disengage;` to abort the remaining queued traversal. The
function body reads `w.found` off the spawned walker instance and
returns it.

A solution that walks every reachable node, sets `found` along the
way, and never calls `disengage` will pass all the functional
tests (cycles included) but misses the construct the task exists
to measure. The rubric penalizes this at Level 3.

Two subtleties inherited from walker/07 that still apply here:

1. **Jac walkers do not auto-dedupe visited nodes.** A bare
   `visit [-->]` on a graph with a cycle `A → B → A` loops
   forever. Confirmed via runtime probe 2026-04-20 (see
   `docs/findings/jac-pitfalls.md` § Walkers). The cycle-no-admin
   test in `tests.jac` will hang without an explicit visited-set
   (`has visited: set[str] = set();` keyed on `jid(here)`).

2. **Walker state is readable on the spawned instance even after
   `disengage`.** Confirmed via runtime probe 2026-04-20: after
   the walker disengages on the admin match, `w.found` holds
   `True` and any other `has`-fields (e.g. `visited`) are
   introspectable. This is what makes the
   `w = start spawn FindAdmin(); return w.found;` idiom work.

## Expected idiomatic constructs

All four are required for full idiomaticity credit:

1. **`node User` archetype** with typed `has name: str;` and
   `has is_admin: bool;` fields. Not `obj`, not `class`, not a
   dict-of-dicts adjacency map. See `jac://docs/osp` § Nodes and
   `jac://guide/patterns` § 4 (Walker Definition and Traversal).

2. **`walker` archetype with `has`-field state** carrying the
   running `found: bool` flag (plus a visited-set for cycle
   handling). The `has_admin_reachable` function must spawn this
   walker and read `w.found` off the returned instance. Flags
   accumulated in a module-level `glob`, in a mutable list
   threaded through the walker, or in `report` + `.reports` list
   inspection are not idiomatic for a single-bool search result.
   See `jac://docs/osp` § Walkers § 2 ("Walker State").

3. **One `can ... with User entry` ability** that fires on
   arrival at each reachable user, checks `here.is_admin`,
   and — critically — calls `disengage;` the instant the check
   succeeds. `visit [-->]` at the end of the non-match branch
   continues traversal. See `jac://docs/osp` § Walkers § 5
   ("The `disengage` Statement") and `jac://docs/tutorial-osp`
   § "Stopping Early with `disengage`".

4. **Explicit `disengage;` on the admin-found branch.** This
   is the core probe of the task. `disengage` immediately
   terminates the walker: already-queued-but-unvisited neighbors
   in the `visit [-->]` queue do NOT fire after disengage.
   Confirmed via runtime probe 2026-04-20 (see Task summary).
   Solutions that use `return` in the admin-found branch halt
   the ability body but leave queued neighbors to keep firing,
   defeating the purpose of the probe. See `jac://docs/osp`
   § Walkers § 5.

**Spawning from the start user.** The function body must spawn
the walker on the given `start` vertex — idiomatically
`w = start spawn FindAdmin(); return w.found;` — not on `root`.
The walker state is read back from the returned walker instance.

## Level descriptors (1–5)

- **5 — Exemplary.** `node User` with typed fields, a
  `walker FindAdmin` (or similar) with `has found: bool = False`
  and `has visited: set[str] = set()` fields, a single
  `can ... with User entry` ability that (a) dedupes on
  `jid(here)`, (b) checks `here.is_admin` and on match sets
  `self.found = True; disengage;`, (c) otherwise calls
  `visit [-->];`, and a `has_admin_reachable` function that
  does `w = start spawn FindAdmin(); return w.found;`. Clean
  Jac style: braces, semicolons, typed fields and return
  annotation.

- **4 — Strong.** All four constructs present but with one minor
  style blemish — e.g. sets `self.found = True` and then uses
  `return;` instead of `disengage;` only because a second
  `visit [-->]` follows outside an `if/else` and the author
  wanted to skip it (still exhausts the walker ability but
  produces the right answer on all test cases); or declares
  `has visited: set = set();` without the `[str]` type
  parameter; or names the found flag `done` / `result` /
  `hit` rather than the semantically clearer `found`.

- **3 — Mixed.** Solves the task and compiles, but misses one
  of the core constructs outright — most commonly:
  - **Exhaustive traversal.** Walker visits every reachable
    user, flips `found = True` somewhere along the way, and
    never calls `disengage`. Functionally correct on all 5
    test cases (dedupe handles the cycle) but entirely misses
    the early-termination primitive the task probes. Capped
    at 3.
  - **`return` in the admin-found branch instead of
    `disengage`.** Halts the current ability body but leaves
    already-queued `visit [-->]` neighbors to continue firing.
    The walker still eventually returns the right answer
    because `self.found` is checked with an early return at
    the top of the ability, but the traversal has already
    exhausted the reachable subgraph. Same semantics as the
    exhaustive-traversal case; capped at 3.
  - Spawns the walker on `root()` and then filters for
    reachability-from-start after the fact, losing the
    per-start scoping the function signature implies. Capped
    at 3.

- **2 — Python-leaking.** Implements the traversal as a manual
  BFS/DFS in a plain `def has_admin_reachable` function,
  using `[-->]` edge queries and a Python-style while-queue
  and visited set, with no `walker` archetype at all. May
  pass observable behavior on these tests but defeats the
  walker-as-mobile-agent + `disengage` measurement this task
  exists to make.

- **1 — Does not compile** under `jac-mcp validate_jac` or via
  `jac test`, OR does not solve the task — most commonly: the
  cycle-no-admin test hangs because the walker has no
  visited-set dedupe; or an import / archetype / syntax error
  prevents tests from running.

## Penalize explicitly

- **No `disengage` — exhaustive traversal.** Walker visits every
  reachable user, sets `found = True` when the admin is seen,
  and never halts. The walker still reads back correctly after
  the traversal completes, so tests pass. But `disengage` is
  the *core* idiomatic construct being probed. A solution
  without it has solved the problem by accident — it does not
  demonstrate knowledge of Jac's search-early-termination
  primitive. Drops to at most 3. See `jac://docs/osp` §
  Walkers § 5 ("The `disengage` Statement").

- **`return` used where `disengage` belongs.** `return` halts
  the current ability body. `disengage` halts the walker.
  Inside a `can ... with User entry` ability, `return` lets
  queued neighbors from the BFS queue keep firing their own
  entry abilities; `disengage` aborts the entire walker
  instance. Runtime probe 2026-04-20 confirmed that on a graph
  where node A's ability queues B and D via `visit [-->]`,
  then B's ability queues C and disengages, C still fires
  (it was queued before the disengage) but D does not. With
  `return` instead, both C and D fire. Drops to at most 3.

- **No walker at all — pure Python-style BFS/DFS with `[-->]`
  edge queries and a manual visited-set in a plain function.**
  The task's primary probe is the walker-as-mobile-agent +
  `disengage` idiom; solving it with a function-level
  traversal bypasses the probe. Drops to at most 2.

- **Walker uses `report` + `.reports` list inspection**
  instead of a `has found: bool` field. The search returns
  a single boolean — a reporting array is overkill and
  obscures the stateful-walker idiom that makes
  `w = start spawn FindAdmin(); return w.found;` readable.
  Drops to at most 3.

- **No cycle handling.** The cycle-no-admin test hangs. The
  solution fails to run. Drops to 1.

- **Spawning from `root` instead of from the given `start`
  user**, then trying to filter for reachable-from-start after
  the fact. The `spawn <node>` syntax in Jac lets the walker
  begin traversal anywhere; using `root` loses the per-start
  scoping the function signature implies. Drops to at most 3.

- **Using `__jac__` or other runtime internals** for node
  identity (e.g. `id(here)` instead of `jid(here)`, or
  `here.__jac__.id`) instead of the public `jid()` accessor.
  Drops one level from wherever the solution otherwise lands.

- **Explicit `self` in method signatures**, Python-style
  indentation without braces / semicolons, `def __init__`
  instead of `def init`, or lowercase `false`/`true` for
  boolean literals (pitfalls #2, #5b, #6, #14 in
  `jac://guide/pitfalls`). Drops one level from wherever the
  solution otherwise lands.
