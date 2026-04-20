"""Correct but not idiomatic: walker finds an admin and uses an early-exit flag + `return` where `disengage` is the Jac-native primitive for aborting traversal."""

node User {
    has name: str;
    has is_admin: bool;
}

walker FindAdmin {
    has found: bool = False;
    has done: bool = False;
    has visited: set[str] = set();

    can check with User entry {
        if self.done {
            return;
        }
        vid = jid(here);
        if vid in self.visited {
            return;
        }
        self.visited.add(vid);
        if here.is_admin {
            self.found = True;
            self.done = True;
            return;
        }
        visit [-->];
    }
}

def has_admin_reachable(start: User) -> bool {
    w = start spawn FindAdmin();
    return w.found;
}
