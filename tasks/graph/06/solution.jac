"""Road-distance graph with in-place distance mutation on typed edges."""

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

def update_road_distance(cities: dict[str, City], src: str, dst: str, new_distance: float) -> None {
    src_city = cities[src];
    dst_city = cities[dst];
    targets = [src_city ->:Road:->];
    edges = [edge src_city ->:Road:->];
    for i in range(len(edges)) {
        if targets[i] is dst_city {
            edges[i].distance = new_distance;
            return;
        }
    }
}
