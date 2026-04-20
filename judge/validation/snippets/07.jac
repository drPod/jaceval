"""Correct but not idiomatic: walker uses a mutable list as a visited-set and linear-scan membership tests instead of a typed `set[str]`. Still traverses correctly, but the data structure choice is Python-transliterated."""

node Person {
    has name: str;
}

walker CountPeople {
    has count: int = 0;
    has visited: list[str] = [];

    can tally with Person entry {
        vid = jid(here);
        for v in self.visited {
            if v == vid {
                return;
            }
        }
        self.visited.append(vid);
        self.count += 1;
        visit [-->];
    }
}

def count_people(start: Person) -> int {
    w = start spawn CountPeople();
    return w.count;
}
