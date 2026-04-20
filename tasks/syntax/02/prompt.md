# Rectangle with area and perimeter

Write a Jac module that defines a `Rectangle` type with two typed fields:

- `width` (float)
- `height` (float)

Attach two methods to it:

- `area() -> float` — returns `width * height`.
- `perimeter() -> float` — returns `2 * (width + height)`.

Examples:

    r = Rectangle(width=4.0, height=3.0)
    r.area() == 12.0
    r.perimeter() == 14.0

    s = Rectangle(width=2.5, height=2.5)
    s.area() == 6.25
    s.perimeter() == 10.0

Write the `Rectangle` definition and both methods in a single file. Do not print anything; just define them.

Output raw Jac source only. No Markdown, no ``` fences, no commentary.
