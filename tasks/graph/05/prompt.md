# Collaboration graph with mutual, project-carrying relationships

Write a Jac module that builds a graph of people and the collaborations between them.

Define a vertex type `Person` with a single typed field `name: str`. Define a relationship type `Collab` that carries a single typed field `project: str` describing the project two people collaborated on. The relationship is **mutual**: if person A collaborated with person B on project P, then person B also collaborated with person A on project P — the two endpoints see each other as collaborators on the same project.

Expose a function with this signature:

    def build_collab_graph(collabs: list[tuple[str, str, str]]) -> dict[str, Person]

Each triple `(a, b, project)` in `collabs` describes one collaboration: person `a` and person `b` worked together on `project`. The function must:

1. Create exactly one `Person` vertex per unique person name across all triples. Repeated names in later triples reuse the already-created vertex.
2. For each triple, record a single **mutual** collaboration relationship between the two people, with the project name attached to that relationship as data.
3. Return a mapping from each person's `name` to their `Person` vertex, so the caller can reach every vertex by name.

Examples:

    g = build_collab_graph([])
    # g == {}

    g = build_collab_graph([("Alice", "Bob", "ProjectX")])
    # Alice and Bob are now each other's collaborators on "ProjectX".
    # The relationship carries "ProjectX" as data on itself.

    g = build_collab_graph([("Alice", "Bob", "ProjectX"), ("Bob", "Carol", "ProjectY")])
    # Alice <-> Bob on "ProjectX"; Bob <-> Carol on "ProjectY".
    # Alice and Carol are NOT directly related.

Write the `Person` type, the `Collab` relationship type, and the `build_collab_graph` function in a single file. Do not print anything; just define them.

Output raw Jac source only. No Markdown, no ``` fences, no commentary.
