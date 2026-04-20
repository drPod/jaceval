from __future__ import annotations

import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RunResult:
    exit_code: int
    stdout: str
    stderr: str
    elapsed_ms: int
    timed_out: bool


def run_jac_file(path: Path | str, timeout_s: int = 30) -> RunResult:
    start = time.monotonic()
    try:
        proc = subprocess.run(
            ["jac", "run", str(path)],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return RunResult(
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            elapsed_ms=elapsed_ms,
            timed_out=False,
        )
    except subprocess.TimeoutExpired as e:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return RunResult(
            exit_code=-1,
            stdout=(e.stdout or b"").decode("utf-8", errors="replace")
            if isinstance(e.stdout, bytes)
            else (e.stdout or ""),
            stderr=(e.stderr or b"").decode("utf-8", errors="replace")
            if isinstance(e.stderr, bytes)
            else (e.stderr or ""),
            elapsed_ms=elapsed_ms,
            timed_out=True,
        )


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------
# Jac routes the unittest summary to stderr. The two patterns we match:
#   "Ran N test(s) in Xs"  -- total count
#   "FAILED (failures=N)"  -- failure count (absent means 0 failures / OK)
# Captured verbatim from Jac 0.x output against real .jac test fixtures.
# ---------------------------------------------------------------------------

_RAN_RE = re.compile(r"Ran\s+(\d+)\s+tests?", re.IGNORECASE)
_FAILED_RE = re.compile(r"FAILED\s*\(failures=(\d+)\)", re.IGNORECASE)


def _parse_test_counts(text: str) -> tuple[int, int]:
    """Return (n_passed, n_failed) by parsing unittest-style summary text."""
    ran_m = _RAN_RE.search(text)
    fail_m = _FAILED_RE.search(text)
    total = int(ran_m.group(1)) if ran_m else None
    n_failed = int(fail_m.group(1)) if fail_m else 0
    n_passed = (total - n_failed) if total is not None else (0 if n_failed > 0 else 0)
    return n_passed, n_failed


@dataclass
class TestResult:
    all_passed: bool
    n_passed: int
    n_failed: int
    raw: RunResult


def run_jac_tests(path: Path | str, timeout_s: int = 30) -> TestResult:
    """Run ``jac test <path>`` and parse the pass/fail summary."""
    start = time.monotonic()
    try:
        proc = subprocess.run(
            ["jac", "test", str(path)],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        elapsed_ms = int((time.monotonic() - start) * 1000)
        timed_out = False
    except subprocess.TimeoutExpired as e:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        # Reconstruct a minimal proc-like namespace for RunResult.
        proc = type(  # type: ignore[assignment]
            "_Proc", (), {
                "returncode": -1,
                "stdout": (e.stdout or b"").decode("utf-8", errors="replace")
                          if isinstance(e.stdout, bytes) else (e.stdout or ""),
                "stderr": (e.stderr or b"").decode("utf-8", errors="replace")
                          if isinstance(e.stderr, bytes) else (e.stderr or ""),
            }
        )()
        timed_out = True

    raw = RunResult(
        exit_code=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        elapsed_ms=elapsed_ms,
        timed_out=timed_out,
    )

    if timed_out:
        return TestResult(all_passed=False, n_passed=0, n_failed=1, raw=raw)

    # jac routes the unittest summary to stderr; search both just in case.
    combined = proc.stdout + "\n" + proc.stderr
    n_passed, n_failed = _parse_test_counts(combined)

    # If parsing found nothing, fall back to exit-code heuristic.
    if n_passed == 0 and n_failed == 0:
        if proc.returncode == 0:
            n_passed = 1
        else:
            n_failed = 1

    return TestResult(
        all_passed=(n_failed == 0 and proc.returncode == 0),
        n_passed=n_passed,
        n_failed=n_failed,
        raw=raw,
    )
