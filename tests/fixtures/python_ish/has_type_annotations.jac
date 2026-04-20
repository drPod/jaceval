"""Non-idiomatic: a function has typed params but no return type annotation."""

obj Record {
    has name: str;
}

def greet(r: Record) {
    print("hi " + r.name);
}
