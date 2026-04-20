from pathlib import Path
from harness.jac_runner import run_jac_file, RunResult, run_jac_tests

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


# ---------------------------------------------------------------------------
# run_jac_tests — verbatim output fixtures (captured from Jac 0.x)
# Jac routes unittest summary to stderr; stdout carries "Passed successfully."
# on success and is empty on failure.
# Passing verbatim:  stderr = ".\n---...---\nRan 1 test in 0.000s\n\nOK\n"
# Failing verbatim:  stderr = "F\n===...===\nFAIL:...\nRan 1 test in 0.000s\n\nFAILED (failures=1)\n✖ Error: Tests failed: 1\n"
# ---------------------------------------------------------------------------

_PASSING_STDERR = (
    ".\n"
    "----------------------------------------------------------------------\n"
    "Ran 1 test in 0.000s\n"
    "\n"
    "OK\n"
)

_FAILING_STDERR = (
    "F\n"
    "======================================================================\n"
    "FAIL: unittest.case.FunctionTestCase (test_addition_is_wrong_on_purpose)\n"
    "----------------------------------------------------------------------\n"
    "AssertionError: 5 != 999\n"
    "\n"
    "----------------------------------------------------------------------\n"
    "Ran 1 test in 0.000s\n"
    "\n"
    "FAILED (failures=1)\n"
    "\u2716 Error: Tests failed: 1\n"
)


def test_regex_matches_passing_verbatim():
    """_parse_test_counts must handle the exact stderr Jac 0.x emits on success."""
    from harness.jac_runner import _parse_test_counts

    n_passed, n_failed = _parse_test_counts(_PASSING_STDERR)
    assert n_passed == 1
    assert n_failed == 0


def test_regex_matches_failing_verbatim():
    """_TEST_SUMMARY_RE must match the exact stderr Jac 0.x emits on failure."""
    from harness.jac_runner import _parse_test_counts

    n_passed, n_failed = _parse_test_counts(_FAILING_STDERR)
    assert n_passed == 0
    assert n_failed == 1


def test_run_tests_passing():
    result = run_jac_tests(FIXTURES / "has_passing_test.jac")
    assert result.all_passed is True
    assert result.n_passed >= 1
    assert result.n_failed == 0


def test_run_tests_failing():
    result = run_jac_tests(FIXTURES / "has_failing_test.jac")
    assert result.all_passed is False
    assert result.n_failed >= 1
