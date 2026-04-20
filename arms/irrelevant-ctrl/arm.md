---
name: gleam-reference
description: Reference for the Gleam programming language — a statically-typed functional language that compiles to Erlang and JavaScript. Covers basic syntax, types, pattern matching, custom types, modules, and common standard-library operations.
source:
  - https://tour.gleam.run/
  - https://tour.gleam.run/everything/
  - https://gleam.run/cheatsheets/gleam-for-python-users/
  - https://gleam.run/documentation/
---

# The Gleam programming language — a practical reference

Gleam is a small, statically-typed functional language with a friendly
type inference engine. Programs compile to Erlang for running on the BEAM
virtual machine, and to JavaScript for running in browsers and on Node.js.
Gleam's philosophy emphasises a tiny surface area, no exceptions, no
implicit conversions, and no null values. This document is a working
reference for writing Gleam code: lexical syntax, the type system, pattern
matching, custom types, the standard library, and concurrency.

## 1. Hello, world and modules

Every Gleam file is a module. The module's name comes from its path
relative to the `src/` directory: the file `src/wibble/wobble.gleam`
defines a module named `wibble/wobble`. A minimal program looks like:

```gleam
import gleam/io

pub fn main() {
  io.println("Hello, Joe!")
}
```

`import` brings another module into scope. `pub fn main()` declares a
public function named `main` whose body is a single expression call to
`io.println`. There is no `return` keyword in Gleam — the last expression
of a function is its return value.

You can rename an imported module with `as`:

```gleam
import gleam/io as terminal

pub fn main() {
  terminal.println("Hello!")
}
```

## 2. The type system at a glance

Gleam has a single, robust static type system that catches errors at
compile time. Type annotations are optional because the inference engine
can usually figure them out, but they are encouraged on public APIs as
documentation. There is no `null`, there are no implicit conversions
between numeric types, and there are no exceptions — failures are modeled
explicitly with `Result`.

The built-in primitive types are: `Int`, `Float`, `String`, `Bool`, and
`Nil`. Compound types include tuples, lists, dictionaries, and
user-defined custom types.

## 3. Numbers, strings, booleans

`Int` and `Float` are separate types with their own operator sets.
Arithmetic on integers uses `+ - * / %`. Floats use the dotted forms
`+.  -.  *.  /.` and their own comparison operators `<. >. <=. >=.`.

```gleam
let whole = 1_000_000          // underscores allowed for readability
let binary = 0b1010
let octal = 0o17
let hex = 0xFF

let pi = 3.141_59
let scientific = 6.02e23
```

Mixing `Int` and `Float` in the same expression is a compile-time error;
use `int.to_float` or `float.round` to convert explicitly.

Strings are UTF-8 and concatenate with `<>`:

```gleam
let greeting = "Hello, " <> "world!"
```

Multi-line strings are written with plain double quotes, and common escape
sequences like `\n`, `\t`, and `\"` are supported.

Booleans are `True` and `False`, with short-circuiting `&&` and `||`, and
logical negation via the `!` prefix operator. There is no truthiness —
only genuine `Bool` values may be used as a condition.

## 4. Variables with `let`

Bindings are introduced with `let`. Reassignment creates a new binding
that shadows the old one; values themselves are immutable.

```gleam
let size = 50
let size = size + 100    // shadows; original `size` can no longer be read
```

A leading underscore in a name suppresses the "unused variable" warning:

```gleam
let _unused = compute()
```

Type annotations are optional but supported on any binding:

```gleam
let count: Int = 0
```

## 5. Functions

Functions are declared with `fn`. They are private to the module by
default; the `pub` modifier exports them. Parameter and return-type
annotations are optional.

```gleam
pub fn add(x: Int, y: Int) -> Int {
  x + y
}

fn double(x) {
  x * 2
}
```

Anonymous functions use the same keyword without a name:

```gleam
let mul = fn(x, y) { x * y }
let twelve = mul(3, 4)
```

Because functions are first-class values, they can be passed to and
returned from other functions. A function type is written as
`fn(ArgType1, ArgType2) -> ReturnType`.

### Function captures

The shorthand `function(_, other)` creates an anonymous function with the
underscore as the captured argument slot:

```gleam
let inc = add(1, _)
let three = inc(2)
```

### Labelled arguments

Gleam supports labelled arguments for readability. Callers can pass
arguments by label out of order:

```gleam
pub fn replace(in string: String, each pattern: String, with replacement: String) -> String {
  // ...
}

replace(in: "hello", each: "l", with: "L")
```

