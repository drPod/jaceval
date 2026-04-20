# Increment the view-count of every reachable post

Write a Jac module that models a directed graph of blog posts, where each post carries a title and a view counter, and increments the view counter of every post reachable from a given starting post.

Define one vertex type:

- `Post` with two typed fields: `title: str` and `views: int`, where `views` defaults to `0`.

A link from post `p` to post `q` means `q` is related to `p`. Links are one-directional and a graph may contain cycles.

Expose one function with this signature:

    def increment_views_reachable(start: Post) -> int

The function takes one starting post, traverses every post reachable from `start` by following outgoing links zero or more times (**including `start` itself**), increments each reachable post's `views` field by exactly `1`, and returns the total number of posts it incremented.

Each reachable post must be incremented **exactly once**, even when the graph contains cycles or when multiple paths lead to the same post.

Examples:

    # A single isolated post, no outgoing links.
    a = Post(title="A");
    increment_views_reachable(a)    # -> 1, and a.views is now 1

    # Chain: A --> B --> C, starting from A.
    # All three posts get views == 1. Returns 3.

    # 3-cycle: A --> B --> C --> A, starting from A.
    # All three posts get views == 1 (not 2, not infinite). Returns 3.

    # Fork: A --> B, A --> C, starting from A. Returns 3.

    # Two disconnected posts. Starting from one, the other's views stays at 0.

Write `Post` and `increment_views_reachable` in a single file. Do not print anything; just define them.

Output raw Jac source only. No Markdown, no ``` fences, no commentary.
