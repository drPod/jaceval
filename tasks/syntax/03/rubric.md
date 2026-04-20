# Rubric: syntax/03 — Filter a list of typed records (HELD OUT)

## Task summary

Define a `Product` archetype with `name: str`, `price: float`, `stock: int`,
and a function `affordable_available(products: list[Product], max_price: float) -> list[Product]`
that returns the products whose `price <= max_price` and `stock > 0`, preserving
input order. This task measures whether the model reaches for Jac's native
filter comprehension (`[?...]`) over a list of typed `obj` records, or
Python-transliterates the same logic as a for-loop or generic list
comprehension.

## Expected idiomatic constructs

All three are required for full idiomaticity credit:

1. **`obj` archetype with typed `has` fields** — `obj Product { has name: str;
   has price: float; has stock: int; }`. See pitfall #4 in
   `jac://guide/pitfalls` ("Prefer `obj` over Python-style `class`"),
   pitfall #10 ("Instance variables use `has`, not `self`"), and pitfall #13
   ("Type annotations are important").
2. **Filter comprehension `[?...]`** on the list — `products[?price <= max_price, stock > 0]`.
   See `jac://docs/advanced` ("Filter Comprehensions"): *"Filter comprehensions
   use the `[?...]` operator to select elements from a collection based on
   attribute conditions... Multiple conditions are separated by commas and
   are ANDed together."* This is the Jac-specific construct this task probes.
3. **Full type annotations on the function signature** — parameter types
   `list[Product]` and `float`, return type `list[Product]`. See pitfall #13
   in `jac://guide/pitfalls` ("Type annotations are important").

## Level descriptors (1–5)

- **5 — Exemplary.** `obj Product` with three typed `has` fields; the
  function uses a single-expression `return products[?price <= max_price, stock > 0];`
  filter comprehension; full type annotations on signature; braces +
  semicolons + no explicit `self` anywhere. Reads like the canonical
  example in `jac://docs/advanced`.
- **4 — Strong.** Uses the filter comprehension correctly but has one
  minor blemish — e.g. uses `class Product` instead of `obj Product`
  (violates pitfall #4 but still idiomatic-enough), or splits the
  comprehension across two filters (`products[?price <= max_price][?stock > 0]`)
  instead of the comma-separated AND form, or redundantly writes
  `stock > 0 == True`-type noise.
- **3 — Mixed.** Solves the task and compiles, but reaches for a generic
  Python-style construct instead of the filter comprehension — e.g.
  `[p for p in products if p.price <= max_price and p.stock > 0]`. This
  is correct, compiles, and passes tests, but defeats the whole point of
  the task (which is to exercise Jac's filter-comprehension affordance).
  Also lands here if the `obj` is well-formed but the function is missing
  a type annotation.
- **2 — Python-leaking.** Structurally transliterated from Python —
  e.g. a `for` loop with `.append()`/`+= [p]` to build the result list,
  or defines `Product` as `class Product` with an `__init__` assigning
  fields via `self.name = name` instead of using `has` declarations
  (violates pitfalls #4 and #10). May still compile but reads as Python
  wearing Jac syntax.
- **1 — Does not compile** under `jac-mcp validate_jac`, OR does not
  solve the task (wrong predicate, wrong return type, missing function,
  wrong ordering).

## Penalize explicitly

- **For-loop with `.append()` / `+= [x]` to build the result list** where
  the idiomatic construct is a filter comprehension. Drops to at most 2.
  This is the central failure mode for this task — the whole reason it
  exists is to catch the Python-transliterated "loop and accumulate"
  pattern.
- **Generic `[p for p in products if ...]` list comprehension instead of
  the `[?...]` filter comprehension.** Correct and compiles, but
  sidesteps the Jac-specific affordance this task measures. Drops to at
  most 3. Cite `jac://docs/advanced` ("Filter Comprehensions") — the
  filter comprehension *is* Jac's idiom for this exact shape.
- **`class Product` with explicit `def init` + `self.x = x` assignments
  instead of `obj Product` with `has`.** Violates pitfalls #4 and #10.
  Drops to at most 2.
- **Explicit `self` in method signatures** (if the model tries to attach
  the filter as a method on `Product`). Violates pitfall #5b. Drops to
  at most 2.
- **Missing type annotations on `has` or on the function signature.**
  Violates pitfall #13. Drops one level from wherever the solution
  otherwise lands.
- **No semicolons / Python-style indentation blocks.** Does not compile.
  Level 1.

## Held-out note

This task is held out from iteration. Its rubric and expected idiomatic
constructs were authored before running the baseline, and are not tuned
to observed model output. Scores on this task during v0 must not be used
to refine the SKILL.md or any other context arm; they report the
generalization gap of the harness.
