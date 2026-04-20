# Jac pitfalls discovered during jaceval v0

Running log of concrete Jac syntax and semantics gotchas found while authoring
the v0 task set. This is a **research artifact** — evidence for what a SKILL.md
must cover, and a candidate upstream bug-report list for Jaseci's documentation.
Each entry names the canonical wrong form, the correct form, and — where the
authoritative docs are ambiguous or misleading — the URI of the `jac-mcp`
resource whose prose conflicts with observed runtime behavior.

Mirrored from Claude's session memory (`ref_jac_pitfalls.md`). Both files are
maintained by every subagent authoring Jac in this repo.

---

## Statements and control flow

### `pass` is not a Jac statement

```jac
// INVALID
while True { pass; }

// VALID — idiomatic no-op inside a loop body
while True { continue; }
```

Discovered while writing a timeout-test fixture (Task 4, 2026-04-19). Caught by
`jac-mcp validate_jac`. Python intuition fails here.

---

## Test blocks

Native Jac test syntax — no `def`, no function wrapper:

```jac
test "describes the test" {
    assert expr, "message";
}
```

Assertions require a trailing semicolon (Python-style predicate, Jac-style
statement terminator).

### `jac test` output format (Jac 0.13.5 / jaclang 0.14.0)

- Test summary is written to **stderr**, not stdout.
- Test runner is Python's `unittest` underneath.
- Passing summary (stderr): `Ran N test(s) in T.TTTs\n\nOK`
- Failing summary (stderr): `Ran N tests in T.TTTs\n\nFAILED (failures=N)` plus a per-failure block above it.
- stdout on passing test = `"Passed successfully.\n"`. stdout on failing test = `""`.

Robust parse for pass/fail in Python — combine stdout+stderr and match:

```python
import re
TOTAL   = re.compile(r"Ran\s+(\d+)\s+tests?", re.IGNORECASE)
FAILED  = re.compile(r"FAILED\s*\(failures=(\d+)\)", re.IGNORECASE)
# all_passed ⇔ failures == 0 AND exit_code == 0
```

---

## Object and archetype syntax

- Fields are declared with `has`: `obj Foo { has a: int; has b: int; }` — type annotations required.
- Methods: `def method() -> T { return expr; }` — **no implicit `self`** in the parameter list (unlike Python).

---

## Cross-file imports and `validate_jac` false positives

### Same-directory import form

```jac
import from solution { fib, Item, build_graph }
```

Plain module name. No path. No `.solution` dot prefix.

### The "Module not found" warning is a static-analysis false positive

`validate_jac` runs without working-directory context, so it cannot resolve
sibling files. Any `import from solution { ... }` in a `tests.jac` will emit a
**warning** (not error). This is a false positive — `jac test` and `jac run`
resolve sibling files correctly at runtime. Only `errors[]` entries from
`validate_jac` are blocking; ignore this class of warning.

### Cascade errors in test files

Because the imported symbol is unresolved at static-analysis time, its return
type becomes `<Unknown>`. Downstream uses of the imported function cascade into
false-positive errors like:

> `Cannot assign <Unknown> to parameter 'obj' of type Sized`

These appear wherever the test file passes the imported function's result to a
typed parameter (`len(x)`, etc.). All such errors are non-blocking — the
runtime resolves the real types. Ignore any `<Unknown>`-rooted error in a test
file that imports from a sibling `solution.jac`.

---

## Graph (OSP) semantics: misleading doc vs. runtime

### "Bidirectional" connect is NOT symmetric storage

Both `a <++> b` and `a <+: Type(...) :+> b` create a **single directed edge
`a → b`** at runtime — not two edges, not an undirected edge. The prose in
`jac://docs/osp` § Edges calls `<++>` "creates edges both ways," which is
wrong with respect to storage semantics.

Symmetry at query time comes from **traversal filters**, not from the connect
operator:

- `[a <-->]` returns neighbors reachable via edges incident to `a` in either direction.
- `[a -->]` follows outbound edges only. `[b -->]` where only `a <++> b` exists returns `[]`.

**Consequence.** Any task requiring mutual/symmetric neighbor queries must use
`[<-->]` / `[<--]` filters. The connect operator itself doesn't encode symmetry.

**Doc-bug candidate.** `jac://docs/osp` § Edges should clarify that
bidirectional connect is a **query-time** affordance, not a storage-layer one.

### Typed-edge traversal filter syntax

The typed form is `->:Type:->` (and `<-:Type:<-` for incoming). **Do not mix
with `-->`** — `[edge src -->:Road:->]` is a parse error. The untyped form is
`-->` alone; the typed form drops to `->:Type:->` with single dashes.

Negative cases — all parse errors:

