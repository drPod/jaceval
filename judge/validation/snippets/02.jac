"""Idiomatic graph construction: typed node, typed edge archetype, connect ops."""

node City {
    has name: str;
}

edge Road {
    has distance: float;
}

def build_road_graph(roads: list[tuple[str, str, float]]) -> dict[str, City] {
    cities: dict[str, City] = {};
    for (src, dst, distance) in roads {
        if src not in cities {
            cities[src] = City(name=src);
        }
        if dst not in cities {
            cities[dst] = City(name=dst);
        }
        cities[src] +>:Road(distance=distance):+> cities[dst];
    }
    return cities;
}

with entry {
    g = build_road_graph([("A", "B", 12.5), ("B", "C", 4.0)]);
    print(len(g));
}
