"""Tests for the graph/04 city graph task."""

import from solution { City, Road, build_city_graph }

test "empty input yields empty mapping" {
    cities = build_city_graph([]);
    assert len(cities) == 0;
}

test "single edge creates two nodes with directional link" {
    cities = build_city_graph([("NYC", "Boston")]);
    assert len(cities) == 2;
    nyc = cities["NYC"];
    boston = cities["Boston"];
    assert len([nyc -->]) == 1;
    assert len([boston -->]) == 0;
    assert boston in [nyc -->];
}

test "shared source city deduplicates to one node" {
    cities = build_city_graph([("NYC", "Boston"), ("NYC", "DC")]);
    assert len(cities) == 3;
    nyc = cities["NYC"];
    neighbors = [nyc -->];
    assert len(neighbors) == 2;
    assert cities["Boston"] in neighbors;
    assert cities["DC"] in neighbors;
}

test "cycle is expressible with two directed edges" {
    cities = build_city_graph([("NYC", "Boston"), ("Boston", "NYC")]);
    nyc = cities["NYC"];
    boston = cities["Boston"];
    assert boston in [nyc -->];
    assert nyc in [boston -->];
}

test "duplicate city names collapse across pairs" {
    pairs = [("A", "B"), ("B", "C"), ("A", "C")];
    cities = build_city_graph(pairs);
    assert len(cities) == 3;
    a = cities["A"];
    assert len([a -->]) == 2;
    assert cities["B"] in [a -->];
    assert cities["C"] in [a -->];
}
