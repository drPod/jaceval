# Count reachable vertices by type

Write a Jac module that models a directed graph whose vertices come in two distinct kinds — people and organizations — and counts how many of each kind are reachable from a given starting vertex by following outgoing links.

Define two vertex types:

- `Person` with a single typed field `name: str`.
- `Organization` with a single typed field `name: str`.

`Person` and `Organization` are different types, even when their `name` values match. A graph may mix both types freely, and a link may go from either type to either type.

Expose one function with this signature:

    def count_by_type(start: Person | Organization) -> tuple[int, int]

The function takes one starting vertex and returns `(num_persons, num_orgs)`, where:

- `num_persons` is the number of `Person` vertices reachable from `start` by following outgoing links zero or more times, **including `start` itself if it is a `Person`**.
- `num_orgs` is the same count for `Organization` vertices.

Each reachable vertex must be counted exactly once, even when the graph contains cycles or when multiple paths lead to the same vertex.

Examples:

    # A single isolated Person vertex, no outgoing links.
    count_by_type(Person(name="Alice"))    # -> (1, 0)

    # Alice --> Bob --> Acme  (Alice, Bob are Persons; Acme is an Organization)
    count_by_type(alice)                   # -> (2, 1)

    # 2-cycle: Alice --> Acme --> Alice
    count_by_type(alice)                   # -> (1, 1)

Write `Person`, `Organization`, and `count_by_type` in a single file. Do not print anything; just define them.

Output raw Jac source only. No Markdown, no ``` fences, no commentary.
