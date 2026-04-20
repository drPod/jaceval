# Rubric: syntax/02 — Rectangle with area and perimeter methods

## Task summary

Define a `Rectangle` archetype with `width: float` and `height: float`, plus
two methods `area() -> float` and `perimeter() -> float`. Area is
`width * height`; perimeter is `2 * (width + height)`. This task measures
whether the model reaches for Jac's native archetype-with-methods shape
rather than a Python-transliterated class.

## Expected idiomatic constructs

All three are required for full idiomaticity credit:

1. **`obj` archetype** — `obj Rectangle { ... }`, not `class Rectangle`.
   See pitfall #4 in `jac://guide/pitfalls` ("Prefer `obj` over Python-style
   `class`") and pattern #2 in `jac://guide/patterns` ("Archetype (obj) with
   Has Declarations and Abilities").
2. **`has` typed fields inside the archetype** — `has width: float;` and
   `has height: float;` declared at the top of the `obj` body, not
   assigned to `self` inside an `init`. See pitfall #10 in
   `jac://guide/pitfalls` ("Instance variables use `has`, not `self`") and
   pitfall #13 ("Type annotations are important").
3. **Methods declared on the archetype with `def` and no explicit `self`** —
   `def area() -> float { return self.width * self.height; }` inside the
   `obj` body. See pitfall #5 in `jac://guide/pitfalls` ("`def` for regular
   methods, `can` ONLY for event-driven abilities") and pitfall #5b
   ("`self` is implicit in `obj` method signatures").

## Level descriptors (1–5)

- **5 — Exemplary.** `obj Rectangle` with `has width: float;` and
  `has height: float;` at the top, `def area() -> float` and
  `def perimeter() -> float` as methods inside the archetype body, no
  explicit `self` in method signatures, typed returns, clean Jac style
  (braces + semicolons). Reads like `jac://guide/patterns` pattern #2.
- **4 — Strong.** All three constructs present but with one minor style
  blemish — e.g. uses `class Rectangle` instead of `obj Rectangle` (still
  idiomatic-enough Jac but violates the stated preference in pitfall #4),
  or declares a redundant `def init(width: float, height: float)` instead
  of relying on the auto-generated `obj` constructor.
- **3 — Mixed.** Solves the task and compiles, but misses one core
  construct outright — e.g. defines `Rectangle` as an archetype but pulls
  the methods out as module-level functions that take a `Rectangle`
  argument; or uses an archetype with no type annotations on `has`.
- **2 — Python-leaking.** Structurally transliterated from Python —
  e.g. `def area(self) -> float` with explicit `self` in the parameter
  list (violates pitfall #5b), or `__init__(self, width, height)`
  pattern with `self.width = width` assignments instead of `has`
  declarations (violates pitfall #10). May still compile but reads as
  Python wearing Jac syntax.
- **1 — Does not compile** under `jac-mcp validate_jac`, OR does not
  solve the task (wrong formulas, methods missing, returns wrong type).

## Penalize explicitly

- **Explicit `self` in method signatures** — `def area(self) -> float`.
  Violates pitfall #5b ("`self` is implicit in `obj` method signatures").
  Drops to at most 2. This is the prototypical Python-transliteration
  smell for this task — the whole reason syntax/02 exists is to catch it.
- **Assigning fields via `__init__` / `def init` instead of `has`
  declarations.** Violates pitfall #10 ("Instance variables use `has`,
  not `self`") and defeats the `has` measurement this task probes.
  Drops to at most 2.
- **`class Rectangle` instead of `obj Rectangle`.** Violates pitfall #4
  ("Prefer `obj` over Python-style `class`"). Drops to at most 4.
- **Methods pulled out as module-level `def area(r: Rectangle)`
  functions** — not idiomatic for this task; the spec asks for methods
  on the type. Drops to at most 3.
- **Missing type annotations on `has` or on method return types.**
  Violates pitfall #13 ("Type annotations are important"). Drops
  one level from wherever the solution otherwise lands.
- **Using `can` instead of `def` for the methods.** Violates pitfall
  #5 — `can` is for event-driven abilities on walkers/nodes, not
  regular methods on an `obj`. The compiler will reject this outright
  (`"Expected 'with' after 'can' ability name"`), so it also fails
  compilation → drops to 1.
- **No semicolons / Python-style indentation blocks.** Does not compile.
  Level 1.
