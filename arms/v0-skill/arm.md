---
name: jac-v0-skill
description: Concise, pitfall-driven reference for writing correct, idiomatic Jac. Covers syntax, Object-Spatial Programming (nodes, edges, walkers), and the specific ways Python intuition silently fails in Jac. Use this when authoring any `.jac` file.
---

# Writing correct, idiomatic Jac

Jac is its own language. It compiles to Python bytecode on the server and to
JavaScript on the client, but **its syntax is not Python's** and training-data
intuition silently fails in many places. This document is a field-tested
reference organized so that the rules that trip models most often appear
first. Read top-to-bottom on first use; skim the later sections when you
need to look something up.

## Output format

Unless explicitly asked otherwise, produce **raw Jac source only**. No
Markdown fences, no ``` code blocks, no commentary before or after the code.
The code you emit should be directly writable to a `.jac` file and runnable
with `jac run`.

## 1. Surface syntax — the rules that trip LLMs first

### Braces, not indentation; semicolons terminate statements

Jac uses C-family braces. Every statement ends with a semicolon, including
`return`, `assert`, assignments, and single-expression statements.

```jac
# WRONG — Python-style colons and indentation
def greet(name: str) -> str:
    return f"Hello, {name}!"

# RIGHT — braces + semicolons
def greet(name: str) -> str {
    return f"Hello, {name}!";
}
```

### Comments use `#` and `#* ... *#`, never `//` or `/* */`

```jac
# line comment — correct

#*
block comment — correct
*#

// WRONG — parse error
/* WRONG — also a parse error */
```

C- and JavaScript-style comment delimiters do **not** parse. Always `#` for
a line comment, `#* ... *#` for a block comment.

### No `let` keyword — assignments are bare

Jac does not have a `let` / `var` / `const` keyword for local bindings.
Inside a block, simply assign.

```jac
# WRONG — `let` is not a Jac keyword
with entry {
    let x = 5;
}

# RIGHT
with entry {
    x = 5;
}
```

Module-level globals use `glob`: `glob counter: int = 0;`. Function-local
bindings take no leading keyword.

### Boolean literals are capitalized

```jac
# WRONG
done = false;

# RIGHT
done = False;
```

`True` / `False` / `None` (Python-capitalized), not `true` / `false` / `null`.
Lowercase `true` / `false` may pass a syntax check but fail at runtime.

### `not x`, never `!x`

```jac
if !finished { ... }        # WRONG — `!` does not exist as a Jac operator
if not finished { ... }     # RIGHT
```

### `pass` is not a Jac statement

Python's `pass` has no Jac equivalent as a bare keyword. Use `continue`
inside a loop, or an empty block `{}`, or a comment.

```jac
# WRONG — `pass` is not a Jac keyword
while busy { pass; }

# RIGHT — idiomatic no-op inside a loop body
while busy { continue; }
```

### No ternary `?:` — use `if`-expression form

```jac
# WRONG
x = cond ? "y" : "n";

# RIGHT
x = ("y") if cond else ("n");
```

### Tuple unpacking requires parentheses

```jac
(a, b) = pair();   # RIGHT
a, b = pair();     # WRONG — parse error
```

### f-strings work server-side

```jac
msg = f"count = {n}";   # RIGHT — standard f-string
```

(Client-side `cl{}` blocks are outside v0 scope; do not use f-strings there.)

## 2. Archetypes: `obj`, `node`, `edge`, `walker`

Jac has four archetype keywords. `obj` is a record type; `node` and `edge`
are graph vertices and relationships; `walker` is a traversal agent.

### `obj` — type-annotated records

Fields are declared with `has`. **Type annotations are required.** Methods
use `def`, and there is **no implicit `self` in the parameter list**.

```jac
obj Point {
    has x: float;
    has y: float;
    def distance_to(other: Point) -> float {
        dx = self.x - other.x;
        dy = self.y - other.y;
        return (dx * dx + dy * dy) ** 0.5;
    }
}
```

### Non-default fields come before default fields

Inside the same archetype, every field without a default value must appear
**before** every field with a default value. Mixing order is a parse error.

