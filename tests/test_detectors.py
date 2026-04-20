from pathlib import Path

from harness.detectors import uses_walker

IDIOMATIC = Path(__file__).parent / "fixtures" / "idiomatic"
PYISH = Path(__file__).parent / "fixtures" / "python_ish"


def test_uses_walker_positive():
    src = (IDIOMATIC / "uses_walker.jac").read_text()
    assert uses_walker(src) is True


def test_uses_walker_negative():
    src = (PYISH / "uses_walker.jac").read_text()
    assert uses_walker(src) is False
