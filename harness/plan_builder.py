"""Build the full (arm × model × task × sample) cross-product run plan.

Each entry is a dict written as one line of `run_plan.jsonl`:

    {
      "group": "main" | "noise",
      "arm": "no-skill" | "llmdocs" | "v0-skill" | "irrelevant-ctrl",
      "model": "<ModelName>",
      "task_id": "01",
      "sample_idx": 0,
      "seed": <int>,
    }

The seed is a deterministic function of (arm, model, task_id, sample_idx, group),
so a re-run produces the same seeds as the original — necessary for reproducibility
and for the noise-floor comparison (same-arm-different-seed runs must be stable
across re-executions).

When ``noise_floor=True`` and ``no-skill`` is among the arms, a second group of
``no-skill`` entries is emitted with a distinct seed offset so that the orchestrator
and analysis can compare the two runs against each other. This operationalises the
no-op noise-floor control from the pre-registration.
"""
from __future__ import annotations

import hashlib
import itertools
from typing import Iterator


def _stable_seed(*parts: str | int, offset: int = 0) -> int:
    """Deterministic small int derived from the arguments. Uses MD5 because it's
    stable across Python processes (unlike ``hash()``) and we're not doing
    anything security-sensitive.
    """
    h = hashlib.md5("|".join(str(p) for p in parts).encode()).digest()
    return (int.from_bytes(h[:4], "big") + offset) % 1_000_000


def build_plan(
    *,
    arms: list[str],
    models: list[str],
    task_ids: list[str],
    n_samples: int,
    seed_base: int = 0,
    noise_floor: bool = False,
) -> Iterator[dict]:
    """Yield one dict per (arm, model, task, sample) combination. See module docstring."""

    groups: list[tuple[str, int]] = [("main", seed_base)]
    if noise_floor and "no-skill" in arms:
        groups.append(("noise", seed_base + 100_000))

    for group_name, seed_offset in groups:
        effective_arms = arms if group_name == "main" else ["no-skill"]
        for arm, model, task_id, i in itertools.product(
            effective_arms, models, task_ids, range(n_samples)
        ):
            yield {
                "group": group_name,
                "arm": arm,
                "model": model,
                "task_id": task_id,
                "sample_idx": i,
                "seed": _stable_seed(group_name, arm, model, task_id, i, offset=seed_offset),
            }
