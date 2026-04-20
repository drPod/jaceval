# Road-distance graph with updatable distances

Write a Jac module that builds a directed graph of cities connected by one-way roads, where every road carries a distance that can later be updated.

Define a vertex type `City` with a single typed field `name: str`. Define a relationship type `Road` that connects one city to another and carries a single typed field `distance: float` describing the road's length. The relationship is directional: the road from city `src` to city `dst` is a different road from the one (if any) going `dst` to `src`.

Expose two functions with these signatures:

    def build_road_graph(roads: list[tuple[str, str, float]]) -> dict[str, City]
    def update_road_distance(cities: dict[str, City], src: str, dst: str, new_distance: float) -> None

`build_road_graph` consumes a list of triples `(src, dst, distance)`. Each triple describes one one-way road from city `src` to city `dst` with the given distance. The function must:

1. Create exactly one `City` vertex per unique name across all triples. Repeated names in later triples reuse the already-created vertex.
2. For each triple, record a directional connection from the `src` vertex to the `dst` vertex and attach `distance` to that connection as data.
3. Return a mapping from each city's `name` to its `City` vertex.

`update_road_distance` is given the mapping returned by `build_road_graph`, a source name `src`, a destination name `dst`, and a new distance. Both cities are guaranteed to exist in the mapping and a single one-way road from `src` to `dst` is guaranteed to exist. The function must locate that specific road and change its stored distance to `new_distance` in place, so any later read of the road's distance returns the new value. The function returns `None`.

Examples:

    g = build_road_graph([("NYC", "Boston", 200.0)])
    # The road from NYC to Boston currently has distance 200.0.

    update_road_distance(g, "NYC", "Boston", 220.0)
    # The same road from NYC to Boston now has distance 220.0.

    g = build_road_graph([("NYC", "Boston", 200.0), ("Boston", "NYC", 210.0)])
    update_road_distance(g, "NYC", "Boston", 220.0)
    # Only the NYC-to-Boston road is changed; the Boston-to-NYC road is still 210.0.

Write `City`, `Road`, `build_road_graph`, and `update_road_distance` in a single file. Do not print anything; just define them.

Output raw Jac source only. No Markdown, no ``` fences, no commentary.
