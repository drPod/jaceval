"""Statistical utilities for jaceval. Task 35 seeds this with Cohen's κ only;
the rest (unbiased pass@k, McNemar, paired bootstrap, Wilson) lands in Task 37.
"""
from __future__ import annotations

from collections import Counter


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
