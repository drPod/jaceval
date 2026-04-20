"""Non-idiomatic: relationship data stored on the node instead of a typed relationship."""

node City {
    has name: str;
    has distance_to_next: float = 0.0;
}

with entry {
    a = City(name="A", distance_to_next=12.5);
    b = City(name="B");
    root() ++> a;
    a ++> b;
}
