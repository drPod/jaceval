"""Count reachable vertices by type using a type-dispatched walker."""

node Person {
    has name: str;
}

node Organization {
    has name: str;
}

walker CountByType {
    has person_count: int = 0;
    has org_count: int = 0;
    has visited: set[str] = set();

    can count_person with Person entry {
        vid = jid(here);
        if vid in self.visited {
            return;
        }
        self.visited.add(vid);
        self.person_count += 1;
        visit [-->];
    }

    can count_org with Organization entry {
        vid = jid(here);
        if vid in self.visited {
            return;
        }
        self.visited.add(vid);
        self.org_count += 1;
        visit [-->];
    }
}

def count_by_type(start: Person | Organization) -> tuple[int, int] {
    w = start spawn CountByType();
    return (w.person_count, w.org_count);
}
