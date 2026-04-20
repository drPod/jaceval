"""Non-idiomatic: manual traversal instead of a walker."""

node Item {
    has value: int;
}

def sum_items(start: Item) -> int {
    frontier: list[Item] = [start];
    seen: set[str] = set();
    total: int = 0;
    while len(frontier) > 0 {
        cur = frontier.pop();
        vid = jid(cur);
        if vid in seen {
            continue;
        }
        seen.add(vid);
        total += cur.value;
        for n in [cur -->] {
            frontier.append(n);
        }
    }
    return total;
}
