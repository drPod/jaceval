from harness.stats import cohen_kappa


def test_cohen_kappa_perfect_agreement():
    assert cohen_kappa([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]) == 1.0


def test_cohen_kappa_disagreement():
    k = cohen_kappa([1, 1, 1, 1, 1], [5, 5, 5, 5, 5])
    assert k <= 0.0


def test_cohen_kappa_mixed():
    # 3 agree, 2 disagree
    k = cohen_kappa([1, 2, 3, 4, 5], [1, 2, 3, 5, 4])
    assert 0.0 < k < 1.0
