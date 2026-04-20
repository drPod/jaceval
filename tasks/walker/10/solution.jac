"""Sum distances along a linear road chain starting from `start`."""

node City {
    has name: str;
}

edge Road {
    has distance: float;
}

walker PathSum {
    has total: float = 0.0;
    has visited: set[str] = set();

    can tick with City entry {
        vid = jid(here);
        if vid in self.visited {
            return;
        }
        self.visited.add(vid);
        roads: list[Road] = [edge here ->:Road:->];
        for e in roads {
            self.total += e.distance;
        }
        visit [-->];
    }
}

def total_distance(start: City) -> float {
    w = start spawn PathSum();
    return w.total;
}
