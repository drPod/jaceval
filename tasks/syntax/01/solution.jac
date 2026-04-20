"""Total cost of a cart of line items."""

obj Item {
    has price: float;
    has qty: int;
}

def total_cost(items: list[Item]) -> float {
    total: float = 0.0;
    for item in items {
        total = total + item.price * item.qty;
    }
    return total;
}
