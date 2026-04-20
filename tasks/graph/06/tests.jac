"""Tests for the graph/06 road-distance mutation task."""

import from solution { City, Road, build_road_graph, update_road_distance }

def _distance_of(cities: dict[str, City], src: str, dst: str) -> float {
    src_city = cities[src];
    dst_city = cities[dst];
    targets = [src_city ->:Road:->];
    edges = [edge src_city ->:Road:->];
    for i in range(len(edges)) {
        if targets[i] is dst_city {
            return edges[i].distance;
        }
    }
    return -1.0;
}

test "build stores the initial distance on the edge" {
    g = build_road_graph([("NYC", "Boston", 200.0)]);
    assert len(g) == 2;
    assert _distance_of(g, "NYC", "Boston") == 200.0;
}

test "update mutates the edge in place; re-read sees new value" {
    g = build_road_graph([("NYC", "Boston", 200.0)]);
    update_road_distance(g, "NYC", "Boston", 220.0);
    assert _distance_of(g, "NYC", "Boston") == 220.0;
}

test "update touches only the targeted road" {
    g = build_road_graph([("NYC", "Boston", 200.0), ("NYC", "Philly", 95.0)]);
    update_road_distance(g, "NYC", "Boston", 220.0);
    assert _distance_of(g, "NYC", "Boston") == 220.0;
    assert _distance_of(g, "NYC", "Philly") == 95.0;
}

test "reverse-direction road on the same pair is unaffected" {
    g = build_road_graph([("NYC", "Boston", 200.0), ("Boston", "NYC", 210.0)]);
    update_road_distance(g, "NYC", "Boston", 220.0);
    assert _distance_of(g, "NYC", "Boston") == 220.0;
    assert _distance_of(g, "Boston", "NYC") == 210.0;
}

test "repeated updates keep the latest value, not accumulated" {
    g = build_road_graph([("NYC", "Boston", 200.0)]);
    update_road_distance(g, "NYC", "Boston", 220.0);
    update_road_distance(g, "NYC", "Boston", 250.0);
    assert _distance_of(g, "NYC", "Boston") == 250.0;
}