```jac
[edge src -->:Road:->]      // WRONG: double-dash with type
[src <-:Road:->]            // WRONG: no such bidirectional typed form
[src <-:Road:-]             // WRONG: no such incoming typed filter
```

Correct forms:

```jac
[src ->:Road:->]            // typed outgoing target nodes
[edge src ->:Road:->]       // typed outgoing edge objects
[src <-:Road:<-]            // typed incoming target nodes
[edge src <-:Road:<-]       // typed incoming edge objects
[edge src <-->][?:Road]     // bidirectional: untyped edge filter + type refinement
```

### Edges have no first-class `source` / `target` accessor

`e.source`, `e.target`, `e.from_node`, `e.to_node` — none are exposed at the
Jac language level. The idiomatic way to find a specific edge from `src` to a
named `dst` is **index-aligned tandem iteration** of:

- `[src ->:Type:->]` — target nodes
- `[edge src ->:Type:->]` — edge objects

The two lists are equal-length and same-order at runtime. Walk both and pick
by comparing the target node:

```jac
let targets = [src ->:Road:->];
let edges = [edge src ->:Road:->];
for i in range(len(targets)) {
    if targets[i] == dst {
        edges[i].distance = new_distance;
    }
}
```

### Edge mutation persistence

Assigning to a `has` field on an edge object retrieved via any filter form
persists in the graph store. No explicit `save()` / `commit()` needed inside a
`with entry` block or a walker ability. Re-querying with typed or untyped
filters returns the updated value.

### Spatial assign comprehension on edges (bulk-mutation idiom)

```jac
[edge src -->][?:Road](=distance=220.0)
```

mutates **all matching edges** in place. Companion to the "filter + index +
assign" loop pattern — use bulk form when the mutation applies to every
matching edge; use the loop pattern when only one specific edge should change.

---

## Walkers and traversal

### Walkers do NOT auto-dedupe visited nodes

A bare `visit [-->]` inside a walker entry ability on a graph with a cycle (`A → B → A`) loops indefinitely — Jac does not maintain a visited set for you. Confirmed via runtime probe 2026-04-20; `jac://docs/osp` § Walkers makes no claim of automatic dedupe, despite being the single most load-bearing assumption a Python-minded author brings to the traversal primitive.

The idiomatic fix is a visited-set field on the walker, keyed on `jid(here)`:

```jac
walker CountByType {
    has visited: set[str] = set();
    has person_count: int = 0;

    can count_person with Person entry {
        if jid(here) in self.visited { return; }
        self.visited.add(jid(here));
        self.person_count += 1;
        visit [-->];
    }
    // ... repeated per NodeType ability
}
```

**Doc-bug candidate.** `jac://docs/osp` § Walkers should explicitly call out that `visit` semantics are "traverse again each time" and that the author is responsible for dedupe.

### Generic `can ... with entry` only fires at the spawn location

A walker with only `can tick with entry { visit [-->]; }` and no typed-node-entry ability fires the ability once at the spawn node and **does not continue traversing**. To walk the graph and fire per node, the walker needs a `can <name> with <NodeType> entry { ... visit [-->]; }` for each type it should react to (and a `with Root entry` if spawned from `root`).

### `start spawn Walker()` returns the walker instance with accumulated state

```jac
w = start spawn CountByType();   // traversal runs synchronously
return (w.person_count, w.org_count);
```

Read `has`-fields directly off the returned value. No `.reports` needed for simple state-collection cases. Spawn form is `<node> spawn <WalkerType>(<init_args>)`.

### Capitalization: `with Root entry`, not `with root entry`

In walker entry abilities, the type filter takes a **type name** — capitalized `Root` is the type; lowercase `root` is the global instance and would need backtick escaping to appear as a type filter (which is not the intended form). Mirror the same rule for any user-defined `node Foo` — use `with Foo entry`, never `with foo entry`.

---

## Runtime / filesystem

### `here` is not valid in node-side abilities — use `self`

Walker-side ability (author is on the walker, arriving at a node of type `Post`):

```jac
walker Tally {
    has count: int = 0;
    can visit_post with Post entry {
        here.views += 1;      // `here` = the Post node
        self.count += 1;      // `self` = the walker
        visit [-->];
    }
}
```

Node-side ability (author is on the node, being visited by a walker of type `Tally`):

```jac
node Post {
    has views: int = 0;
    can on_visit with Tally entry {
        self.views += 1;      // `self` = the Post node (this instance)
        visitor.count += 1;   // `visitor` = the arriving walker
        visit [-->];          // issue further traversal on the walker's behalf
        // `here` is NOT valid here — would error at runtime
    }
}
```

