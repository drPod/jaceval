from pathlib import Path

from harness.detectors import (
    DETECTORS,
    has_type_annotations,
    run_all,
    uses_abilities_on_nodes,
    uses_connect_op,
    uses_typed_edge_archetype,
    uses_visit,
    uses_walker,
)

IDIOMATIC = Path(__file__).parent / "fixtures" / "idiomatic"
PYISH = Path(__file__).parent / "fixtures" / "python_ish"


def test_uses_walker_positive():
    src = (IDIOMATIC / "uses_walker.jac").read_text()
    assert uses_walker(src) is True


def test_uses_walker_negative():
    src = (PYISH / "uses_walker.jac").read_text()
    assert uses_walker(src) is False


def test_uses_visit_positive():
    src = (IDIOMATIC / "uses_visit.jac").read_text()
    assert uses_visit(src) is True


def test_uses_visit_negative():
    src = (PYISH / "uses_visit.jac").read_text()
    assert uses_visit(src) is False


def test_uses_typed_edge_archetype_positive():
    src = (IDIOMATIC / "uses_typed_edge_archetype.jac").read_text()
    assert uses_typed_edge_archetype(src) is True


def test_uses_typed_edge_archetype_negative():
    src = (PYISH / "uses_typed_edge_archetype.jac").read_text()
    assert uses_typed_edge_archetype(src) is False


def test_uses_connect_op_positive():
    src = (IDIOMATIC / "uses_connect_op.jac").read_text()
    assert uses_connect_op(src) is True


def test_uses_connect_op_negative():
    src = (PYISH / "uses_connect_op.jac").read_text()
    assert uses_connect_op(src) is False


def test_has_type_annotations_positive():
    src = (IDIOMATIC / "has_type_annotations.jac").read_text()
    assert has_type_annotations(src) is True


def test_has_type_annotations_negative():
    src = (PYISH / "has_type_annotations.jac").read_text()
    assert has_type_annotations(src) is False


def test_has_type_annotations_vacuously_true_on_empty():
    assert has_type_annotations("") is True


def test_uses_abilities_on_nodes_positive():
    src = (IDIOMATIC / "uses_abilities_on_nodes.jac").read_text()
    assert uses_abilities_on_nodes(src) is True


def test_uses_abilities_on_nodes_negative():
    src = (PYISH / "uses_abilities_on_nodes.jac").read_text()
    assert uses_abilities_on_nodes(src) is False


def test_run_all_registers_every_detector():
    assert set(DETECTORS.keys()) == {
        "uses_walker",
        "uses_visit",
        "uses_typed_edge_archetype",
        "uses_connect_op",
        "has_type_annotations",
        "uses_abilities_on_nodes",
    }


def test_run_all_without_expected_returns_mean_over_all():
    src = (IDIOMATIC / "uses_walker.jac").read_text()
    out = run_all(src)
    assert set(out["per_detector"].keys()) == set(DETECTORS.keys())
    # uses_walker.jac triggers uses_walker, uses_visit, uses_connect_op, and
    # (vacuously) has_type_annotations — 4/6.
    assert out["ast_subscore"] == 4 / 6


def test_run_all_with_expected_filters_to_expected_only():
    src = (IDIOMATIC / "uses_walker.jac").read_text()
    out = run_all(src, expected=["uses_walker"])
    assert out["ast_subscore"] == 1.0


def test_run_all_with_expected_mixed_hits_and_misses():
    src = (IDIOMATIC / "uses_walker.jac").read_text()
    # uses_walker hits; uses_abilities_on_nodes misses (walker-side only here).
    out = run_all(src, expected=["uses_walker", "uses_abilities_on_nodes"])
    assert out["ast_subscore"] == 0.5


def test_run_all_with_unknown_expected_name_ignored():
    src = (IDIOMATIC / "uses_walker.jac").read_text()
    out = run_all(src, expected=["uses_walker", "not_a_detector"])
    # Unknown name dropped silently; only uses_walker applies.
    assert out["ast_subscore"] == 1.0


def test_run_all_with_empty_applicable_returns_zero():
    out = run_all("", expected=["not_a_detector"])
    assert out["ast_subscore"] == 0.0
