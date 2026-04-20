"""Idiomatic: walker issues visit to traverse outgoing neighbours."""

node Item {
    has value: int = 0;
}

walker Crawler {
    has touched: int = 0;

    can tick with Item entry {
        self.touched += 1;
        visit [-->];
    }
}
