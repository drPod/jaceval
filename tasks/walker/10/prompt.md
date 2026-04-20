# Sum distances along a chain of roads

Write a Jac module that models a directed graph of cities connected by one-way roads, where every road carries a distance, and reports the total distance accumulated by travelling from a given starting city along the outgoing road chain until it ends.

Define a vertex type `City` with a single typed field `name: str`. Define a relationship type `Road` that connects one city to another and carries a single typed field `distance: float` describing the road's length.

In every graph used by this task, each city carries at most one outgoing road — so from any starting city there is a single chain of cities to follow, ending at some city with no outgoing road. A graph may also contain a back-link from a later city to an earlier one, in which case the traversal must still terminate without double-counting any distance.

Expose one function with this signature:

    def total_distance(start: City) -> float

The function takes one starting city, walks along the chain of outgoing roads beginning at `start`, sums the `distance` field of every road it walks over, and returns the total. Each road contributes its `distance` to the sum exactly once, even when the graph contains a back-link.

A city with no outgoing road contributes `0.0`. A single isolated city returns `0.0`.

Examples:

    # Single isolated city.
    a = City(name="A");
    total_distance(a)                              # -> 0.0

    # A --(10.0)--> B, starting from A.
    total_distance(a)                              # -> 10.0

    # A --(10.0)--> B --(20.0)--> C, starting from A.
    total_distance(a)                              # -> 30.0

    # A --(2.5)--> B --(1.5)--> C, starting from A.
    total_distance(a)                              # -> 4.0

Write `City`, `Road`, and `total_distance` in a single file. Do not print anything; just define them.

Output raw Jac source only. No Markdown, no ``` fences, no commentary.
