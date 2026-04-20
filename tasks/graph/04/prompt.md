# Directed graph of cities and roads

Write a Jac module that builds a directed graph of cities connected by one-way roads.

Define a vertex type `City` with a single typed field `name: str`, and a relationship type `Road` that connects one city to another with no additional data of its own.

Expose a function with this signature:

    def build_city_graph(roads: list[tuple[str, str]]) -> dict[str, City]

Each pair `(src, dst)` in `roads` describes a single one-way road from `src` to `dst`. The function must:

1. Create exactly one `City` vertex per unique city name across all pairs. Repeated names in later pairs reuse the already-created vertex.
2. For each pair, record a directional connection from the `src` vertex to the `dst` vertex.
3. Return a mapping from each city's `name` to its `City` vertex, so the caller can reach every vertex by name.

Examples:

    g = build_city_graph([])
    # g == {}

    g = build_city_graph([("NYC", "Boston")])
    # g["Boston"] is reachable by following the one outgoing connection from g["NYC"]
    # g["Boston"] leads to no further cities

    g = build_city_graph([("NYC", "Boston"), ("Boston", "NYC")])
    # Both directions are reachable because two separate one-way connections were added

Write the `City` type, the `Road` relationship type, and the `build_city_graph` function in a single file. Do not print anything; just define them.

Output raw Jac source only. No Markdown, no ``` fences, no commentary.
