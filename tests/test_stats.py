from harness.stats import (
    cohen_kappa,
    mcnemar_exact,
    paired_bootstrap_mean,
    pass_at_k,
    wilson_interval,
)


def test_cohen_kappa_perfect_agreement():
    assert cohen_kappa([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]) == 1.0


def test_cohen_kappa_disagreement():
    k = cohen_kappa([1, 1, 1, 1, 1], [5, 5, 5, 5, 5])
    assert k <= 0.0


def test_cohen_kappa_mixed():
    # 3 agree, 2 disagree
    k = cohen_kappa([1, 2, 3, 4, 5], [1, 2, 3, 5, 4])
    assert 0.0 < k < 1.0


def test_pass_at_k_unbiased():
    # n=5, c=3, k=1: 1 - C(2,1)/C(5,1) = 1 - 2/5 = 0.6
    assert abs(pass_at_k(n=5, c=3, k=1) - 0.6) < 1e-9
    # All pass → 1.0
    assert pass_at_k(n=5, c=5, k=5) == 1.0
    # None pass → 0.0
    assert pass_at_k(n=5, c=0, k=1) == 0.0
    # pass@5 with c=1: 1 - C(4,5)/C(5,5)... C(4,5)=0, so 1.0
    assert pass_at_k(n=5, c=1, k=5) == 1.0


def test_mcnemar_exact_trivial():
    # No flips → p = 1
    assert mcnemar_exact(a_wins=0, b_wins=0) == 1.0
    # All flips one way → p very small
    assert mcnemar_exact(a_wins=10, b_wins=0) < 0.01
    # Balanced flips → p = 1 (max uncertainty)
    assert abs(mcnemar_exact(a_wins=5, b_wins=5) - 1.0) < 1e-9


def test_paired_bootstrap_mean_identical_arms_contains_zero():
    a = [0.5] * 20
    b = [0.5] * 20
    lo, hi = paired_bootstrap_mean(a, b, n_boot=500, seed=42)
    assert lo <= 0.0 <= hi


def test_paired_bootstrap_mean_positive_delta_excludes_zero():
    a = [0.8] * 20
    b = [0.2] * 20
    lo, hi = paired_bootstrap_mean(a, b, n_boot=500, seed=42)
    assert lo > 0.0


def test_wilson_interval():
    lo, hi = wilson_interval(successes=5, trials=10, z=1.96)
    assert 0.0 <= lo < 0.5 < hi <= 1.0


def test_wilson_interval_edge_cases():
    # 0/10 → lower bound 0, upper bound strictly < 1
    lo, hi = wilson_interval(successes=0, trials=10)
    assert lo == 0.0 and 0.0 < hi < 1.0
    # 10/10 → lower bound > 0, upper bound 1
    lo, hi = wilson_interval(successes=10, trials=10)
    assert 0.0 < lo < 1.0 and hi == 1.0
    # trials=0 → full [0, 1]
    assert wilson_interval(successes=0, trials=0) == (0.0, 1.0)