```jac
# WRONG — default field precedes non-default field
obj User {
    has joined: int = 0;
    has name: str;
}

# RIGHT
obj User {
    has name: str;
    has joined: int = 0;
}
```

### `node` and `edge` — graph primitives

```jac
node Person {
    has name: str;
    has age: int = 0;
}

edge Friend {
    has since: int = 2020;
}
```

### Type filter polarity: type name is capitalized

Event clauses on walkers and nodes take a **type name**, which must be
capitalized.

```jac
can greet with Root entry { ... }     # RIGHT — `Root` is the type
can greet with `root entry { ... }    # WRONG — backticked instance form is not the right place
```

Same rule for user types: `with Person entry`, never `with person entry`.

## 3. Control flow and top-level

### Top-level is declarations only; execution lives in `with entry {}`

Print statements, graph-construction snippets, and any other executable code
at module scope must live inside a `with entry { ... }` block.

```jac
# WRONG — bare executable at top level
print("starting");

# RIGHT
with entry {
    print("starting");
}
```

### Match statements use `case X: stmt;`, not `case X { ... }`

```jac
match value {
    case 1: print("one");
    case 2 | 3: print("two or three");
    case x if x > 5: print(f"big: {x}");
    case _: print("other");
}
```

Wrong forms — both parse errors:

```jac
case 1 { stmt; }          # WRONG
case "hi": { stmt; }      # WRONG — braces not allowed after a case colon
```

If a case needs multiple statements, use `case "hi": if True { stmt1; stmt2; }`
or nest a block by other means — not a braced case body.

### `try ... except`, not `try ... catch`

```jac
try {
    risky();
} except ValueError as e {
    handle(e);
} finally {
    cleanup();
}
```

## 4. Imports

```jac
import os;                            # namespace import
import from math { sqrt, pi }         # selective; note: no semicolon after `}`
import from .sibling { helper }       # relative
import from solution { fib, Item }    # same-directory sibling (module name only)
```

Do **not** write `import:py` or `import:jac` — just `import from`. Do not
comma-separate multiple symbols with the module: `import from math, sqrt` is
a parse error.

A static-analysis warning like `Module 'solution' not found` when your code
actually imports from a sibling file in the same directory is a **known
false positive** — the runtime resolves sibling files correctly.

## 5. Test blocks

```jac
test "describes the test" {
    assert 1 + 1 == 2;
}

test "with a message" {
    assert len(xs) > 0, "list must not be empty";
}
```

No `def`, no function wrapper. Assertions end with a semicolon like every
other statement.

## 6. Graphs: connect, traverse, mutate

### Root handling — always `root()`

```jac
root ++> city;      # WARNING: Bare `root` is deprecated.
root() ++> city;    # RIGHT — use the call form
```

### Untyped connect operators

```jac
a ++> b;       # one directed edge a → b
a <++ b;       # one directed edge b → a
a <++> b;      # see "bidirectional is query-time, not storage" below
a del--> b;    # disconnect
```

### Typed edge connect

```jac
a +>: Friend(since=2020) :+> b;    # typed forward
a <+: Friend() :<+ b;              # typed backward

# WRONG — do not chain an edge between two connect operators
a ++> Edge() ++> b;
```

### CRITICAL: `<++>` is NOT symmetric storage

The bidirectional connect `a <++> b` and its typed form create a **single
directed edge `a → b`** in storage. They do not create two edges, and they
do not create an undirected edge. Symmetry shows up only **at query time**,
via the bidirectional traversal filter `[<-->]`.

```jac
# Build with bidirectional connect
a <++> b;

# Only one direction follows outbound filter
from_a = [a -->];     # returns [b]
from_b = [b -->];     # returns []  — there is no b→a edge in storage

