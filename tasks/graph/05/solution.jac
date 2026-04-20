"""Symmetric collaboration graph with typed Collab edges."""

node Person {
    has name: str;
}

edge Collab {
    has project: str;
}

def build_collab_graph(collabs: list[tuple[str, str, str]]) -> dict[str, Person] {
    people: dict[str, Person] = {};
    for (a, b, project) in collabs {
        if a not in people {
            people[a] = Person(name=a);
        }
        if b not in people {
            people[b] = Person(name=b);
        }
        people[a] <+: Collab(project=project) :+> people[b];
    }
    return people;
}
