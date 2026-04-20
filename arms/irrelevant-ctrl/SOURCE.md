# irrelevant-ctrl provenance

Authored 2026-04-20 as the length-matched null control for jaceval v0. The
content is a real Gleam language reference, pulled from Gleam's public
documentation. Its purpose is to test the "more tokens help" null
hypothesis: any improvement over `no-skill` attributable purely to the
arm's length rather than its Jac content would also appear here.

- Word count: 2,818.
- Length-match to `arms/v0-skill/arm.md` (2,761 words): 102.1% — within the
  ±5% target from the dispatch spec.
- Rationale: Gleam is a statically-typed functional language compiling to
  Erlang/JavaScript. It shares Jac's "niche, typed, compiled" flavor but is
  entirely unrelated syntactically. If this arm improves Jac generation,
  the effect is token-count, not Jac-specific teaching.

## Sources

Content sourced from Gleam's public documentation and tour pages:

- https://tour.gleam.run/ — the interactive language tour overview.
- https://tour.gleam.run/everything/ — the single-page aggregate of every
  tour section. Primary source for syntax, types, functions, pattern
  matching, custom types, and advanced features.
- https://gleam.run/cheatsheets/gleam-for-python-users/ — the Gleam-for-Python
  cheatsheet. Primary source for the section-by-section syntax surface.
- https://gleam.run/documentation/ — the documentation index; used for
  cross-checking tool, project-layout, and standard-library references.

Gleam's documentation voice and structure have been preserved rather than
rewritten in the style of `v0-skill/arm.md` — the two arms should read as
genuinely different language references of similar length.
