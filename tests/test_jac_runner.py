from pathlib import Path
from harness.jac_runner import run_jac_file, RunResult

FIXTURES = Path(__file__).parent / "fixtures"


def test_run_hello_returns_stdout():
    result = run_jac_file(FIXTURES / "hello.jac", timeout_s=10)
    assert isinstance(result, RunResult)
    assert result.exit_code == 0
    assert "hello" in result.stdout
    assert result.timed_out is False


def test_run_timeout_marks_timed_out():
    result = run_jac_file(FIXTURES / "forever.jac", timeout_s=2)
    assert result.timed_out is True
    assert result.exit_code == -1
    assert result.elapsed_ms >= 2000
    assert result.elapsed_ms < 5000  # sanity upper bound
