from harness.scorer import idiom_score


def test_idiom_score_weights_correctly():
    # AST 1.0, judge 5 -> 0.4*1.0 + 0.6*(5/5) = 1.0
    assert abs(idiom_score(ast_subscore=1.0, judge_median=5) - 1.0) < 1e-9
    # AST 0.0, judge 1 -> 0.4*0 + 0.6*(1/5) = 0.12
    assert abs(idiom_score(ast_subscore=0.0, judge_median=1) - 0.12) < 1e-9
    # AST 0.5, judge 3 -> 0.4*0.5 + 0.6*(3/5) = 0.2 + 0.36 = 0.56
    assert abs(idiom_score(ast_subscore=0.5, judge_median=3) - 0.56) < 1e-9


def test_idiom_score_rejects_out_of_range_ast():
    import pytest

    with pytest.raises(AssertionError):
        idiom_score(ast_subscore=1.1, judge_median=5)
    with pytest.raises(AssertionError):
        idiom_score(ast_subscore=-0.1, judge_median=5)


def test_idiom_score_rejects_out_of_range_judge():
    import pytest

    with pytest.raises(AssertionError):
        idiom_score(ast_subscore=0.5, judge_median=0)
    with pytest.raises(AssertionError):
        idiom_score(ast_subscore=0.5, judge_median=6)
