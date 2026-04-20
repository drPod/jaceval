"""Tests for the walker/08 has-admin-reachable task."""

import from solution { User, has_admin_reachable }

test "start is itself an admin" {
    alice = User(name="Alice", is_admin=True);
    assert has_admin_reachable(alice);
}

test "no admins anywhere in the reachable subgraph" {
    bob = User(name="Bob", is_admin=False);
    carol = User(name="Carol", is_admin=False);
    bob ++> carol;
    assert not has_admin_reachable(bob);
}

test "admin reachable via a multi-hop chain" {
    u1 = User(name="U1", is_admin=False);
    u2 = User(name="U2", is_admin=False);
    u3 = User(name="U3", is_admin=False);
    admin = User(name="Admin", is_admin=True);
    u1 ++> u2;
    u2 ++> u3;
    u3 ++> admin;
    assert has_admin_reachable(u1);
}

test "cycle with no admin terminates and returns false" {
    x = User(name="X", is_admin=False);
    y = User(name="Y", is_admin=False);
    x ++> y;
    y ++> x;
    assert not has_admin_reachable(x);
}

test "admin on only one branch of a fork is still found" {
    root_user = User(name="Root", is_admin=False);
    dead_end = User(name="DeadEnd", is_admin=False);
    chain_mid = User(name="ChainMid", is_admin=False);
    admin = User(name="Admin", is_admin=True);
    root_user ++> dead_end;
    root_user ++> chain_mid;
    chain_mid ++> admin;
    assert has_admin_reachable(root_user);
}
