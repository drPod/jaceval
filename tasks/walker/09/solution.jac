"""Bump the view-count of every reachable post via a node-side ability."""

walker ViewBumper {
    has visited: set[str] = set();
}

node Post {
    has title: str;
    has views: int = 0;

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
