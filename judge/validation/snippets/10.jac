"""Python-transliterated: relationships stored in dict-of-lists adjacency instead of Jac node/edge archetypes. No connect op, no typed edge, no graph-native storage."""

obj RoadGraph {
    has adj: dict[str, list[str]] = {};
    has distances: dict[str, dict[str, float]] = {};

    def add_road(src: str, dst: str, distance: float) -> None {
        if src not in self.adj {
            self.adj[src] = [];
            self.distances[src] = {};
        }
        if dst not in self.adj {
            self.adj[dst] = [];
            self.distances[dst] = {};
        }
        self.adj[src].append(dst);
        self.distances[src][dst] = distance;
    }

    def neighbors(city: str) -> list[str] {
        return self.adj.get(city, []);
    }
}

with entry {
    g = RoadGraph();
    g.add_road("A", "B", 12.5);
    g.add_road("B", "C", 4.0);
    print(g.neighbors("A"));
}