Confirmed via `jac://docs/osp` § Walkers § 8 ("Special References") — the reference matrix explicitly lists `here=N/A` for node abilities. Since `here` is idiomatic in walker-side abilities, Python-minded authors (and LLMs trained on walker-side examples) will reach for it inside a node-side ability and hit a runtime error.

### The `with <Type> entry` clause is context-polarized

Same syntactic form means two different things depending on where it's declared:

| Where declared | `<Type>` means | `here` | `self` | `visitor` |
|---|---|---|---|---|
| inside `walker` | node type the walker is arriving at | the node | the walker | N/A |
| inside `node` | walker type arriving at this node | N/A | the node | the walker |

The type name after `with` has **opposite polarity** between the two contexts. `jac://docs/osp` § Nodes § 2 notes the distinction but it's easy to miss:

> "In node abilities, the type expression after `with` refers to the *walker* type visiting this node, NOT the node type."

**Doc-bug candidate.** The polarity flip deserves a prominent side-by-side example in `jac://docs/osp` — the current presentation treats the two contexts separately and the symmetry/asymmetry isn't obvious from a single reading.

### `visit [-->]` from inside a node-side ability

Not documented explicitly in `jac://docs/osp` § Walkers (which shows `visit` only in walker-side ability examples), but **runtime-verified to work**. The node-side ability, once triggered, can queue the walker's next traversal steps on the walker's behalf. This is the mechanism that lets "behavior on arrival at this node type" live fully on the node archetype rather than being forced onto the walker.

Probe-confirmed 2026-04-20 on a 3-cycle `A → B → C → A` with node-side `can tick with W entry { self.views += 1; visit [-->]; }`: traversal proceeds through all three nodes exactly once (walker-side visited-set dedupe applied). Doc-coverage gap — worth flagging upstream.

### `jac run` and `jac test` persist root-level graph state across runs

Jac writes lock and cache files (`.jac*`, `jac.lock`, `__jac_gen__/`) in the current working directory and **persists graph state attached to `root` across runs**. Entry-block probes that do `root ++> some_node;` will accumulate nodes run over run, producing misleading visit counts on the second run onward.

**For probes**: clear state between runs:

```bash
rm -rf .jac* jac.lock __jac_gen__ && jac run probe.jac
```

**For `tests.jac`**: each test block creates disconnected nodes that aren't touched to `root`, so persistence isn't an issue — but any test that intentionally uses `root` will leak state into the next test. The harness orchestrator (Task 39) must treat each generation as running in a fresh cwd or clean these files between runs.

---

## No `let` keyword — assignments are bare

```jac
# WRONG — parse error, "Missing ';'" at the '=' plus "Name 'let' may be undefined"
with entry {
    let x = 5;
    print(x);
}

# RIGHT — local bindings are bare assignments
with entry {
    x = 5;
    print(x);
}

# Module-scope globals use `glob`, not `let`:
glob counter: int = 0;
```

Rust and TypeScript/JavaScript both use `let` heavily for local bindings, so
training-data intuition reaches for it. Jac has none — locals are plain
assignments, module globals are `glob`. Confirmed 2026-04-20 by
`validate_jac` during v0-skill authoring (the pitfall was discovered by
writing the teaching doc, not by running the eval — arm authorship is itself a
discovery method).

---

## Comment syntax

### Bare `root` is deprecated — use `root()`

```jac
root ++> node;     # WARNING (deprecated): Bare 'root' is deprecated. Use 'root()' instead.
root() ++> node;   # current idiomatic form
```

`validate_jac` emits this as a warning rather than an error (non-blocking at runtime), but the deprecation is explicit. Prefer `root()` in all authored solutions.

### Jac uses `#` line comments and `#* ... *#` block comments — NOT `//` or `/* */`

```jac
# line comment — correct

#*
block comment — correct
*#

// WRONG — parse error
/* WRONG — parse error */
```

Several LLM-generated Jac samples reach for C/JavaScript-style comments (`//`, `/* */`) and fail to parse. This project's own implementation plan (pre-Phase-6) inherited the same error, documented `strip_comments` with `//` and `/* */` regexes, and had to be corrected during detector authoring (2026-04-20). Confirmed via `validate_jac`: `#` / `#* *#` are the only valid forms.

---

## Meta rule

Never trust training-data Jac syntax. Python intuition silently fails in many
places. Always round-trip through `jac-mcp`'s `validate_jac` before committing
any Jac snippet. For semantics-level questions the docs don't clarify, run a
minimal probe with `jac run` and verify observed behavior. Cite specific
`jac://guide/pitfalls` or `jac://guide/patterns` URIs when documenting a rule;
cite runtime probe output when documenting a doc-vs-runtime discrepancy.
