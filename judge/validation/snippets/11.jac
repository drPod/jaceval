"""Python-transliterated: manual BFS over [-->] neighbor lists inside a plain function instead of a walker with visit. Archetypes exist but traversal is hand-rolled."""

node Person {
    has name: str;
}

def count_reachable(start: Person) -> int {
    frontier: list[Person] = [start];
    seen: set[str] = set();
    total: int = 0;
    while len(frontier) > 0 {
        cur = frontier.pop(0);
        vid = jid(cur);
        if vid in seen {
            continue;
        }
        seen.add(vid);
        total += 1;
        for n in [cur -->] {
            frontier.append(n);
        }
    }
    return total;
}
