"""Python-transliterated: `node` archetype is shaped like a Python class — traversal is done by recursing through `[-->]` via a regular method on the node, no walker, no visit, no abilities."""

node TreeNode {
    has label: str;
    has count: int = 0;

    def traverse(seen: set[str]) -> int {
        vid = jid(self);
        if vid in seen {
            return 0;
        }
        seen.add(vid);
        total: int = 1;
        children: list[TreeNode] = [self -->];
        for child in children {
            total += child.traverse(seen);
        }
        return total;
    }
}

def count_tree(start: TreeNode) -> int {
    seen: set[str] = set();
    return start.traverse(seen);
}
