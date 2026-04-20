"""Idiomatic: graph with a declared edge archetype carrying typed data."""

node City {
    has name: str;
}

edge Road {
    has distance: float;
}

with entry {
    a = City(name="A");
    b = City(name="B");
    root() ++> a;
    a +>:Road(distance=12.5):+> b;
}
