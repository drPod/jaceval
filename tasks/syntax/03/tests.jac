"""Tests for the syntax/03 affordable_available task."""

import from solution { Product, affordable_available }

test "empty list returns empty" {
    r = affordable_available([], 5.0);
    assert len(r) == 0;
}

test "single affordable in-stock product" {
    xs = [
        Product(name="apple", price=1.5, stock=10),
        Product(name="bread", price=3.0, stock=0),
        Product(name="cheese", price=8.5, stock=5),
    ];
    r = affordable_available(xs, 5.0);
    assert len(r) == 1;
    assert r[0].name == "apple";
}

test "multiple matches preserve order" {
    xs = [
        Product(name="apple", price=1.5, stock=10),
        Product(name="bread", price=3.0, stock=0),
        Product(name="cheese", price=8.5, stock=5),
        Product(name="dates", price=12.0, stock=3),
    ];
    r = affordable_available(xs, 10.0);
    assert len(r) == 2;
    assert r[0].name == "apple";
    assert r[1].name == "cheese";
}

test "no matches returns empty" {
    xs = [
        Product(name="apple", price=1.5, stock=10),
        Product(name="bread", price=3.0, stock=0),
    ];
    r = affordable_available(xs, 0.5);
    assert len(r) == 0;
}

test "out-of-stock items excluded even when affordable" {
    xs = [
        Product(name="bread", price=3.0, stock=0),
        Product(name="milk",  price=2.0, stock=0),
    ];
    r = affordable_available(xs, 10.0);
    assert len(r) == 0;
}
