"""Search for a reachable admin using a walker that disengages on first match."""

node User {
    has name: str;
    has is_admin: bool;
}

walker FindAdmin {
    has found: bool = False;
    has visited: set[str] = set();

    can check with User entry {
        vid = jid(here);
        if vid in self.visited {
            return;
        }
        self.visited.add(vid);
        if here.is_admin {
            self.found = True;
            disengage;
        }
        visit [-->];
    }
}

def has_admin_reachable(start: User) -> bool {
    w = start spawn FindAdmin();
    return w.found;
}
