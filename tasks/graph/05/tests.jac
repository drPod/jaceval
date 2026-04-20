"""Tests for the graph/05 collaboration graph task."""

import from solution { Person, Collab, build_collab_graph }

test "empty input yields empty mapping" {
    people = build_collab_graph([]);
    assert len(people) == 0;
}

test "pair is mutually reachable via undirected neighbor query" {
    people = build_collab_graph([("Alice", "Bob", "ProjectX")]);
    assert len(people) == 2;
    alice = people["Alice"];
    bob = people["Bob"];
    assert bob in [alice <-->];
    assert alice in [bob <-->];
}

test "edge carries project field accessible on the Collab edge" {
    people = build_collab_graph([("Alice", "Bob", "ProjectX")]);
    alice = people["Alice"];
    bob = people["Bob"];
    edges_from_alice = [edge alice <-->][?:Collab];
    edges_from_bob = [edge bob <-->][?:Collab];
    assert len(edges_from_alice) == 1;
    assert len(edges_from_bob) == 1;
    assert edges_from_alice[0].project == "ProjectX";
    assert edges_from_bob[0].project == "ProjectX";
}

test "non-adjacent pair is not directly connected" {
    people = build_collab_graph([("Alice", "Bob", "ProjectX"), ("Bob", "Carol", "ProjectY")]);
    alice = people["Alice"];
    carol = people["Carol"];
    assert carol not in [alice <-->];
    assert alice not in [carol <-->];
}

test "repeated names across triples collapse to a single person node" {
    triples = [("Alice", "Bob", "P1"), ("Alice", "Carol", "P2"), ("Bob", "Carol", "P3")];
    people = build_collab_graph(triples);
    assert len(people) == 3;
    alice = people["Alice"];
    neighbors = [alice <-->];
    assert people["Bob"] in neighbors;
    assert people["Carol"] in neighbors;
    assert len(neighbors) == 2;
}
