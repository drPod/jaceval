"""Run the judge on the 15 hand-labeled snippets, compute Cohen's κ, and gate at 0.4.

Usage:
    .venv/bin/python scripts/validate_judge.py

Exits non-zero if κ < 0.4 so CI / Makefile can fail fast.
"""
import json
import sys
from pathlib import Path

from harness.judge import judge_median
from harness.stats import cohen_kappa

VAL = Path("judge/validation")
SNIPPETS = VAL / "snippets"
HAND_LABELS = VAL / "hand_labels.jsonl"

# Minimal task-free rubric used for validation-corpus snippets, since they are
# not tied to any single eval task.
GENERIC_RUBRIC = (
    "Score the snippet on Jac idiomaticity 1-5. "
    "5 = uses nodes/edges/walkers/visit/abilities where applicable, type annotations present, no Python smells. "
    "1 = not Jac or fully Python-transliterated."
)

KAPPA_GATE = 0.4


def main() -> int:
    if not HAND_LABELS.exists():
        print(f"FATAL: {HAND_LABELS} missing. Run Task 34 first.", file=sys.stderr)
        return 2

    rows = [json.loads(ln) for ln in HAND_LABELS.read_text().splitlines() if ln.strip()]
    hand: list[int] = []
    model: list[int] = []

    for row in rows:
        snippet_path = SNIPPETS / row["file"]
        if not snippet_path.exists():
            print(f"FATAL: {snippet_path} missing but referenced in hand_labels.jsonl", file=sys.stderr)
            return 2
        candidate = snippet_path.read_text()
        out = judge_median(
            task_rubric=GENERIC_RUBRIC,
            reference_solution="(none)",
            candidate_code=candidate,
        )
        hand.append(row["label"])
        model.append(out["median"])
        print(f"{row['file']}: hand={row['label']}  judge_median={out['median']}  runs={out['scores']}")

    k = cohen_kappa(hand, model)
    print(f"\nCohen's κ = {k:.3f}   (target ≥ {KAPPA_GATE})")

    if k < KAPPA_GATE:
        print("JUDGE FAILED VALIDATION. Iterate judge/prompt.md and re-run.")
        return 1

    print("JUDGE VALIDATED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
