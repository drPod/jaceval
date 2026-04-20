"""Non-idiomatic: the walker carries the ability; the node has no abilities."""

node Post {
    has views: int = 0;
}

walker Tally {
    has total: int = 0;

    can count with Post entry {
        self.total += here.views;
    }
}
