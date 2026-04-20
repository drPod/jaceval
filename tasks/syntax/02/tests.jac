"""Tests for the syntax/02 Rectangle task."""

import from solution { Rectangle }

test "normal rectangle area" {
    r = Rectangle(width=4.0, height=3.0);
    assert r.area() == 12.0;
}

test "normal rectangle perimeter" {
    r = Rectangle(width=4.0, height=3.0);
    assert r.perimeter() == 14.0;
}

test "zero-dimension rectangle" {
    r = Rectangle(width=0.0, height=5.0);
    assert r.area() == 0.0;
    assert r.perimeter() == 10.0;
}

test "square case" {
    r = Rectangle(width=2.5, height=2.5);
    assert r.area() == 6.25;
    assert r.perimeter() == 10.0;
}

test "non-integer floats" {
    r = Rectangle(width=1.5, height=0.5);
    a = r.area();
    assert a > 0.74 and a < 0.76;
    p = r.perimeter();
    assert p > 3.99 and p < 4.01;
}
