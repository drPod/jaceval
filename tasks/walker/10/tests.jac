"""Tests for the walker/10 path-distance aggregation task."""

import from solution { City, Road, total_distance }

test "single isolated city returns zero" {
    a = City(name="A");
    assert total_distance(a) == 0.0;
}

test "two-city chain returns the single road distance" {
    a = City(name="A");
    b = City(name="B");
    a +>:Road(distance=10.0):+> b;
    assert total_distance(a) == 10.0;
}

test "three-city chain returns the sum of both distances" {
    a = City(name="A");
    b = City(name="B");
    c = City(name="C");
    a +>:Road(distance=10.0):+> b;
    b +>:Road(distance=20.0):+> c;
    assert total_distance(a) == 30.0;
}

test "non-integer distances sum correctly under float tolerance" {
    a = City(name="A");
    b = City(name="B");
    c = City(name="C");
    a +>:Road(distance=2.5):+> b;
    b +>:Road(distance=1.5):+> c;
    result = total_distance(a);
    assert abs(result - 4.0) < 1e-9;
}

test "cycle back to start is counted once and terminates" {
    a = City(name="A");
    b = City(name="B");
    c = City(name="C");
    a +>:Road(distance=5.0):+> b;
    b +>:Road(distance=7.0):+> c;
    c +>:Road(distance=3.0):+> a;
    # Each road's distance is summed exactly once: 5.0 + 7.0 + 3.0 = 15.0.
    # Visited-set dedupe prevents infinite loop on the back-edge into A.
    assert total_distance(a) == 15.0;
}
