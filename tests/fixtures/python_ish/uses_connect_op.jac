"""Non-idiomatic: relationships stored in a dict-of-lists, no connect operators."""

obj Graph {
    has adj: dict[str, list[str]] = {};

    def add_edge(src: str, dst: str) -> None {
        if src not in self.adj {
            self.adj[src] = [];
        }
        self.adj[src].append(dst);
    }
}

with entry {
    g = Graph();
    g.add_edge("alice", "bob");
}
