"""Tests for the walker/09 increment-views-reachable task."""

import from solution { Post, increment_views_reachable }

test "single isolated post is incremented exactly once" {
    a = Post(title="A");
    n = increment_views_reachable(a);
    assert n == 1;
    assert a.views == 1;
}

test "chain of 3 posts: every post bumped exactly once" {
    a = Post(title="A");
    b = Post(title="B");
    c = Post(title="C");
    a ++> b;
    b ++> c;
    n = increment_views_reachable(a);
    assert n == 3;
    assert a.views == 1;
    assert b.views == 1;
    assert c.views == 1;
}

test "cycle is not visited twice: 3-cycle bumps each post exactly once" {
    a = Post(title="A");
    b = Post(title="B");
    c = Post(title="C");
    a ++> b;
    b ++> c;
    c ++> a;
    n = increment_views_reachable(a);
    assert n == 3;
    assert a.views == 1;
    assert b.views == 1;
    assert c.views == 1;
}

test "fork: one post with two outgoing neighbors, all three bumped once" {
    root_post = Post(title="R");
    left = Post(title="L");
    right = Post(title="Rt");
    root_post ++> left;
    root_post ++> right;
    n = increment_views_reachable(root_post);
    assert n == 3;
    assert root_post.views == 1;
    assert left.views == 1;
    assert right.views == 1;
}

test "disconnected post is not reached and keeps views at 0" {
    a = Post(title="A");
    b = Post(title="B");
    a ++> b;
    unreached = Post(title="U");
    n = increment_views_reachable(a);
    assert n == 2;
    assert a.views == 1;
    assert b.views == 1;
    assert unreached.views == 0;
}
