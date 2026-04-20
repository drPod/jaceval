"""City graph built from directed road pairs."""

node City {
    has name: str;
}

edge Road;

def build_city_graph(roads: list[tuple[str, str]]) -> dict[str, City] {
    cities: dict[str, City] = {};
    for (src, dst) in roads {
        if src not in cities {
            cities[src] = City(name=src);
        }
        if dst not in cities {
            cities[dst] = City(name=dst);
        }
        cities[src] ++> cities[dst];
    }
    return cities;
}
