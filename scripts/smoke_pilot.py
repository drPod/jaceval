#!/usr/bin/env python3
"""One-shot: run Haiku on the pilot task, execute, print pass/fail."""

from pathlib import Path
import tempfile
import shutil
import sys

from harness.prompts import build_prompt
from harness.generators import generate
from harness.jac_runner import run_jac_tests

TASK_DIR = Path("tasks/pilot/pilot-fibonacci")
prompt_text = (TASK_DIR / "prompt.md").read_text()

full_prompt = build_prompt(arm="", task=prompt_text)
g = generate(model="claude-haiku-4-5", prompt=full_prompt, temperature=0.2, max_tokens=1024, seed=0)
print("---completion---")
print(g.completion)
print("---end---")

with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    (td / "solution.jac").write_text(g.completion)
    shutil.copy(TASK_DIR / "tests.jac", td / "tests.jac")
    result = run_jac_tests(td / "tests.jac", timeout_s=30)
    print(f"all_passed={result.all_passed} n_passed={result.n_passed} n_failed={result.n_failed}")
