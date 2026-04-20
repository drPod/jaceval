# Rubric: syntax/01 — total_cost over a list of Item

## Task summary

Define an `Item` archetype with `price: float` and `qty: int`, and a function
`total_cost(items: list[Item]) -> float` that returns the sum of `price * qty`
over all items. An empty list must return `0.0`.

## Expected idiomatic constructs

All three are required for full idiomaticity credit:

1. **`has` field typing inside an `obj`** — `obj Item { has price: float; has qty: int; }`.
   Required type annotations on every `has` declaration (see pitfall #13 in
   `jac://guide/pitfalls` — "Type annotations are important" — and pattern #2
   in `jac://guide/patterns`).
2. **`for ... in ...` iteration** with braces and semicolons
   (`for item in items { total = total + ...; }`). Not `.map`, not a
   Python-style list comprehension sum, not `reduce`.
3. **Typed return** on the function signature:
   `def total_cost(items: list[Item]) -> float { ... }`. Pattern #1 in
   `jac://guide/patterns`.

## Level descriptors (1–5)

- **5 — Exemplary.** All three constructs present. `obj` (not `class`),
  required type annotations on every `has` and on the function signature,
  `for-in` loop. Clean Jac style (braces, semicolons, no Python leakage).
  Reads like the `jac://guide/patterns` examples.
- **4 — Strong.** All three constructs present but with a minor style
  blemish — e.g. uses `sum([i.price * i.qty for i in items])` (comprehension)
  instead of an explicit `for-in`, OR uses `class Item` instead of
  `obj Item`. Correct Jac otherwise.
- **3 — Mixed.** Solves the task and compiles, but misses one of the
  three expected constructs outright — e.g. drops a type annotation,
  returns untyped, or skips the `Item` archetype and takes
  `list[dict]` / `list[tuple]`.
- **2 — Python-leaking.** Missing multiple type annotations, Python-style
  `:` blocks preserved incorrectly, or structurally transliterated from
  Python (e.g. `def total_cost(items):` with no type hints). May not
  compile under `jac-mcp validate_jac`.
- **1 — Does not compile** OR does not solve the task (wrong math,
  always returns 0, crashes on non-empty list).

## Penalize explicitly

- **Python transliteration.** `sum(i.price * i.qty for i in items)` with no
  `for-in` block — drops to at most 4. Generator-expression sum is a
  Python idiom that hides the for-in construct this task is measuring.
- **Missing type annotations.** Any `has` without a type, or a function
  signature without `-> float`, drops to at most 3. Violates pitfall #13.
- **`class` instead of `obj`.** Violates pitfall #4 ("Prefer `obj` over
  Python-style `class`"). Drops to at most 4.
- **Using a `dict` or `tuple` in place of `Item`.** The task explicitly
  calls for a typed archetype; skipping it defeats the `has` field typing
  measurement. Drops to at most 3.
- **Implicit `self` in method signatures** (if the solver wraps
  `total_cost` as a method). Violates pitfall #5b. Drops one level.
- **No semicolons / indentation blocks.** Does not compile — level 1.
