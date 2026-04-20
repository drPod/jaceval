"""Idiomatic: every has-field, param, and return type is annotated."""

obj Record {
    has name: str;
    has count: int = 0;
}

def greet(r: Record) -> str {
    return "hi " + r.name;
}

def double(n: int) -> int {
    return n * 2;
}