# Bidirectional filter sees the connection symmetrically
either = [a <-->];    # returns [b]
same   = [b <-->];    # returns [a]
```

If a task says "mutual" or "each knows the other," either build **two
directed edges** (`a ++> b; b ++> a;`) or use the bidirectional traversal
filter `[<-->]` to query it.

### Traversal filters

```jac
neighbors = [here -->];                 # untyped outbound
bidir     = [here <-->];                # untyped, either direction
people    = [here -->](?:Person);       # type filter
adults    = [here -->](?:Person, age > 18);   # type + attribute filter
old       = [here -->](?age > 18);      # attribute only
```

Always assign the result of a traversal filter to a variable or use it in an
expression. Never write a bare filter statement.

### Typed-edge traversal filters use single dashes

```jac
# RIGHT
targets = [src ->:Road:->];             # typed outgoing — target nodes
edges   = [edge src ->:Road:->];        # typed outgoing — edge objects
incoming_nodes = [src <-:Road:<-];      # typed incoming — target nodes
incoming_edges = [edge src <-:Road:<-]; # typed incoming — edge objects

# WRONG — all three are parse errors
[edge src -->:Road:->]    # no double-dash with a type
[src <-:Road:->]          # no such bidirectional-typed form
[src <-:Road:-]           # no such incoming-typed form
```

For bidirectional + typed, combine an untyped bidirectional edge filter with
a type refinement:

```jac
edges = [edge src <-->][?:Road];
```

### Edges have no `.source` / `.target` — use index-aligned tandem lists

`e.source`, `e.target`, `e.from_node`, `e.to_node` are **not exposed** at
the Jac level. To find the specific edge from `src` to a named `dst`, pair
up the target-node list and the edge-object list (they are equal-length and
same-order) and walk by index:

```jac
targets = [src ->:Road:->];
edges = [edge src ->:Road:->];
for i in range(len(targets)) {
    if targets[i] == dst {
        edges[i].distance = new_distance;
    }
}
```

### Edge mutation persists without `save()`

Assigning to a `has` field on an edge object retrieved via any filter form
**persists automatically** in the graph store — no `save()` / `commit()` is
needed inside a walker ability or `with entry` block. Re-querying returns
the new value.

### Bulk mutation: spatial assign comprehension

If the same mutation applies to every matching edge, use the one-line form:

```jac
[edge src -->][?:Road](=distance=220.0);
```

Use the index-aligned loop pattern above when only a specific edge should
change; use this bulk form when all matching edges change.

## 7. Walkers and traversal

A walker is an agent that moves through the graph, firing abilities based
on the type of the node it arrives at.

```jac
walker CountPeople {
    has count: int = 0;

    can start with Root entry {
        visit [-->];
    }

    can tally with Person entry {
        self.count += 1;
        visit [-->];
    }
}
```

Spawn returns the walker instance after the traversal runs synchronously:

```jac
w = start spawn CountPeople();
n = w.count;
```

Both spawn directions are valid: `start spawn CountPeople()` and
`CountPeople() spawn start` are equivalent.

### Walkers do NOT auto-dedupe visited nodes

A bare `visit [-->]` on a graph with a cycle `A → B → A` **loops
indefinitely**. Jac does not maintain a visited set for you. This is the
single most load-bearing assumption a Python-minded author brings to the
traversal primitive — and it is wrong.

The idiomatic fix: a visited-set field on the walker keyed on `jid(here)`.

```jac
walker VisitOnce {
    has visited: set[str] = set();
    has total: int = 0;

    can tick with Room entry {
        if jid(here) in self.visited { return; }
        self.visited.add(jid(here));
        self.total += 1;
        visit [-->];
    }
}
```

The pattern scales to multiple node types — declare one typed ability per
type the walker should count, and reuse the same `visited` set across
them all.

### A generic `can ... with entry` only fires at the spawn location

A walker with only `can tick with entry { visit [-->]; }` (no type filter)
runs its ability **once, at the spawn node**, and then stops. To walk a
multi-node graph, define a typed ability — `can <name> with <NodeType> entry`
— for each node type the walker should react to. Include a `with Root entry`
if the walker is spawned from `root()`.

### `visit` queues the next step

`visit [-->]` does not immediately jump to the neighbors — it **queues**
them for the next step. Code following `visit` in the same ability body
continues to execute.

```jac
can tally with Person entry {
    self.count += 1;
    visit [-->];                 # queues out-neighbors
    self.last_visited = here.name;   # runs AFTER the visit queueing, not after the traversal
}
```

Use `disengage` to immediately terminate the walker, and `skip` to skip the
rest of the current node's ability and continue with the next queued node.

### `visit ... else { ... }` for dead ends

```jac
can step with Person entry {
    visit [-->] else { self.dead_ends += 1; }
}
```

## 8. Walker-side vs. node-side abilities — the polarity flip

`with <Type> entry` means two **opposite** things depending on where it is
declared:

| Where declared | `<Type>` means | `here` | `self` | `visitor` |
|---|---|---|---|---|
| inside `walker` | node type the walker is arriving at | the node | the walker | N/A |
| inside `node` | walker type arriving at this node | N/A | the node | the walker |

Walker-side:

```jac
walker Tally {
    has count: int = 0;
    can visit_post with Post entry {
        here.views += 1;     # `here` = the Post node
        self.count += 1;     # `self` = the walker
        visit [-->];
    }
}
```

Node-side:

```jac
node Post {
    has views: int = 0;
    can on_visit with Tally entry {
        self.views += 1;        # `self` = this Post instance
        visitor.count += 1;     # `visitor` = the arriving walker
        visit [-->];            # issuing further traversal on the walker's behalf is allowed
        # `here` is NOT valid inside a node-side ability — would error at runtime
    }
}
```

Inside a node-side ability, `visit [-->]` is valid and continues the
walker's traversal.

## 9. Quick reference — WRONG vs RIGHT cheatsheet

Final pass of the highest-frequency mistakes. Scan before emitting code.

```jac
# Booleans and keywords
true  / false                 # WRONG — lowercase
True  / False                 # RIGHT

