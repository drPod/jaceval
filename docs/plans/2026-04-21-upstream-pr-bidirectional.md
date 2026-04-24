# Upstream PR handoff: fix `<++>` bidirectional wording

**Target repo:** `jaseci-labs/jaseci` (Jason Mars's flagship Jac repo, not `jaseci-llmdocs`).
**Branch from:** latest `main`.
**Scope:** one PR, four file edits + one release-note fragment + one runtime-probe verification.

## Why this PR exists

`jac-llmdocs.md` (v0.12.1 pinned in `arms/llmdocs/`) documents `a <++> b` as "Bidirectional" / "Undirected: creates edges both ways." Pitfall finding logged at `docs/findings/jac-pitfalls.md` § *"Bidirectional" connect is NOT symmetric storage* showed the runtime stores a single directed edge — confirmed via probe 2026-04-20 on Jac 0.13.5 / jaclang 0.14.0.

Investigation 2026-04-21 (logged in `docs/journal/research-log.md`) traced the wrong wording:

- `jaseci-llmdocs/release/jac-llmdocs.md` is **auto-generated** by an LLM-assembly pipeline (Claude Opus 4.6 at `temperature=0.0, seed=42`). A PR against that repo would be overwritten on the next regeneration.
- The "Bidirectional" label is inherited verbatim from **upstream canonical docs at `jaseci-labs/jaseci`**, path `docs/docs/`. The llmdocs prompt-rules file (`config/rag_rules.txt`) never mentions `<++>` — the pipeline is faithfully propagating an upstream doc bug.

The real fix goes upstream. The four locations below all need correcting in one PR so the generated llmdocs regenerates cleanly next cycle.

## Pre-flight — MANDATORY before editing

Re-confirm the pitfall still holds on whatever `jac` version is installed locally. The original probe was on 0.13.5 / 0.14.0 in April 2026; if the runtime has since changed to actually create two directed edges, this PR becomes moot (docs would be right, runtime would be right, no bug).

Run from a clean empty dir:

```bash
mkdir /tmp/bidir-probe && cd /tmp/bidir-probe
cat > probe.jac <<'EOF'
node N {}

with entry {
    a = N();
    b = N();
    a <++> b;
    print("from a:", [a -->]);
    print("from b:", [b -->]);
    print("either from a:", [a <-->]);
    print("either from b:", [b <-->]);
}
EOF
rm -rf .jac* jac.lock __jac_gen__
jac run probe.jac
```

**Expected output if pitfall is still live:**
```
from a: [<N>]     ← a has an outgoing edge to b
from b: []        ← b has NO outgoing edge to a (single directed storage)
either from a: [<N>]
either from b: [<N>]  ← query-time symmetry via [<-->]
```

If `from b:` returns a non-empty list, `<++>` now creates two edges and the upstream docs are correct — **stop, do not open the PR, report back**. If `from b: []`, proceed.

Also record the jaclang version: `jac --version` — belongs in the PR body.

## The four file edits

All paths are relative to `jaseci-labs/jaseci` repo root. Clone with:

```bash
gh repo fork jaseci-labs/jaseci --clone --remote
cd jaseci
git checkout -b docs-fix-bidirectional-edge
```

### Edit 1: `docs/docs/reference/language/osp.md` — the strongest wrong claim

Current content (§ Edges.3, around the "Directed vs Undirected" heading):

```
### 3 Directed vs Undirected

Edge direction is determined by connection operators:

```jac
node Item {}

with entry {
    a = Item();
    b = Item();

    a ++> b;          # Directed: a → b
    a <++> b;         # Undirected: a ↔ b (creates edges both ways)
}
```

**Replace with:**

```
### 3 Edge Direction

Edges are always stored as directed. The connect operators differ in syntax, not in storage semantics — both create a single directed edge from the left node to the right node:

```jac
node Item {}

with entry {
    a = Item();
    b = Item();

    a ++> b;          # Creates directed edge a → b
    a <++> b;         # Also creates directed edge a → b (alternate syntax)
}
```

For bidirectional *traversal* — visiting or querying neighbors regardless of edge direction — use the `[<-->]` filter at query time. See [Walkers § 3](#the-visit-statement) and [Data Spatial Queries § 1](#edge-reference-syntax) for `[<-->]`.

**Rationale.** The rest of `osp.md` already treats `[<-->]` as a query-time direction-agnostic traversal (§ Walkers.3: `visit [<-->]; # Visit both directions`; § Data Spatial Queries.1: `both = [<-->]; # Both directions`). This correction aligns § Edges.3 with that framing instead of implying `<++>` does something at storage level that the rest of the doc doesn't confirm.

### Edit 2: `docs/docs/reference/language/osp.md` — Graph Construction comment

Current content (§ Graph Construction.2, inside the "Creating Edges" example):

```
    # Bidirectional typed
    alice <+: Colleague(department="Engineering") :+> bob;
```

**Replace with:**

```
    # Typed edge, alternate syntax (same storage: directed alice → bob)
    alice <+: Colleague(department="Engineering") :+> bob;
```

### Edit 3: `docs/docs/quick-guide/syntax-cheatsheet.md`

Current content (Connection Operators section of the "Learn Jac in Y Minutes" code block):

```
a <++> b;               # Bidirectional a <-> b
```

**Replace with:**

```
a <++> b;               # Also creates a → b (use [<-->] to query both directions)
```

### Edit 4: `docs/docs/reference/language/foundation.md`

Current content (Graph Operators (OSP) → Connection Operators):

```
node1 <++> node2;        # Bidirectional
```

**Replace with:**

```
node1 <++> node2;        # Also creates directed node1 → node2 (use [<-->] for direction-agnostic traversal)
```

## Release-note fragment

Jaseci's `CONTRIBUTING.md` requires a fragment at:

```
docs/docs/community/release_notes/unreleased/jaclang/<PR#>.docs.md
```

You won't know `<PR#>` until after opening the PR. Workflow: push the branch, open the PR, note the PR number, add the fragment file in a follow-up commit on the same branch (GitHub auto-updates the PR).

**Fragment content:**

```markdown
Documentation: clarified that `<++>` creates a single directed edge (not two edges / not an undirected edge). Bidirectional traversal is a query-time affordance via `[<-->]`. Fixes mismatch between Edges § 3 and the Walkers / Data Spatial Queries sections, which already treat `[<-->]` as direction-agnostic at query time.
```

## PR title and body

**Title:**
```
docs: clarify that `<++>` creates a directed edge; bidirectional traversal is query-time only
```

**Body:**

```markdown
## Problem

`docs/` documents `<++>` as creating a bidirectional / undirected edge ("creates edges both ways"). Runtime stores a single directed edge from the left to the right operand. The discrepancy shows up in four places across three files:

- `docs/docs/reference/language/osp.md` § Edges.3 — "Undirected: a ↔ b (creates edges both ways)"
- `docs/docs/reference/language/osp.md` § Graph Construction.2 — comment "Bidirectional typed"
- `docs/docs/quick-guide/syntax-cheatsheet.md` — "Bidirectional a <-> b"
- `docs/docs/reference/language/foundation.md` § Graph Operators — "Bidirectional"

This is particularly impactful because these files are the source that `jaseci-labs/jaseci-llmdocs` LLM-assembles into `jac-llmdocs.md`, so the incorrect framing propagates to every LLM-facing artifact downstream.

## Evidence

Probe on Jac `<JAC_VERSION_FROM_PREFLIGHT>`:

```jac
node N {}
with entry {
    a = N();
    b = N();
    a <++> b;
    print("from a:", [a -->]);   # [<N>]
    print("from b:", [b -->]);   # []  ← no edge from b
    print("either from b:", [b <-->]);  # [<N>] ← query-time symmetry
}
```

If `<++>` created edges both ways, `[b -->]` would return `[<N>]`. It returns `[]`. The symmetry that `[b <-->]` returns is the *query filter* walking edges incident to `b` in either direction, not a second stored edge.

## Fix

Aligns the four doc locations with the framing already used in `osp.md`'s Walkers (§ 3) and Data Spatial Queries (§ 1) sections, both of which correctly describe `[<-->]` as a direction-agnostic traversal query. No semantic change — this is a consistency / accuracy correction within docs.

## Context

Discovered while building [`jaceval`](https://github.com/drPod/jaceval), a paired-A/B benchmark for LLM idiomaticity on niche languages. `<++>` was among 17 Jac pitfalls logged during v0 authorship; tracing the source of the wrong wording led here. Happy to file follow-up PRs for other findings if they'd be useful.
```

Replace `<JAC_VERSION_FROM_PREFLIGHT>` with whatever `jac --version` reports.

## Execution checklist

1. **Pre-flight probe** — run the probe script above on your local Jac. Record exit output and `jac --version`. If the probe shows two-edge storage, STOP and report back; otherwise proceed.
2. **Fork + branch** — `gh repo fork jaseci-labs/jaseci --clone --remote` then `git checkout -b docs-fix-bidirectional-edge`.
3. **Apply the four edits** — verbatim from this doc. Don't improvise wording; the phrasing is chosen to be minimal, align with existing `osp.md` framing, and avoid opening side debates.
4. **Commit** — `git add -A && git commit -m "docs: clarify <++> creates a directed edge; bidirectional traversal is query-time"`.
5. **Push + open PR** — `git push -u origin docs-fix-bidirectional-edge && gh pr create --title "docs: clarify \`<++>\` creates a directed edge; bidirectional traversal is query-time only" --body-file <path-to-body.md>`. Substitute the version string into the body before creating.
6. **Add release-note fragment** — once PR is open and you have the PR number, create `docs/docs/community/release_notes/unreleased/jaclang/<PR#>.docs.md` with the fragment content above. Commit and push.
7. **Report back** — PR URL + PR number. Controller will then (a) commit a jaceval-side record of the PR being open, (b) post to Discord.

## What NOT to do in this PR

- **Don't** file a separate PR against `jaseci-llmdocs` to fix the `.md` — it's bot-regenerated. Fixing upstream is the only fix that sticks.
- **Don't** propose changing the runtime behavior of `<++>` (i.e. "make it actually store two edges"). That's a language-design change, not a doc fix, and a separate conversation. This PR is scoped to docs-only.
- **Don't** bundle other pitfalls (walker dedupe, named tests, etc.) into this PR. Keep it one focused change. Follow-ups go in separate PRs so each can be reviewed and merged independently.
- **Don't** add emoji or decorative formatting to the PR body. Keep it sober and technical.
