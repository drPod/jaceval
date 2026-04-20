"""Idiomatic: graph construction uses connect operators."""

node Person {
    has name: str;
}

with entry {
    alice = Person(name="Alice");
    bob = Person(name="Bob");
    root() ++> alice;
    alice ++> bob;
    alice <++> bob;
}
