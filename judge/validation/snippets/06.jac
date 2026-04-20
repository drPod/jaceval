"""Mostly idiomatic walker: uses visit and typed ability. Minor smell — has a redundant generic `can kickoff with entry` that only fires at the spawn node (no typed-node filter), which is a known weaker pattern than a typed `with Root entry` or `with City entry`."""

node City {
    has name: str;
    has visits: int = 0;
}

walker Tour {
    has stops: int = 0;
    has visited: set[str] = set();

    can kickoff with entry {
        visit [-->];
    }

    can stop with City entry {
        vid = jid(here);
        if vid in self.visited {
            return;
        }
        self.visited.add(vid);
        here.visits += 1;
        self.stops += 1;
        visit [-->];
    }
}

def tour_count(start: City) -> int {
    w = start spawn Tour();
    return w.stops;
}
