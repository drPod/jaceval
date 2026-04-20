"""Return products that are affordable and in stock."""

obj Product {
    has name: str;
    has price: float;
    has stock: int;
}

def affordable_available(products: list[Product], max_price: float) -> list[Product] {
    return products[?price <= max_price, stock > 0];
}
