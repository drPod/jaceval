"""Mostly idiomatic: node-side ability + walker, but one has-field is missing its type annotation default."""

walker ViewBumper {
    has visited: set[str] = set();
}

node Post {
    has title: str;
    has views: int;

    can tick with ViewBumper entry {
        vid = jid(self);
        if vid in visitor.visited {
            return;
        }
        visitor.visited.add(vid);
        self.views += 1;
        visit [-->];
    }
}

def increment_views_reachable(start: Post) -> int {
    w = start spawn ViewBumper();
    return len(w.visited);
}
