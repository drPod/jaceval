"""Tests for the walker/07 count-by-type task."""

import from solution { Person, Organization, count_by_type }

test "isolated person counts only itself" {
    alice = Person(name="Alice");
    (persons, orgs) = count_by_type(alice);
    assert persons == 1;
    assert orgs == 0;
}

test "isolated organization counts only itself" {
    acme = Organization(name="Acme");
    (persons, orgs) = count_by_type(acme);
    assert persons == 0;
    assert orgs == 1;
}

test "small mixed graph: 2 persons + 1 org reachable" {
    alice = Person(name="Alice");
    bob = Person(name="Bob");
    acme = Organization(name="Acme");
    alice ++> bob;
    bob ++> acme;
    (persons, orgs) = count_by_type(alice);
    assert persons == 2;
    assert orgs == 1;
}

test "multi-hop chain: walker traverses transitively, not just direct neighbors" {
    p1 = Person(name="P1");
    p2 = Person(name="P2");
    p3 = Person(name="P3");
    o1 = Organization(name="O1");
    o2 = Organization(name="O2");
    p1 ++> p2;
    p2 ++> p3;
    p3 ++> o1;
    o1 ++> o2;
    (persons, orgs) = count_by_type(p1);
    assert persons == 3;
    assert orgs == 2;
}

test "cycle in graph: each vertex counted exactly once, no infinite loop" {
    alice = Person(name="Alice");
    acme = Organization(name="Acme");
    alice ++> acme;
    acme ++> alice;
    (persons, orgs) = count_by_type(alice);
    assert persons == 1;
    assert orgs == 1;
}
