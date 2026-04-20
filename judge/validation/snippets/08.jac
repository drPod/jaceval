"""Correct but not idiomatic: typed node archetype exists, but relationships are *also* duplicated into a parallel dict-of-lists adjacency, adding redundant bookkeeping that the graph already stores."""

node City {
    has name: str;
}

edge Road;

obj RoadGraph {
    has cities: dict[str, City] = {};
    has adj: dict[str, list[str]] = {};

    def add(src: str, dst: str) -> None {
        if src not in self.cities {
            self.cities[src] = City(name=src);
            self.adj[src] = [];
        }
        if dst not in self.cities {
            self.cities[dst] = City(name=dst);
            self.adj[dst] = [];
        }
        self.cities[src] ++> self.cities[dst];
        self.adj[src].append(dst);
    }
}

with entry {
    g = RoadGraph();
    g.add("A", "B");
    g.add("B", "C");
}
