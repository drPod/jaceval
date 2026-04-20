from __future__ import annotations

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