!done                         # WRONG — no `!` operator
not done                      # RIGHT

# Comments
// line comment               # WRONG
# line comment                # RIGHT

/* block */                   # WRONG
#* block *#                   # RIGHT

# Control flow
while busy { pass; }          # WRONG — no `pass` keyword
while busy { continue; }      # RIGHT

cond ? a : b                  # WRONG — no ternary
(a) if cond else (b)          # RIGHT

case 1 { stmt; }              # WRONG
case 1: stmt;                 # RIGHT

try {} catch E as e {}        # WRONG
try {} except E as e {}       # RIGHT

# Imports
import from math, sqrt;       # WRONG
import from math { sqrt }     # RIGHT

import:py from os { path }    # WRONG
import from os { path }       # RIGHT

# Archetypes and fields
has joined: int = 0;          # WRONG if an undefaulted field follows
has name: str;                # non-default first
has joined: int = 0;          # default second

# Spawning
node spawn W();               # WRONG — `node` is a keyword
root() spawn W();             # RIGHT
my_var spawn W();             # RIGHT
root spawn W();               # DEPRECATED — prefer `root()`
# (both orderings also work: `W() spawn root()`)

# Connects
a ++> Edge() ++> b;           # WRONG — cannot chain edge between connects
a +>: Edge() :+> b;           # RIGHT

del a --> b;                  # WRONG
a del--> b;                   # RIGHT

# Traversal filters
[-->:E:]                      # WRONG
[->:E:->]                     # RIGHT

[-->:E1:->-->:E2:->]          # WRONG
[->:E1:->->:E2:->]            # RIGHT

(`?Type)                      # WRONG — backtick form
(?:Type)                      # RIGHT

(`?Type:attr>v)               # WRONG
(?:Type, attr > v)            # RIGHT

# Walker entry clause
can act with `root entry      # WRONG
can act with Root entry       # RIGHT

# Result retrieval
result.returns[0]             # WRONG
result.reports[0]             # RIGHT
# (or simply read `has` fields off the spawned walker)

# Testing
test my_test { }              # WRONG
test "my test" { assert x; }  # RIGHT
```

## 10. Meta rule

Never trust training-data Jac. Python intuition silently fails in many
places. When in doubt, prefer the rules in this document over pattern-match
from memory, and prefer explicit type annotations on every `has`,
parameter, and return.
