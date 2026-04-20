# Affordable, in-stock products

Write a Jac module that defines:

1. A record-like type `Product` with three typed fields: `name` (str), `price` (float), and `stock` (int). `stock` is the number of units available.
2. A function `affordable_available(products: list[Product], max_price: float) -> list[Product]` that returns every product whose `price` is less than or equal to `max_price` **and** whose `stock` is greater than zero. The returned list should preserve the original order. An empty input list returns an empty list. If no product matches, return an empty list.

Examples:

    xs = [
        Product(name="apple",  price=1.5, stock=10),
        Product(name="bread",  price=3.0, stock=0),
        Product(name="cheese", price=8.5, stock=5),
    ]
    affordable_available(xs, 5.0)    # [Product(name="apple", price=1.5, stock=10)]
    affordable_available(xs, 10.0)   # [apple, cheese] in that order
    affordable_available(xs, 0.5)    # []
    affordable_available([], 5.0)    # []

Write both the `Product` definition and the `affordable_available` function in a single file. Do not print anything; just define them.

Output raw Jac source only. No Markdown, no ``` fences, no commentary.
