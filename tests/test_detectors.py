from pathlib import Path

from harness.detectors import (
    has_type_annotations,
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