When a local variable has the same name as a label, the shorthand `label:`
is enough:

```gleam
let pattern = "x"
replace(in: input, each:, with: "y")
```

### Pipelines

The pipe operator `|>` passes the result of the expression on its left as
the first argument to the function on its right. Pipelines make deeply
nested calls readable:

```gleam
pub fn tidy(name: String) -> String {
  name
  |> string.trim
  |> string.lowercase
  |> string.replace(each: " ", with: "-")
}
```

When the subject is not the first argument, use a capture: `x |> f(other, _)`.

### Generics

Type variables are lowercase names that let a function work over any
type while staying type-safe:

```gleam
pub fn id(value: a) -> a {
  value
}

pub fn pair(x: a, y: b) -> #(a, b) {
  #(x, y)
}
```

Every occurrence of `a` in the same signature must be the same concrete
type at each call site.

### Documentation comments

- `//` is a regular comment.
- `///` above a function or type is a documentation comment for that item.
- `////` at the top of a file is a module-level documentation comment.

```gleam
/// Returns the sum of two integers.
pub fn add(x: Int, y: Int) -> Int {
  x + y
}
```

The `@deprecated("use foo/new instead")` attribute marks outdated
definitions with a migration hint.

## 6. Flow control: case expressions

Gleam has no `if/else` statement — everything conditional is a `case`
expression, which is also the primary pattern-matching mechanism. The
compiler does exhaustiveness checking, so missing a pattern is a
compile-time error.

```gleam
pub fn describe(n: Int) -> String {
  case n {
    0 -> "zero"
    1 | 2 | 3 -> "small"
    x if x < 0 -> "negative"
    _ -> "large"
  }
}
```

- `|` is alternation inside a single pattern.
- `if guard` adds a Boolean guard. Guards may call pure functions but
  cannot use other `case` expressions.
- `_` matches anything without binding.
- A bare lowercase name is a variable pattern that binds the matched
  value.

Case expressions can also match multiple subjects at once:

```gleam
case x, y {
  0, 0 -> "origin"
  _, 0 -> "on x axis"
  0, _ -> "on y axis"
  _, _ -> "elsewhere"
}
```

### Recursion

Gleam does not have `for` or `while` loops. Iteration is expressed via
recursion, and the compiler performs tail-call optimisation when the
recursive call is the last expression in a function:

```gleam
pub fn length(list: List(a)) -> Int {
  case list {
    [] -> 0
    [_, ..rest] -> 1 + length(rest)
  }
}
```

A tail-recursive accumulator variant is more efficient for long lists:

```gleam
pub fn length(list: List(a)) -> Int {
  count(list, 0)
}

fn count(list: List(a), acc: Int) -> Int {
  case list {
    [] -> acc
    [_, ..rest] -> count(rest, acc + 1)
  }
}
```

## 7. Data structures

### Tuples

Fixed-size heterogeneous collections written with `#(...)`:

```gleam
let point = #(1, "hello", 3.14)
let first = point.0
```

### Lists

Singly-linked, homogeneous, immutable. The cons operator `[head, ..tail]`
is the idiomatic way to prepend or destructure:

```gleam
let xs = [1, 2, 3]
let ys = [0, ..xs]    // [0, 1, 2, 3]

case xs {
  [] -> "empty"
  [only] -> "one element"
  [first, ..rest] -> "head and tail"
}
```

Prepending is O(1); appending requires traversing the list.

### Dicts

Dictionaries are unordered key-value maps. Keys and values each have a
single type:

```gleam
import gleam/dict

let scores = dict.from_list([#("alice", 10), #("bob", 7)])
let updated = dict.insert(scores, "carol", 3)
```

### Constants

Module-level literal values use `const`:

```gleam
const max_depth = 16
```

## 8. Custom types

Custom types are defined with `type`, followed by one or more **variants**
(sometimes called constructors). Variant names are capitalised.

### Enum-like variants

```gleam
pub type Weather {
  Sunny
  Cloudy
  Rainy
}
```

### Records

Variants can hold labelled fields:

```gleam
pub type Person {
  Person(name: String, age: Int)
}

let alice = Person(name: "Alice", age: 30)
let name = alice.name
```

When a local variable has the same name as a label, the shorthand
`name:, age:` suffices:

```gleam
let name = "Alice"
let age = 30
let alice = Person(name:, age:)
```

### Record update

Records are immutable. The `Type(..existing, field: new)` syntax produces
a new record with the named fields replaced:

