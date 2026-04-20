"""Mostly idiomatic: typed node+edge, connect ops used, but edge field is mutated via the filter-and-loop pattern without using the bulk spatial-assign idiom even though it applies to all matching edges."""

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

def reset_all_roads(cities: dict[str, City], new_distance: float) -> None {
    for city in cities.values() {
        edges = [edge city ->:Road:->];
        for i in range(len(edges)) {
            edges[i].distance = new_distance;
        }
    }
}
