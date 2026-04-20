# Search a user graph for a reachable admin

Write a Jac module that models a directed "follows" graph of users, where each user carries a name and a boolean admin flag, and reports whether any admin user is reachable from a given starting user.

Define one vertex type:

- `User` with two typed fields: `name: str` and `is_admin: bool`.

A link from user `u` to user `v` means `u` follows `v`. Links are one-directional. A graph may mix admin and non-admin users freely, and cycles are allowed.

Expose one function with this signature:

    def has_admin_reachable(start: User) -> bool

The function takes one starting user and returns `True` if there is at least one admin user reachable from `start` by following outgoing links zero or more times (**including `start` itself if `start` is an admin**), and `False` otherwise. It must stop searching as soon as the first admin is found — the implementation should not exhaustively explore the whole reachable subgraph once an admin has been identified.

The graph may contain cycles, so the implementation must avoid re-examining users it has already examined.

Examples:

    # A single admin user, no outgoing links.
    alice = User(name="Alice", is_admin=True);
    has_admin_reachable(alice)                       # -> True

    # Non-admin starts, non-admin intermediate, admin at depth 2.
    bob = User(name="Bob", is_admin=False);
    carol = User(name="Carol", is_admin=False);
    root_admin = User(name="Dana", is_admin=True);
    bob --follows--> carol --follows--> root_admin;
    has_admin_reachable(bob)                         # -> True

    # A 2-cycle of non-admins, no admin anywhere reachable.
    x = User(name="X", is_admin=False);
    y = User(name="Y", is_admin=False);
    x --follows--> y; y --follows--> x;
    has_admin_reachable(x)                           # -> False

Write `User` and `has_admin_reachable` in a single file. Do not print anything; just define them.

Output raw Jac source only. No Markdown, no ``` fences, no commentary.
