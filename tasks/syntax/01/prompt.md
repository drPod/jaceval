# Total cost of a cart

Write a Jac module that defines:

1. An `obj Item` with two typed fields: `price` (float) and `qty` (int).
2. A function `total_cost(items: list[Item]) -> float` that returns the sum of `price * qty` across every item in the list. An empty list returns `0.0`.

Examples:

    total_cost([]) == 0.0
    total_cost([Item(price=2.5, qty=4)]) == 10.0
    total_cost([Item(price=1.5, qty=2), Item(price=3.0, qty=1)]) == 6.0

Write both the `Item` definition and the `total_cost` function in a single file. Do not print anything; just define them.

Output raw Jac source only. No Markdown, no ``` fences, no commentary. Remember Jac requires `has` before every field declaration inside an `obj`.