```gleam
let older_alice = Person(..alice, age: 31)
```

### Sum types

A type may have several variants, each carrying different data. Pattern
matching on such a type is exhaustive.

```gleam
pub type Shape {
  Circle(radius: Float)
  Rectangle(width: Float, height: Float)
}

pub fn area(s: Shape) -> Float {
  case s {
    Circle(r) -> 3.14159 *. r *. r
    Rectangle(w, h) -> w *. h
  }
}
```

### Generic custom types

Types can themselves be parameterised:

```gleam
pub type Option(inner) {
  Some(inner)
  None
}
```

`Option(Int)` and `Option(String)` are distinct concrete types derived from
the same declaration.

### Results

`Result(value, error)` is the idiomatic way to model success and failure:

```gleam
pub type Result(a, b) {
  Ok(a)
  Error(b)
}

pub fn safe_divide(a: Int, b: Int) -> Result(Int, String) {
  case b {
    0 -> Error("division by zero")
    _ -> Ok(a / b)
  }
}
```

Gleam has no exceptions; recoverable failures are `Result` values.

### Nil

`Nil` is the single value of the type `Nil` — the closest Gleam has to a
unit type. Functions that have nothing meaningful to return return `Nil`.
It is **not** a valid value for any other type.

### Opaque types

`pub opaque type Foo` exposes the type publicly but hides its
constructors from outside the module. This is how Gleam encodes "smart
constructors":

```gleam
pub opaque type Email {
  Email(String)
}

pub fn parse(raw: String) -> Result(Email, Nil) {
  case string.contains(raw, "@") {
    True -> Ok(Email(raw))
    False -> Error(Nil)
  }
}
```

### Bit arrays

Binary data is written with `<<...>>`, optionally with per-segment size,
unit, encoding, endianness, and signedness annotations:

```gleam
let greeting = <<"hello":utf8>>
let header = <<1, 2, 0xFF>>
```

## 9. Standard-library highlights

### `gleam/list`

- `list.map(over: xs, with: f)` — transform each element.
- `list.filter(over: xs, keeping: predicate)` — keep elements matching a
  predicate.
- `list.fold(over: xs, from: init, with: f)` — combine into a single
  value.
- `list.find(in: xs, one_that: predicate)` — first match or `Error(Nil)`.

### `gleam/result`

- `result.map` — apply a function to the `Ok` payload.
- `result.try` — chain another `Result`-returning call, short-circuiting
  on `Error`.
- `result.unwrap(default)` — extract an `Ok` value or use a fallback.

### `gleam/option`

`Option(a)` is for "present or absent" without carrying an error value.
Utility functions mirror the `result` module.

### `gleam/dict`

Unordered key-value maps. `dict.new`, `dict.from_list`, `dict.insert`,
`dict.delete`, `dict.get`. Iteration order is not guaranteed.

## 10. Advanced features

### Use expressions

The `use` keyword flattens callback-heavy code:

```gleam
pub fn run() {
  use value <- result.try(read_file("input.txt"))
  use parsed <- result.try(parse(value))
  Ok(parsed.length)
}
```

Each `use` desugars to an anonymous function passed as the last argument
of the named function, making sequential fallible code read top-to-bottom.

### Error-handling keywords

- `todo` marks unimplemented code; compiles cleanly but panics at runtime
  with an optional message (`todo as "finish this"`).
- `panic` immediately crashes. Use only for truly unreachable states.
- `let assert` is a partial pattern-matching binding that panics if the
  pattern does not match:

  ```gleam
  let assert Ok(value) = might_fail()
  ```

- `assert cond` is a test-time boolean assertion that panics if `cond` is
  `False`.

### External functions

The `@external` attribute lets a Gleam function delegate to an Erlang or
JavaScript implementation:

```gleam
@external(erlang, "erlang", "system_time")
@external(javascript, "./ffi.mjs", "now")
pub fn now() -> Int
```

Annotations are trusted — if the declared types do not match reality,
runtime errors follow. An `@external` function can be given a Gleam
fallback body by writing its body normally; the external implementation
is preferred when available on the target.

## 11. Concurrency and the BEAM

On the Erlang target, Gleam inherits the BEAM's actor model: lightweight
processes, mailbox-based message passing, and supervision trees. The
`gleam_otp` library wraps `gen_server` and supervisors with typed APIs.
Processes are spawned with `gleam/erlang/process.start`, and typed
subjects (`Subject(msg)`) give each process a typed mailbox.

