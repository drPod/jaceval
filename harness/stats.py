"""Statistical utilities for jaceval.

- Cohen's κ — judge-vs-hand-label agreement (Task 35 seed).
- Chen (2021) unbiased pass@k — correctness aggregation across K samples.
- McNemar exact — paired binary flip test (e.g. SKILL vs no-skill on same task).
- Paired bootstrap — 95% CI on mean Δ between two paired arms.
- Wilson interval — small-n binomial confidence interval.
"""
from __future__ import annotations

import random
from collections import Counter
from math import comb, sqrt


def cohen_kappa(labels_a: list[int], labels_b: list[int]) -> float:
    """Cohen's κ between two rating sequences over the same items.

    κ = (p_o − p_e) / (1 − p_e), where p_o is observed agreement and p_e is
    expected agreement by chance given the marginal distributions. Returns
    1.0 for perfect agreement, 0.0 for chance-level, and negative values for
    systematic disagreement.
    """

    assert len(labels_a) == len(labels_b) and len(labels_a) > 0
    n = len(labels_a)
    cats = sorted(set(labels_a) | set(labels_b))
    agree = sum(1 for a, b in zip(labels_a, labels_b) if a == b) / n
    pa = Counter(labels_a)
    pb = Counter(labels_b)
    expected = sum((pa[c] / n) * (pb[c] / n) for c in cats)
    if expected == 1.0:
        return 1.0
    return (agree - expected) / (1 - expected)


def pass_at_k(*, n: int, c: int, k: int) -> float:
    """Chen et al. 2021 unbiased estimator: pass@k = 1 − C(n−c, k) / C(n, k).

    ``n`` samples, ``c`` of which pass. Returns 1.0 when n−c < k (all k-subsets
    must include at least one passing sample) and 0.0 when c = 0.
    """
    assert 0 <= c <= n and 1 <= k <= n
    if n - c < k:
        return 1.0
    return 1.0 - comb(n - c, k) / comb(n, k)


def mcnemar_exact(*, a_wins: int, b_wins: int) -> float:
    """Two-sided exact McNemar p-value on discordant paired binary outcomes.

    ``a_wins`` is the count of pairs where arm A passed and arm B failed;
    ``b_wins`` is the reverse. Concordant pairs (both pass or both fail) are
    ignored. Returns 1.0 when there are no discordant pairs.
    """
    n = a_wins + b_wins
    if n == 0:
        return 1.0
    k = min(a_wins, b_wins)
    tail = sum(comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def paired_bootstrap_mean(
    a: list[float],
    b: list[float],
    *,
    n_boot: int = 10_000,
    seed: int = 0,
    alpha: float = 0.05,
) -> tuple[float, float]:
    """95% bootstrap CI on the mean of pairwise differences a_i − b_i.

    ``a`` and ``b`` must be same-length paired samples (e.g. same task under two
    arms). Resamples ``n_boot`` times with replacement and returns the
    (α/2, 1−α/2) percentile interval.
    """
    assert len(a) == len(b) and len(a) > 0
    rng = random.Random(seed)
    diffs = [ai - bi for ai, bi in zip(a, b)]
    n = len(diffs)
    boots: list[float] = []
    for _ in range(n_boot):
        sample = [diffs[rng.randrange(n)] for _ in range(n)]
        boots.append(sum(sample) / n)
    boots.sort()
    lo = boots[int((alpha / 2) * n_boot)]
    hi = boots[int((1 - alpha / 2) * n_boot) - 1]
    return lo, hi


def wilson_interval(
    *,
    successes: int,
    trials: int,
    z: float = 1.96,
) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion. Better than CLT for small n.

    ``z`` defaults to 1.96 for a 95% two-sided interval.
    """
    if trials == 0:
        return 0.0, 1.0
    p = successes / trials
    denom = 1 + z ** 2 / trials
    center = (p + z ** 2 / (2 * trials)) / denom
    margin = z * sqrt((p * (1 - p) + z ** 2 / (4 * trials)) / trials) / denom
    return max(0.0, center - margin), min(1.0, center + margin)
