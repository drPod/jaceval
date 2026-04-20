"""Idiomatic use of a walker archetype."""

node Item {
    has value: int;
}

walker Sum {
    has total: int = 0;

    can add with Item entry {
        self.total += here.value;
        visit [-->];
    }
}

with entry {
    a = Item(value=1);
    b = Item(value=2);
    root() ++> a;
    a ++> b;
    w = root() spawn Sum();
    print(w.total);
}
