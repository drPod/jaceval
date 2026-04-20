# v0-skill provenance

Authored 2026-04-20 from `docs/findings/jac-pitfalls.md` during Phase 11 of
jaceval v0.

- Word count: 2,761.
- Source corpus: 21 empirically-logged pitfalls across Statements/control flow,
  Test blocks, Object/archetype syntax, Cross-file imports, Graph (OSP)
  semantics, Walkers/traversal, Runtime/filesystem, and Comment syntax in
  `docs/findings/jac-pitfalls.md`, plus one **new** pitfall discovered during
  authoring (no `let` keyword in Jac — confirmed by `validate_jac`; see the
  report's Findings section).
- Coverage: 19 of 21 logged pitfalls plus the newly-discovered `let` pitfall
  represented as explicit rules, code examples, or WRONG-vs-RIGHT pairs in
  the arm. Two logged pitfalls excluded because they are harness/probe
  concerns (not code-writing rules the generator can act on): `jac test`
  output parsing and `jac run` cross-run graph-state persistence.
- Structure: 10 numbered sections plus a final cheatsheet. Surface syntax
  first, then archetypes, control flow, imports, tests, graphs, walkers,
  walker-vs-node polarity, cheatsheet, and a closing meta rule. Progressive
  disclosure: the rules models fail on most often (braces, semicolons,
  comment syntax, `pass`, `True/False`) appear first.
- WRONG/RIGHT pairs: approximately 25 across the document (well above the
  15–20 target from the dispatch spec).
- First eval run: pending (Day 10 of the v0 timeline, per
  `docs/specs/2026-04-19-jaceval-v0-design.md` §5.1).
