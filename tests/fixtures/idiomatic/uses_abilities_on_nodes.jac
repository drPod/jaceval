"""Idiomatic: the node declares a can/with/entry ability; walker is empty."""

walker Crawler {}

node Post {
    has views: int = 0;

    can bump with Crawler entry {
        self.views += 1;
    }
}
