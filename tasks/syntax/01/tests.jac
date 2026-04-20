"""Tests for the syntax/01 total_cost task."""

import from solution { Item, total_cost }

test "empty list returns zero" {
    assert total_cost([]) == 0.0;
}

test "single item" {
    items = [Item(price=2.5, qty=4)];
    assert total_cost(items) == 10.0;
}

test "multiple items" {
    items = [
        Item(price=1.5, qty=2),
        Item(price=3.0, qty=1),
        Item(price=0.5, qty=10)
    ];
    assert total_cost(items) == 11.0;
}

test "zero quantity contributes nothing" {
    items = [Item(price=99.99, qty=0), Item(price=2.0, qty=3)];
    assert total_cost(items) == 6.0;
}

test "price times qty uses float math" {
    items = [Item(price=0.1, qty=3)];
    result = total_cost(items);
    assert result > 0.29 and result < 0.31;
}