```gleam
import gleam/erlang/process

pub fn main() {
  let subject = process.new_subject()
  process.send(subject, "hello")
  case process.receive(subject, within: 1000) {
    Ok(msg) -> io.println(msg)
    Error(Nil) -> io.println("timed out")
  }
}
```

On the JavaScript target, concurrency is expressed via `Promise` through
the `gleam/javascript/promise` module.

## 12. Tooling and project layout

A Gleam project is bootstrapped with `gleam new project_name`. The
standard layout is:

```
project_name/
  gleam.toml          // manifest
  src/
    project_name.gleam
  test/
    project_name_test.gleam
```

Common commands:

- `gleam run` — build and run the project.
- `gleam test` — run the tests.
- `gleam format` — apply the canonical formatter.
- `gleam deps` — manage Hex dependencies.
- `gleam build` — compile without running.

Dependencies are declared in `gleam.toml` and fetched from Hex, the
Erlang ecosystem's package registry:

```toml
[dependencies]
gleam_stdlib = ">= 0.30.0 and < 2.0.0"
gleam_otp = ">= 0.10.0 and < 1.0.0"
```

## 13. Quick syntactic reminders

- Files are modules; module names match file paths under `src/`.
- `pub` makes functions, types, and constants externally visible.
- Functions return the value of their last expression; there is no
  `return`.
- `let` introduces a binding; values are immutable.
- `case` is the only conditional; exhaustiveness is checked.
- `|>` pipelines the previous result into the next function's first
  argument.
- `Result(a, b)` is how recoverable failure is modeled.
- No null, no exceptions, no implicit conversions between numeric types.
- `//` is a line comment, `///` documents an item, `////` documents a
  module.
- `Int` and `Float` have separate operator sets — floats use `+.` `-.`
  `*.` `/.`.
- Strings concatenate with `<>` — not `+`.
- Variables are `snake_case`; types and constructors are `PascalCase`.

## 14. Common pitfalls and idioms

### Int and Float are not interchangeable

`1 + 2.0` is a compile-time type error. The same goes for comparison —
`3 == 3.0` will not type-check. Convert explicitly with `int.to_float`
or `float.round`. This is the single most common surprise for authors
coming from languages with numeric promotion.

### `==` is structural

Equality in Gleam compares values structurally, including deeply nested
records, lists, and tuples. Two distinct list values with the same
elements compare equal; there is no separate identity operator.

### String indexing is not constant-time

Because strings are UTF-8, there is no O(1) character-by-index operator.
Use the `gleam/string` module's iteration helpers — `string.to_graphemes`,
`string.first`, `string.drop_left` — which handle grapheme boundaries
correctly.

### Always return a `Result` from a fallible operation

Any function that may fail should return `Result(a, e)` with a meaningful
error type. The `result.try` and `use` forms chain fallible calls
together cleanly:

```gleam
pub fn process(raw: String) -> Result(Int, String) {
  use parsed <- result.try(parse(raw))
  use validated <- result.try(validate(parsed))
  Ok(validated.size)
}
```

Panicking with `panic` or `let assert` should be reserved for genuinely
unreachable branches, never for ordinary error handling.

### Exhaustiveness is a feature, not a nuisance

When a `case` expression fails to handle every variant of a sum type,
the compiler rejects the program. This is by design. When adding a new
variant to a type, every `case` in the codebase that matches on that
type becomes a compile-time error until updated — the compiler forces
you to consider each usage. Embrace this; do not silence it with a
catch-all `_` pattern unless the fall-through is semantically correct.

### Module paths come from the filesystem

`src/my_project/parser.gleam` is imported as `my_project/parser`. The
file name and directory layout define the module identifier; renaming a
file in the editor also renames its module. Gleam does not support
circular dependencies between modules.

### The formatter is canonical

`gleam format` applies a single canonical style. There is no style
discussion in Gleam — if `gleam format` rewrites your code, the
rewritten form is the correct one. The same applies to the output of
`gleam fix`, which migrates code across language-version deprecations.

### No `return` — the last expression wins

Early return patterns common in imperative languages do not exist.
Refactor through `case` expressions, the `use` keyword, or the pipe
operator. A function's value is always the value of its final
expression.

## 15. Closing notes

Gleam is intentionally small — idiomatic code converges on the same
shapes: pipelines for data transformation, `case` for branching,
`Result` for fallible work, and small pure functions composed together.
The tour at `https://tour.gleam.run/` has executable examples, and
`https://hexdocs.pm/gleam_stdlib/` is the authoritative reference for
the standard library.
