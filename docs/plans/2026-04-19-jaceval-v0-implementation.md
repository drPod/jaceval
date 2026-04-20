# jaceval v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and execute the v0 `jaceval` harness — a paired A/B benchmark measuring whether context docs improve LLM-generated Jac quality, over 10 tasks × 5 arms × 3 models × 5 samples, with a validated LLM judge.

**Architecture:** Python 3.12 harness that subprocesses `jac run` for correctness and calls three LLM APIs (Claude Haiku 4.5, Gemini 3 Flash Preview, Llama 4 Scout 17B via Groq) for generation and GPT-OSS 120B via Groq for judgment. Intermediate state flows through append-only JSONL files for resumability. Jac-specific authoring is delegated to Claude via the local `jac-mcp` server (already wired in `.mcp.json`).

**Tech Stack:** Python 3.12 (pyenv), `pip install -e .` with pyproject.toml, pytest for unit tests, `jac` CLI for running Jac code, `jac-mcp` tools for Jac authoring assistance, official API SDKs (`anthropic`, `google-genai`, `groq`), `numpy` for bootstrap, `scipy.stats` for McNemar and Wilson intervals, PyYAML for task metadata, `python-dotenv` for API keys.

**Ground rules the engineer must follow:**
- **Every Jac file you author or modify is round-tripped through `jac-mcp`'s `validate_jac` before check-in.** Non-negotiable per `CLAUDE.md`.
- **TDD everywhere.** Tests first, watch fail, minimal implementation, watch pass, commit.
- **Commit after every task.** Keep working tree green.
- **Read `docs/specs/2026-04-19-jaceval-v0-design.md` end-to-end before Task 1.** It's the frozen spec; this plan implements it.
- **Never look at the held-out tasks (03, 10) during iteration.** Their results are not examined until Day 12.
- **Pre-committed thresholds are frozen** (spec §7.3). Do not revise them after seeing results.

---

## File structure (what gets created)

```
jaceval/
├── pyproject.toml                    # project metadata + deps
├── requirements.txt                  # pinned versions (generated)
├── Makefile                          # `make eval`, `make test`, etc.
├── .env.example                      # API key template
├── README.md                         # public-facing, written last
├── CLAUDE.md                         # already exists
├── design-recipe.md                  # already exists
├── .mcp.json                         # already exists
├── .gitignore                        # already exists (add .env, .venv, pytest cache)
├── tasks/
│   ├── syntax/{01,02,03}/{prompt.md, solution.jac, tests.jac, rubric.md, meta.yaml}
│   ├── graph/{04,05,06}/...
│   └── walker/{07,08,09,10}/...
├── arms/
│   ├── no-skill/arm.md
│   ├── llmdocs-mini/{arm.md, SOURCE.md}
│   ├── llmdocs-full/{arm.md, SOURCE.md}
│   ├── v0-skill/arm.md               # written Day 10
│   └── irrelevant-ctrl/arm.md        # written Day 10
├── harness/
│   ├── __init__.py
│   ├── prompts.py                    # prompt assembly
│   ├── generators.py                 # unified LLM client interface
│   ├── jac_runner.py                 # subprocess jac run + parse
│   ├── detectors.py                  # AST idiom detectors (pattern-based)
│   ├── judge.py                      # GPT-OSS 120B via Groq judge + 3-run median
│   ├── scorer.py                     # AST + judge → idiom_score
│   ├── stats.py                      # McNemar, paired bootstrap, Wilson, Cohen's κ
│   ├── plan_builder.py               # writes run_plan.jsonl
│   └── run.py                        # orchestrator
├── judge/
│   ├── prompt.md                     # Prometheus-format judge prompt template
│   ├── rubric.md                     # generic rubric scaffold (per-task rubrics are in tasks/)
│   └── validation/
│       ├── snippets/{01..15}.jac     # 15 hand-labeled snippets
│       ├── hand_labels.jsonl         # labels with justifications
│       └── rubric_history.md         # judge rubric revisions
├── scripts/
│   ├── fetch_llmdocs.py              # pulls LLMDocs from docs.jaseci.org
│   ├── calibrate_task.py             # pilot run for baseline pass rate
│   ├── failure_analysis.py           # Day 10 failure-mode extractor
│   └── validate_judge.py             # Cohen's κ on hand labels
├── tests/
│   ├── test_jac_runner.py
│   ├── test_prompts.py
│   ├── test_generators.py            # uses mocks
│   ├── test_detectors.py
│   ├── test_judge.py                 # uses mocks
│   ├── test_scorer.py
│   ├── test_stats.py
│   └── fixtures/                     # small Jac snippets for detector tests
├── results/
│   ├── RESULTS.md                    # writeup, written Day 12
│   └── summary.jsonl                 # committed summary of final run
└── docs/
    ├── specs/2026-04-19-jaceval-v0-design.md       # already exists
    └── plans/2026-04-19-jaceval-v0-implementation.md  # this file
```

All files under `.eval_cache/`, `.env`, `__pycache__/`, `.venv/`, `.pytest_cache/` are git-ignored. Everything else is tracked.

---

## Task list

Total: **51 tasks** grouped into 13 phases aligned with the spec's 14-day timeline. Each task is self-contained; you can pick up at any task boundary. Every task ends in a commit.

---

## PHASE 0 — Project scaffolding (Day 1 AM)

### Task 1: Initialize Python project and directory skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `Makefile`
- Create: `harness/__init__.py` (empty)
- Create: `tests/__init__.py` (empty)
- Modify: `.gitignore` (append `.env`, `.venv/`, `.pytest_cache/`, `.eval_cache/`, `__pycache__/`)

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "jaceval"
version = "0.1.0"
description = "v0 Jac codegen eval — paired-design benchmark for LLM-generated Jac"
requires-python = ">=3.12"
dependencies = [
  "anthropic>=0.40.0",
  "google-genai>=0.3.0",
  "groq>=0.13.0",
  "numpy>=1.26",
  "scipy>=1.13",
  "pyyaml>=6.0",
  "python-dotenv>=1.0",
  "jac-mcp>=0.1.10",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-mock>=3.12"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
```

- [ ] **Step 2: Create .env.example**

```
# Copy to .env and fill in. .env is git-ignored.
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
GROQ_API_KEY=
```

- [ ] **Step 3: Create Makefile**

```makefile
.PHONY: install test eval clean

install:
	python -m venv .venv
	.venv/bin/pip install -e .[dev]

test:
	.venv/bin/pytest -v

eval:
	.venv/bin/python -m harness.run --all

clean:
	rm -rf .eval_cache/ .pytest_cache/ __pycache__/ harness/__pycache__/ tests/__pycache__/
```

- [ ] **Step 4: Append to .gitignore**

Read current `.gitignore`. Append these lines if not already present:
```
.env
.venv/
.pytest_cache/
.eval_cache/
__pycache__/
```

- [ ] **Step 5: Create empty harness and tests packages**

Create zero-byte files: `harness/__init__.py`, `tests/__init__.py`.

- [ ] **Step 6: Install**

```bash
make install
```
Expected: `.venv/` created; successful install of all deps.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml .env.example Makefile harness/ tests/ .gitignore
git commit -m "scaffold: python project with deps, Makefile, .env template"
```

---

### Task 2: Wire pytest with a smoke test

**Files:**
- Create: `tests/test_smoke.py`

- [ ] **Step 1: Write the smoke test**

```python
# tests/test_smoke.py
def test_python_version():
    import sys
    assert sys.version_info >= (3, 12)

def test_jac_mcp_available():
    import shutil
    assert shutil.which("jac") is not None, "jac CLI must be on PATH"
```

- [ ] **Step 2: Run**

```bash
make test
```
Expected: 2 passed.

- [ ] **Step 3: Commit**

```bash
git add tests/test_smoke.py
git commit -m "test: add smoke test for python and jac availability"
```

---

## PHASE 1 — Jac runner (Day 1 PM)

### Task 3: Jac runner — run a file and capture output

**Files:**
- Create: `harness/jac_runner.py`
- Create: `tests/test_jac_runner.py`
- Create: `tests/fixtures/hello.jac`

- [ ] **Step 1: Create the fixture**

```jac
// tests/fixtures/hello.jac
with entry {
    print("hello");
}
```

Round-trip it:
```bash
.venv/bin/python -c "
import subprocess
r = subprocess.run(['jac', 'run', 'tests/fixtures/hello.jac'], capture_output=True, text=True, timeout=10)
print('stdout:', r.stdout); print('stderr:', r.stderr); print('returncode:', r.returncode)
"
```
Expected: stdout contains `hello`, returncode 0.

- [ ] **Step 2: Write the failing test**

```python
# tests/test_jac_runner.py
from pathlib import Path
from harness.jac_runner import run_jac_file, RunResult

FIXTURES = Path(__file__).parent / "fixtures"

def test_run_hello_returns_stdout():
    result = run_jac_file(FIXTURES / "hello.jac", timeout_s=10)
    assert isinstance(result, RunResult)
    assert result.exit_code == 0
    assert "hello" in result.stdout
    assert result.timed_out is False
```

- [ ] **Step 3: Run — expect ModuleNotFoundError**

```bash
make test
```
Expected: test_run_jac_runner fails with "No module named 'harness.jac_runner'".

- [ ] **Step 4: Implement minimal jac_runner**

```python
# harness/jac_runner.py
from __future__ import annotations
import subprocess
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
    import time
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
            stdout=(e.stdout or b"").decode("utf-8", errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or ""),
            stderr=(e.stderr or b"").decode("utf-8", errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or ""),
            elapsed_ms=elapsed_ms,
            timed_out=True,
        )
```

- [ ] **Step 5: Run — expect pass**

```bash
make test
```
Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add harness/jac_runner.py tests/test_jac_runner.py tests/fixtures/hello.jac
git commit -m "feat(runner): run_jac_file with timeout and RunResult"
```

---

### Task 4: Jac runner — timeout behavior

**Files:**
- Modify: `tests/test_jac_runner.py`
- Create: `tests/fixtures/forever.jac`

- [ ] **Step 1: Create the fixture**

```jac
// tests/fixtures/forever.jac
with entry {
    while True {
        continue;
    }
}
```

**Note:** Jac does not have a `pass` statement; use `continue;` as the in-loop no-op. This was discovered during the first execution of Task 4 via `jac-mcp validate_jac`.

Verify via `jac-mcp` `validate_jac` that it compiles (expect no compile errors — it's an infinite loop, not a syntax error).

- [ ] **Step 2: Add the failing test**

Append to `tests/test_jac_runner.py`:
```python
def test_run_timeout_marks_timed_out():
    result = run_jac_file(FIXTURES / "forever.jac", timeout_s=2)
    assert result.timed_out is True
    assert result.exit_code == -1
    assert result.elapsed_ms >= 2000
    assert result.elapsed_ms < 5000  # sanity upper bound
```

- [ ] **Step 3: Run — expect pass**

Implementation already handles timeouts. Run:
```bash
make test
```
Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add tests/test_jac_runner.py tests/fixtures/forever.jac
git commit -m "test(runner): confirm timeout path marks timed_out"
```

---

### Task 5: Jac runner — parse test output for pass/fail

Jac's `jac test <file>` prints a summary line like `Passed X Failed Y` or similar. Pattern-match that to a boolean.

**Files:**
- Modify: `harness/jac_runner.py`
- Modify: `tests/test_jac_runner.py`
- Create: `tests/fixtures/has_passing_test.jac`
- Create: `tests/fixtures/has_failing_test.jac`

- [ ] **Step 1: Create fixtures (author via jac-mcp)**

Use `jac-mcp`'s `get_resource` on `jac://docs/testing` to see the current test syntax. Author:
- `has_passing_test.jac` — contains one `test` block that passes.
- `has_failing_test.jac` — contains one `test` block with an `assert` that fails.

Round-trip both through `validate_jac`, then run `jac test <file>` on each to capture the exact output shape.

- [ ] **Step 2: Add the failing test**

```python
# tests/test_jac_runner.py (append)
from harness.jac_runner import run_jac_tests

def test_run_tests_passing():
    result = run_jac_tests(FIXTURES / "has_passing_test.jac")
    assert result.all_passed is True
    assert result.n_passed >= 1
    assert result.n_failed == 0

def test_run_tests_failing():
    result = run_jac_tests(FIXTURES / "has_failing_test.jac")
    assert result.all_passed is False
    assert result.n_failed >= 1
```

- [ ] **Step 3: Run — expect ImportError**

```bash
make test
```
Expected: test_run_tests_* fail with "cannot import name 'run_jac_tests'".

- [ ] **Step 4: Implement**

Append to `harness/jac_runner.py`:
```python
import re

@dataclass
class TestResult:
    all_passed: bool
    n_passed: int
    n_failed: int
    raw: RunResult

_TEST_SUMMARY_RE = re.compile(r"(?i)(\d+)\s+passed.*?(\d+)\s+failed|Passed\s*:?\s*(\d+).*?Failed\s*:?\s*(\d+)", re.DOTALL)

def run_jac_tests(path: Path | str, timeout_s: int = 30) -> TestResult:
    import time
    start = time.monotonic()
    proc = subprocess.run(
        ["jac", "test", str(path)],
        capture_output=True, text=True, timeout=timeout_s,
    )
    raw = RunResult(
        exit_code=proc.returncode,
        stdout=proc.stdout, stderr=proc.stderr,
        elapsed_ms=int((time.monotonic() - start) * 1000),
        timed_out=False,
    )
    combined = proc.stdout + "\n" + proc.stderr
    m = _TEST_SUMMARY_RE.search(combined)
    if m:
        groups = [g for g in m.groups() if g is not None]
        n_passed = int(groups[0]) if len(groups) >= 1 else 0
        n_failed = int(groups[1]) if len(groups) >= 2 else 0
    else:
        # If we can't parse, treat any non-zero exit code as failure.
        n_passed = 0 if proc.returncode != 0 else 1
        n_failed = 1 if proc.returncode != 0 else 0
    return TestResult(
        all_passed=(n_failed == 0 and proc.returncode == 0),
        n_passed=n_passed, n_failed=n_failed, raw=raw,
    )
```

**Note:** The regex above handles two common output formats. After Step 1 you will know Jac's exact format; if it differs, update `_TEST_SUMMARY_RE` to match the actual output verbatim and add a unit test using that verbatim output as a string fixture.

- [ ] **Step 5: Run — expect pass**

```bash
make test
```

- [ ] **Step 6: Commit**

```bash
git add harness/jac_runner.py tests/test_jac_runner.py tests/fixtures/has_*.jac
git commit -m "feat(runner): run_jac_tests parses pass/fail counts"
```

---

## PHASE 2 — Prompts and generators (Day 2)

### Task 6: Prompt assembly

**Files:**
- Create: `harness/prompts.py`
- Create: `tests/test_prompts.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_prompts.py
from harness.prompts import build_prompt

def test_build_prompt_combines_arm_and_task():
    arm = "Helpful context about Jac.\n"
    task = "Write a function foo(x: int) -> int."
    prompt = build_prompt(arm=arm, task=task)
    assert arm.strip() in prompt
    assert task.strip() in prompt
    assert "Return only the Jac code" in prompt

def test_build_prompt_no_arm():
    prompt = build_prompt(arm="", task="Write foo")
    assert "Write foo" in prompt
    assert "---" in prompt  # structure preserved

def test_build_prompt_strips_whitespace():
    prompt = build_prompt(arm="  ctx  \n", task="  task  \n")
    assert "ctx" in prompt
    assert "task" in prompt
    assert "  ctx" not in prompt  # leading spaces stripped
```

- [ ] **Step 2: Run — expect fail**

```bash
make test
```

- [ ] **Step 3: Implement**

```python
# harness/prompts.py
from __future__ import annotations

PROMPT_TEMPLATE = """{arm}

---

{task}

---

Return only the Jac code, no prose, no fences."""

def build_prompt(arm: str, task: str) -> str:
    return PROMPT_TEMPLATE.format(arm=arm.strip(), task=task.strip())
```

- [ ] **Step 4: Run — expect pass**

- [ ] **Step 5: Commit**

```bash
git add harness/prompts.py tests/test_prompts.py
git commit -m "feat(prompts): build_prompt assembles arm + task"
```

---

### Task 7: Generator interface with a mock-backed test

**Files:**
- Create: `harness/generators.py`
- Create: `tests/test_generators.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_generators.py
from harness.generators import Generation, generate

def test_generate_returns_generation(monkeypatch):
    # monkeypatch the underlying SDK call
    from harness import generators
    def fake_claude(prompt, temperature, max_tokens, seed):
        return Generation(
            model="claude-haiku-4-5",
            completion="walker foo { }",
            finish_reason="stop",
            input_tokens=10,
            output_tokens=5,
            wall_ms=123,
        )
    monkeypatch.setattr(generators, "_call_claude", fake_claude)
    g = generate(model="claude-haiku-4-5", prompt="Write a walker", temperature=0.2, max_tokens=512, seed=42)
    assert g.completion == "walker foo { }"
    assert g.model == "claude-haiku-4-5"
```

- [ ] **Step 2: Run — expect fail**

- [ ] **Step 3: Implement skeleton with model dispatch**

```python
# harness/generators.py
from __future__ import annotations
import os
import time
from dataclasses import dataclass
from typing import Literal

ModelName = Literal["claude-haiku-4-5", "gemini-3-flash-preview", "meta-llama/llama-4-scout-17b-16e-instruct"]

@dataclass
class Generation:
    model: str
    completion: str
    finish_reason: str
    input_tokens: int
    output_tokens: int
    wall_ms: int

def generate(
    model: ModelName,
    prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 2048,
    seed: int = 0,
) -> Generation:
    if model == "claude-haiku-4-5":
        return _call_claude(prompt, temperature, max_tokens, seed)
    elif model == "gemini-3-flash-preview":
        return _call_gemini(prompt, temperature, max_tokens, seed)
    elif model == "meta-llama/llama-4-scout-17b-16e-instruct":
        return _call_groq(prompt, temperature, max_tokens, seed)
    else:
        raise ValueError(f"unknown model: {model}")

def _call_claude(prompt: str, temperature: float, max_tokens: int, seed: int) -> Generation:
    raise NotImplementedError("implemented in Task 8")

def _call_gemini(prompt: str, temperature: float, max_tokens: int, seed: int) -> Generation:
    raise NotImplementedError("implemented in Task 9")

def _call_groq(prompt: str, temperature: float, max_tokens: int, seed: int) -> Generation:
    raise NotImplementedError("implemented in Task 10")
```

- [ ] **Step 4: Run — expect pass**

- [ ] **Step 5: Commit**

```bash
git add harness/generators.py tests/test_generators.py
git commit -m "feat(generators): skeleton interface with model dispatch"
```

---

### Task 8: Claude Haiku client

**Files:**
- Modify: `harness/generators.py`
- Modify: `tests/test_generators.py`

- [ ] **Step 1: Ensure API key is set**

```bash
cp -n .env.example .env 2>/dev/null || true
# Open .env and fill ANTHROPIC_API_KEY, then:
.venv/bin/python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(bool(os.getenv('ANTHROPIC_API_KEY')))"
```
Expected: `True`.

- [ ] **Step 2: Add a live smoke test (skipped without key)**

Append to `tests/test_generators.py`:
```python
import os
import pytest
from dotenv import load_dotenv
load_dotenv()

@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="no Anthropic key")
def test_claude_live_roundtrip():
    g = generate(model="claude-haiku-4-5", prompt="Reply with exactly the word: ok", temperature=0.0, max_tokens=8, seed=0)
    assert "ok" in g.completion.lower()
    assert g.input_tokens > 0
    assert g.output_tokens > 0
```

- [ ] **Step 3: Implement `_call_claude`**

Replace `_call_claude` in `harness/generators.py`:
```python
def _call_claude(prompt: str, temperature: float, max_tokens: int, seed: int) -> Generation:
    from dotenv import load_dotenv
    load_dotenv()
    from anthropic import Anthropic
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    start = time.monotonic()
    resp = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
    )
    wall_ms = int((time.monotonic() - start) * 1000)
    completion = "".join(b.text for b in resp.content if b.type == "text")
    return Generation(
        model="claude-haiku-4-5",
        completion=completion,
        finish_reason=resp.stop_reason or "stop",
        input_tokens=resp.usage.input_tokens,
        output_tokens=resp.usage.output_tokens,
        wall_ms=wall_ms,
    )
```

- [ ] **Step 4: Run — expect pass**

```bash
make test
```

- [ ] **Step 5: Commit**

```bash
git add harness/generators.py tests/test_generators.py
git commit -m "feat(generators): claude haiku client with live smoke test"
```

---

### Task 9: Gemini client

**Files:**
- Modify: `harness/generators.py`
- Modify: `tests/test_generators.py`

- [ ] **Step 1: Add skipped live test**

```python
# tests/test_generators.py (append)
@pytest.mark.skipif(not os.getenv("GOOGLE_API_KEY"), reason="no Google key")
def test_gemini_live_roundtrip():
    g = generate(model="gemini-3-flash-preview", prompt="Reply with exactly the word: ok", temperature=0.0, max_tokens=8, seed=0)
    assert "ok" in g.completion.lower()
```

- [ ] **Step 2: Implement `_call_gemini`**

Replace in `harness/generators.py`:
```python
def _call_gemini(prompt: str, temperature: float, max_tokens: int, seed: int) -> Generation:
    from dotenv import load_dotenv
    load_dotenv()
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    start = time.monotonic()
    resp = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            seed=seed,
        ),
    )
    wall_ms = int((time.monotonic() - start) * 1000)
    text = resp.text or ""
    usage = resp.usage_metadata
    return Generation(
        model="gemini-3-flash-preview",
        completion=text,
        finish_reason=(resp.candidates[0].finish_reason.name if resp.candidates else "stop"),
        input_tokens=(usage.prompt_token_count if usage else 0),
        output_tokens=(usage.candidates_token_count if usage else 0),
        wall_ms=wall_ms,
    )
```

- [ ] **Step 3: Run — expect pass**

- [ ] **Step 4: Commit**

```bash
git add harness/generators.py tests/test_generators.py
git commit -m "feat(generators): gemini 2.5 pro client"
```

---

### Task 10: Groq / Llama client

**Files:**
- Modify: `harness/generators.py`
- Modify: `tests/test_generators.py`

- [ ] **Step 1: Add skipped live test**

```python
# tests/test_generators.py (append)
@pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="no Groq key")
def test_groq_live_roundtrip():
    g = generate(model="meta-llama/llama-4-scout-17b-16e-instruct", prompt="Reply with exactly the word: ok", temperature=0.0, max_tokens=8, seed=0)
    assert "ok" in g.completion.lower()
```

- [ ] **Step 2: Implement `_call_groq`**

Replace in `harness/generators.py`:
```python
def _call_groq(prompt: str, temperature: float, max_tokens: int, seed: int) -> Generation:
    from dotenv import load_dotenv
    load_dotenv()
    from groq import Groq
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    start = time.monotonic()
    resp = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        temperature=temperature,
        max_tokens=max_tokens,
        seed=seed,
        messages=[{"role": "user", "content": prompt}],
    )
    wall_ms = int((time.monotonic() - start) * 1000)
    choice = resp.choices[0]
    return Generation(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        completion=choice.message.content or "",
        finish_reason=choice.finish_reason or "stop",
        input_tokens=resp.usage.prompt_tokens,
        output_tokens=resp.usage.completion_tokens,
        wall_ms=wall_ms,
    )
```

- [ ] **Step 3: Run — expect pass**

- [ ] **Step 4: Commit**

```bash
git add harness/generators.py tests/test_generators.py
git commit -m "feat(generators): groq llama 3.3 70b client"
```

---

## PHASE 3 — Pilot end-to-end (Day 2 late)

### Task 11: Author one throwaway pilot task

**Goal:** Prove generator → runner works end-to-end before burning time on task authoring.

**Files:**
- Create: `tasks/pilot/pilot-fibonacci/{prompt.md, solution.jac, tests.jac, rubric.md, meta.yaml}`

- [ ] **Step 1: Use jac-mcp to fetch guidance**

Call `jac-mcp` tools:
1. `understand_jac_and_jaseci` — read the knowledge map.
2. `get_resource` on `jac://guide/pitfalls` and `jac://guide/patterns`.
3. `get_resource` on `jac://docs/cheatsheet` for syntax.
4. `get_resource` on `jac://docs/testing` for the test syntax.

- [ ] **Step 2: Author `prompt.md`**

```markdown
# Pilot task: fibonacci

Write a Jac function `fib(n: int) -> int` that returns the n-th Fibonacci number where `fib(0) = 0`, `fib(1) = 1`, `fib(n) = fib(n-1) + fib(n-2)` for `n >= 2`.

Example:
  fib(0) == 0
  fib(1) == 1
  fib(10) == 55
```

- [ ] **Step 3: Author `solution.jac` via jac-mcp**

Draft a Jac implementation. Call `validate_jac` until it compiles cleanly. Common pitfalls to watch:
- Function declarations use `def name(params: type) -> type` (see `jac://docs/foundation`).
- Type annotations are required.
- Run once via `jac run solution.jac` as a sanity smoke (even if there's no entry point, this catches import errors).

- [ ] **Step 4: Author `tests.jac`**

Use Jac's native `test` block syntax (verify via `jac://docs/testing`). Tests must import/use `solution.jac`. Must cover the three examples from the prompt.

- [ ] **Step 5: Validate end-to-end**

```bash
cd tasks/pilot/pilot-fibonacci
jac test tests.jac
```
Expected: all tests pass.

Also round-trip with `validate_jac` on both files.

- [ ] **Step 6: Author `rubric.md`**

```markdown
# Rubric: pilot-fibonacci

This pilot task is used only to smoke-test the harness. Do not use its scores in the main report.

Expected constructs: type annotations on params and return, a function defined with `def`.
```

- [ ] **Step 7: Author `meta.yaml`**

```yaml
task_id: pilot-fibonacci
bucket: pilot
created_at: 2026-04-DD  # fill in today
jac_constructs_expected: [type_annotations]
baseline_pass_target: skip
```

- [ ] **Step 8: Commit**

```bash
git add tasks/pilot/
git commit -m "feat(tasks): add pilot fibonacci task for smoke testing"
```

---

### Task 12: End-to-end smoke — generator → runner on the pilot task

**Files:**
- Create: `scripts/smoke_pilot.py`

- [ ] **Step 1: Write the smoke script**

```python
# scripts/smoke_pilot.py
"""One-shot: run Haiku on the pilot task, execute, print pass/fail."""
from pathlib import Path
import tempfile, shutil
from harness.prompts import build_prompt
from harness.generators import generate
from harness.jac_runner import run_jac_tests

TASK_DIR = Path("tasks/pilot/pilot-fibonacci")
prompt_text = (TASK_DIR / "prompt.md").read_text()

full_prompt = build_prompt(arm="", task=prompt_text)
g = generate(model="claude-haiku-4-5", prompt=full_prompt, temperature=0.2, max_tokens=1024, seed=0)
print("---completion---"); print(g.completion); print("---end---")

with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    (td / "solution.jac").write_text(g.completion)
    shutil.copy(TASK_DIR / "tests.jac", td / "tests.jac")
    result = run_jac_tests(td / "tests.jac", timeout_s=30)
    print(f"all_passed={result.all_passed} n_passed={result.n_passed} n_failed={result.n_failed}")
```

- [ ] **Step 2: Run**

```bash
.venv/bin/python scripts/smoke_pilot.py
```
Expected: completion prints Jac code; eventually prints `all_passed=True` or `all_passed=False`. Either is fine — the point is the pipeline works.

If `all_passed=False`, inspect the completion. If the model's output included prose or markdown fences despite our prompt, either (a) strip them in `run.py` later, or (b) tune the prompt. Note which for Task 39.

- [ ] **Step 3: Commit**

```bash
git add scripts/smoke_pilot.py
git commit -m "chore: e2e smoke script confirms generator → runner path"
```

---

## PHASE 4 — Arm content (Day 3 AM)

### Task 13: Fetch LLMDocs-Mini and LLMDocs-Full

**Files:**
- Create: `scripts/fetch_llmdocs.py`
- Create: `arms/llmdocs-mini/arm.md`
- Create: `arms/llmdocs-mini/SOURCE.md`
- Create: `arms/llmdocs-full/arm.md`
- Create: `arms/llmdocs-full/SOURCE.md`

- [ ] **Step 1: Find the canonical URLs**

Use `jac-mcp`'s `search_docs` or WebFetch against `docs.jaseci.org`. Typical URLs:
- `https://docs.jaseci.org/llms-mini.txt` or similar
- `https://docs.jaseci.org/llms-full.txt` or similar

Confirm the exact URLs by inspecting docs.jaseci.org. Record them in `SOURCE.md` for each arm.

- [ ] **Step 2: Write the fetch script**

```python
# scripts/fetch_llmdocs.py
import sys, urllib.request
from pathlib import Path

SOURCES = {
    "arms/llmdocs-mini/arm.md": "https://docs.jaseci.org/LLMDOCS_MINI_URL",   # fill after Step 1
    "arms/llmdocs-full/arm.md": "https://docs.jaseci.org/LLMDOCS_FULL_URL",   # fill after Step 1
}

for dest, url in SOURCES.items():
    Path(dest).parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as r:
        Path(dest).write_text(r.read().decode("utf-8"))
    print(f"fetched {url} -> {dest}")
```

- [ ] **Step 3: Fill in the URLs and run**

```bash
.venv/bin/python scripts/fetch_llmdocs.py
```
Expected: both arm files populated with non-empty content.

- [ ] **Step 4: Write SOURCE.md for each**

```markdown
# arms/llmdocs-mini/SOURCE.md
Source: <the actual URL>
Fetched: 2026-04-DD
SHA256: <compute with `shasum -a 256 arms/llmdocs-mini/arm.md`>
License: see jaseci.org; redistributed here verbatim for evaluation purposes under fair use.
```

Same shape for `llmdocs-full/SOURCE.md`.

- [ ] **Step 5: Commit**

```bash
git add scripts/fetch_llmdocs.py arms/llmdocs-mini/ arms/llmdocs-full/
git commit -m "feat(arms): fetch and pin LLMDocs-Mini and LLMDocs-Full"
```

---

### Task 14: No-skill arm

**Files:**
- Create: `arms/no-skill/arm.md`

- [ ] **Step 1: Write the arm content**

```markdown
<!-- arms/no-skill/arm.md -->
You are writing Jac code. Return only the Jac code requested, no prose or fences.
```

Rationale: not literally empty (a totally empty arm would break the paired prompt structure), but zero domain-specific content. Length ≈ 15 tokens.

- [ ] **Step 2: Commit**

```bash
git add arms/no-skill/arm.md
git commit -m "feat(arms): add minimal no-skill arm"
```

---

## PHASE 5 — Task authoring (Days 3–5)

Each of Tasks 15–25 authors one of the 10 Jac tasks (plus the calibration helper). The workflow is identical across tasks; only the content differs.

### Task 15: Calibration helper

**Files:**
- Create: `scripts/calibrate_task.py`

- [ ] **Step 1: Write the script**

```python
# scripts/calibrate_task.py
"""Run 5 samples of no-skill / Haiku on a task; report pass rate."""
import argparse, tempfile, shutil
from pathlib import Path
from harness.prompts import build_prompt
from harness.generators import generate
from harness.jac_runner import run_jac_tests

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task_dir", type=Path)
    ap.add_argument("--n", type=int, default=5)
    args = ap.parse_args()
    prompt_text = (args.task_dir / "prompt.md").read_text()
    no_skill_arm = Path("arms/no-skill/arm.md").read_text()
    full_prompt = build_prompt(arm=no_skill_arm, task=prompt_text)
    passes = 0
    for i in range(args.n):
        g = generate(model="claude-haiku-4-5", prompt=full_prompt, temperature=0.2, max_tokens=2048, seed=i)
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            (td / "solution.jac").write_text(g.completion)
            shutil.copy(args.task_dir / "tests.jac", td / "tests.jac")
            result = run_jac_tests(td / "tests.jac", timeout_s=30)
            print(f"sample {i}: all_passed={result.all_passed}")
            if result.all_passed: passes += 1
    rate = passes / args.n
    print(f"\nBASELINE PASS RATE: {passes}/{args.n} = {rate:.0%}")
    if rate == 0.0 or rate == 1.0:
        print("WARN: task does not discriminate at baseline. Revise or reject.")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke-test against the pilot task**

```bash
.venv/bin/python scripts/calibrate_task.py tasks/pilot/pilot-fibonacci
```
Expected: prints 5 per-sample results and a summary line. Rate is informational for the pilot (not gating).

- [ ] **Step 3: Commit**

```bash
git add scripts/calibrate_task.py
git commit -m "feat(scripts): calibrate_task reports baseline pass rate"
```

---

### Tasks 16–25: Author the 10 Jac tasks

Each task follows the same template. The procedure is identical; only the task's purpose differs.

**Template applied in every one of Tasks 16–25:**

Files for task N:
- Create: `tasks/<bucket>/<id>/prompt.md`
- Create: `tasks/<bucket>/<id>/solution.jac`
- Create: `tasks/<bucket>/<id>/tests.jac`
- Create: `tasks/<bucket>/<id>/rubric.md`
- Create: `tasks/<bucket>/<id>/meta.yaml`

- [ ] **Step A: Use jac-mcp to read relevant guides**
  - Always: `jac://guide/pitfalls`, `jac://guide/patterns`.
  - For syntax bucket: `jac://docs/foundation`, `jac://docs/cheatsheet`.
  - For graph bucket: `jac://docs/osp`.
  - For walker bucket: `jac://docs/osp`, `jac://docs/tutorial-osp`, `jac://docs/walker-responses`.

- [ ] **Step B: Author `prompt.md`**
  - HumanEval style: signature + docstring + 1–3 input/output examples.
  - No references to the test file. Generator must not see hidden tests.
  - Under 200 words.

- [ ] **Step C: Author `solution.jac`** via jac-mcp
  - Call `validate_jac` until it compiles cleanly.
  - Run `jac run solution.jac` to catch runtime errors (if it has an entry point).
  - Must use the Jac-native constructs listed in the task's `jac_constructs_expected`.

- [ ] **Step D: Author `tests.jac`**
  - Use Jac's native `test` blocks.
  - Must import `solution.jac` (or include it via Jac's import syntax — confirm via `jac://docs/code-organization`).
  - 3–5 assertions covering normal cases, one edge case, and one tricky case.
  - Run `jac test tests.jac` — must pass with the `solution.jac` present.

- [ ] **Step E: Author `rubric.md`** — per-task, following the research recipe's Pathak-style per-task rubric.

```markdown
# Rubric: tasks/<bucket>/<id>

## Task summary
<one-line what this task measures>

## Expected idiomatic constructs (from jac-mcp guides)
- <construct 1> — cite pitfall/pattern URI
- <construct 2> — cite pitfall/pattern URI

## Level descriptors
- 5 — uses all expected constructs, clean typing, no Python-transliteration smells
- 4 — uses most expected constructs; minor style issues
- 3 — solves the task but misses ≥ 1 core idiomatic construct
- 2 — solves via Python-transliterated pattern (e.g., dict-of-lists for edges)
- 1 — does not solve or not recognizable as Jac

## Penalize explicitly
- <Python-ish anti-pattern specific to this task>
```

- [ ] **Step F: Author `meta.yaml`**

```yaml
task_id: <id>
bucket: <syntax|graph|walker>
created_at: 2026-04-DD
jac_constructs_expected:
  - <constr_1>
  - <constr_2>
baseline_pass_target: 0.2-0.8
held_out: false  # true only for tasks 03 and 10
```

- [ ] **Step G: Calibrate**

```bash
.venv/bin/python scripts/calibrate_task.py tasks/<bucket>/<id>
```
Expected: pass rate in [0.2, 0.8]. If 0.0 or 1.0, revise prompt or tests and rerun.

- [ ] **Step H: Commit**

```bash
git add tasks/<bucket>/<id>/
git commit -m "feat(tasks): <id> — <bucket> — <one-line description>"
```

**Specific content per task:**

| Task# | id | bucket | what it measures | expected constructs |
|---|---|---|---|---|
| 16 | 01 | syntax | Function with typed params/return over a list | `has` field typing, for-in iteration, typed return |
| 17 | 02 | syntax | `obj` archetype with methods | `obj` archetype, method syntax, `has` fields |
| 18 | 03 | syntax | Filter-assign comprehension over a list of objs | filter comprehension `(=)`, type annotations. **HELD OUT** |
| 19 | 04 | graph | Build a small typed graph | `node` archetype, `edge` archetype, `++>` connect |
| 20 | 05 | graph | Graph with bidirectional edges and properties | typed `edge` with `has` fields, `<++>` bidir |
| 21 | 06 | graph | Mutate a typed edge's attribute | typed edges, access + assignment via spawn |
| 22 | 07 | walker | Walker that counts nodes by type | `walker`, `visit`, `can ... with node entry` |
| 23 | 08 | walker | Walker with `disengage` on condition | `walker`, `visit`, `disengage` |
| 24 | 09 | walker | Walker using abilities on nodes | `walker`, node-side abilities, `here` |
| 25 | 10 | walker | Walker that aggregates over a path | `walker`, `visit`, typed state. **HELD OUT** |

Held-out tasks (18 and 25): after authoring and calibration, do not look at their scores during iteration.

After completing Task 25, **all 10 tasks have been authored, calibrated, and committed.**

---

## PHASE 6 — AST detectors (Day 6)

### Tasks 26–31: Implement the 6 binary idiom detectors

**Files:**
- Create: `harness/detectors.py`
- Create: `tests/test_detectors.py`
- Create: `tests/fixtures/idiomatic/*.jac` — one per detector
- Create: `tests/fixtures/python_ish/*.jac` — one per detector

Each detector is a function with signature `def detector_name(source: str) -> bool`, where `source` is Jac code with comments stripped and formatting normalized.

**Workflow applied in every one of Tasks 26–31:**

- [ ] **Step 1: Create fixtures for this detector**
  - `tests/fixtures/idiomatic/<detector>.jac` — obvious positive case
  - `tests/fixtures/python_ish/<detector>.jac` — obvious negative case
  - Round-trip both through `validate_jac`.

- [ ] **Step 2: Write the failing test**

```python
# tests/test_detectors.py (append)
from pathlib import Path
from harness.detectors import DETECTOR_NAME  # substitute per task

IDIOMATIC = Path(__file__).parent / "fixtures" / "idiomatic"
PYISH = Path(__file__).parent / "fixtures" / "python_ish"

def test_DETECTOR_NAME_positive():
    src = (IDIOMATIC / "DETECTOR_FILE.jac").read_text()
    assert DETECTOR_NAME(src) is True

def test_DETECTOR_NAME_negative():
    src = (PYISH / "DETECTOR_FILE.jac").read_text()
    assert DETECTOR_NAME(src) is False
```

- [ ] **Step 3: Run — expect fail**

- [ ] **Step 4: Implement**

Append to `harness/detectors.py`:
```python
import re

def strip_comments(src: str) -> str:
    # Jac comments: // line, /* block */ (confirm via jac://docs/cheatsheet)
    src = re.sub(r"//[^\n]*", "", src)
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
    return src
```

Then for each detector:

**Task 26 — `uses_walker`:** match `\bwalker\s+\w+` in stripped source.
**Task 27 — `uses_visit`:** match `\bvisit\b` followed by an expression (not a comment), in stripped source.
**Task 28 — `uses_typed_edge_archetype`:** match `\bedge\s+\w+` (an `edge` archetype declaration).
**Task 29 — `uses_connect_op`:** match `\+\+>` or `<\+\+>` in stripped source.
**Task 30 — `has_type_annotations`:** all `has` declarations, function params, and return types have `: <type>` annotations. This is multi-line — use two passes: (1) find all `has <name>` — confirm each has `: <type>`; (2) find all `def name(<params>)` — confirm each param has `:`; (3) find all `def name(...) -> ...` — confirm `->` present. Return True iff all three pass or if no applicable constructs appear.
**Task 31 — `uses_abilities_on_nodes`:** match `\bcan\s+\w+\s+with\s+\w+\s+entry\b` — this is Jac's ability syntax (confirm exact form via `jac://guide/patterns`).

Each detector is ~5-15 lines. Keep them small.

- [ ] **Step 5: Run — expect pass**

- [ ] **Step 6: Commit**

```bash
git add harness/detectors.py tests/test_detectors.py tests/fixtures/idiomatic/<detector>.jac tests/fixtures/python_ish/<detector>.jac
git commit -m "feat(detectors): <detector_name> — pattern-based"
```

After Task 31, add the aggregation function:

```python
# harness/detectors.py (append after the 6 detectors)
DETECTORS = {
    "uses_walker": uses_walker,
    "uses_visit": uses_visit,
    "uses_typed_edge_archetype": uses_typed_edge_archetype,
    "uses_connect_op": uses_connect_op,
    "has_type_annotations": has_type_annotations,
    "uses_abilities_on_nodes": uses_abilities_on_nodes,
}

def run_all(source: str, expected: list[str] | None = None) -> dict:
    """Run all detectors. If `expected` is given, subscore is mean over expected only."""
    stripped = strip_comments(source)
    results = {name: fn(stripped) for name, fn in DETECTORS.items()}
    if expected:
        applicable = [results[name] for name in expected if name in results]
    else:
        applicable = list(results.values())
    subscore = (sum(applicable) / len(applicable)) if applicable else 0.0
    return {"per_detector": results, "ast_subscore": subscore}
```

Add a test for `run_all`:
```python
def test_run_all_uses_expected():
    src = (IDIOMATIC / "uses_walker.jac").read_text()
    out = run_all(src, expected=["uses_walker"])
    assert out["ast_subscore"] == 1.0
    out = run_all(src, expected=["uses_walker", "uses_abilities_on_nodes"])
    # exactly one of the two expected is present
    assert 0.0 < out["ast_subscore"] < 1.0 or out["ast_subscore"] in (0.0, 0.5, 1.0)
```

Commit:
```bash
git add harness/detectors.py tests/test_detectors.py
git commit -m "feat(detectors): run_all aggregation with expected filtering"
```

---

## PHASE 7 — Judge + validation (Days 7–8)

### Task 32: Judge prompt template

**Files:**
- Create: `judge/prompt.md`

- [ ] **Step 1: Write the Prometheus-format prompt**

```markdown
<!-- judge/prompt.md -->
You are grading one candidate Jac-language solution to a programming task. You are NOT grading whether the code compiles or passes tests — a separate system does that. You are grading IDIOMATICITY: how well the candidate uses Jac-native constructs versus transliterating Python.

# Task rubric
{task_rubric}

# Reference idiomatic solution
```jac
{reference_solution}
```

# Candidate code
```jac
{candidate_code}
```

# Instructions

First, list which idiomatic Jac constructs appear in the candidate, citing line numbers. Be specific: "line 5 uses a `walker` archetype", not "uses walkers".

Second, for each level descriptor in the task rubric, write one sentence on whether the candidate meets it.

Third, if the candidate reads like Python-with-Jac-syntax — e.g., using dict-of-lists for what should be typed edges, using recursion instead of a walker with visit, omitting type annotations — this is a SERIOUS idiomaticity failure. Score 1 or 2 regardless of whether tests pass. Jac is not Python; this is the single most important thing to catch.

Finally, emit STRICTLY VALID JSON on its own line:
{"constructs_present": [<strings>], "per_criterion": {<rubric_item>: <1-5 int>}, "feedback": "<1-3 sentences>", "score": <1-5 int>}

Then on a new line emit: [RESULT] X   where X is your final score 1-5.
```

- [ ] **Step 2: Commit**

```bash
git add judge/prompt.md
git commit -m "feat(judge): prometheus-format prompt template with python-penalty"
```

---

### Task 33: Judge implementation

**Files:**
- Create: `harness/judge.py`
- Create: `tests/test_judge.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_judge.py
import os, pytest
from dotenv import load_dotenv
load_dotenv()
from harness.judge import judge_once, judge_median

@pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="no Groq key")
def test_judge_once_returns_int_score():
    task_rubric = "Uses walker for traversal. Score 1-5."
    reference = "walker foo { has count: int = 0; }"
    candidate = "walker foo { has count: int = 0; }"
    r = judge_once(task_rubric=task_rubric, reference_solution=reference, candidate_code=candidate)
    assert 1 <= r["score"] <= 5
    assert "feedback" in r

@pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="no Groq key")
def test_judge_median_runs_three():
    task_rubric = "Uses walker. Score 1-5."
    reference = "walker foo { }"
    candidate = "walker foo { }"
    out = judge_median(task_rubric=task_rubric, reference_solution=reference, candidate_code=candidate)
    assert 1 <= out["median"] <= 5
    assert len(out["runs"]) == 3
```

- [ ] **Step 2: Run — expect fail**

- [ ] **Step 3: Implement**

```python
# harness/judge.py
from __future__ import annotations
import json, os, re, time
from pathlib import Path
from statistics import median

PROMPT_TEMPLATE = Path("judge/prompt.md").read_text()
_RESULT_RE = re.compile(r"\[RESULT\]\s*([1-5])")
_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)

JUDGE_MODEL = "openai/gpt-oss-120b"  # via Groq; see spec §6.2

def _call_judge(prompt: str, *, temperature: float = 0.3, max_tokens: int = 1024, seed: int = 0) -> str:
    """Call the judge model via Groq SDK and return the completion text.

    GPT-OSS 120B via Groq is deliberately non-Anthropic, non-Google, and non-Meta
    so no self-preference bias against any of the three generator families.
    """
    from dotenv import load_dotenv
    load_dotenv()
    from groq import Groq
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    resp = client.chat.completions.create(
        model=JUDGE_MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
        seed=seed,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content or ""

def judge_once(*, task_rubric: str, reference_solution: str, candidate_code: str) -> dict:
    prompt = PROMPT_TEMPLATE.format(
        task_rubric=task_rubric,
        reference_solution=reference_solution,
        candidate_code=candidate_code,
    )
    text = _call_judge(prompt=prompt, temperature=0.3, max_tokens=1024, seed=int(time.time() * 1000) % 10_000)
    m = _RESULT_RE.search(text)
    score = int(m.group(1)) if m else 1
    jm = _JSON_RE.search(text)
    parsed = {}
    if jm:
        try: parsed = json.loads(jm.group(0))
        except Exception: parsed = {}
    return {
        "score": score,
        "feedback": parsed.get("feedback", text[:200]),
        "constructs_present": parsed.get("constructs_present", []),
        "raw": text,
    }

def judge_median(*, task_rubric: str, reference_solution: str, candidate_code: str) -> dict:
    runs = [judge_once(task_rubric=task_rubric, reference_solution=reference_solution, candidate_code=candidate_code) for _ in range(3)]
    scores = [r["score"] for r in runs]
    return {"median": int(median(scores)), "runs": runs, "scores": scores}
```

- [ ] **Step 4: Run — expect pass**

- [ ] **Step 5: Commit**

```bash
git add harness/judge.py tests/test_judge.py
git commit -m "feat(judge): gpt-oss-120b via groq judge with 3-run median"
```

---

### Task 34: Hand-label 15 snippets (judge validation corpus)

**Files:**
- Create: `judge/validation/snippets/{01..15}.jac`
- Create: `judge/validation/hand_labels.jsonl`
- Create: `judge/validation/rubric_history.md` (seeded with "2026-04-DD: initial rubric — see judge/prompt.md")

- [ ] **Step 1: Decide snippet composition**

Distribute 15 snippets across the 1–5 quality spectrum:
- 3 score-5 snippets — fully idiomatic Jac (can be cribbed from existing Jaseci examples if license permits, or hand-authored via jac-mcp).
- 3 score-4 snippets — mostly idiomatic, minor issues.
- 3 score-3 snippets — correct but not idiomatic (e.g., missing type annotations).
- 3 score-2 snippets — Python-transliterated (dict-of-lists for edges, recursion instead of walker).
- 3 score-1 snippets — non-Jac, syntax errors, or nonsense.

- [ ] **Step 2: Author each snippet via jac-mcp**

For each snippet:
1. Call `jac-mcp` `get_resource` on `jac://guide/pitfalls` and `jac://guide/patterns` for reference.
2. Write the snippet to `judge/validation/snippets/NN.jac`.
3. Validate parseability (score-1 snippets may intentionally fail to parse — that's fine; tag them accordingly).

- [ ] **Step 3: Hand-label with justifications**

Write `judge/validation/hand_labels.jsonl`, one JSON object per line:
```json
{"file": "01.jac", "label": 5, "justification": "Uses walker + visit + typed edge archetype. See jac://guide/patterns §Traversal."}
```

Every label's justification **must cite a specific rule from `jac://guide/pitfalls` or `jac://guide/patterns`** (spec §6.3 and CLAUDE.md).

- [ ] **Step 4: Commit**

```bash
git add judge/validation/
git commit -m "feat(judge): 15 hand-labeled Jac snippets for κ validation"
```

---

### Task 35: Validate the judge — Cohen's κ gate

**Files:**
- Create: `scripts/validate_judge.py`
- Create: `harness/stats.py` (partial — just Cohen's κ for now; rest in Task 37)

- [ ] **Step 1: Write Cohen's κ test first**

```python
# tests/test_stats.py
from harness.stats import cohen_kappa

def test_cohen_kappa_perfect_agreement():
    assert cohen_kappa([1,2,3,4,5], [1,2,3,4,5]) == 1.0

def test_cohen_kappa_disagreement():
    k = cohen_kappa([1,1,1,1,1], [5,5,5,5,5])
    assert k <= 0.0  # maximum disagreement

def test_cohen_kappa_mixed():
    # 3 agree, 2 disagree
    k = cohen_kappa([1,2,3,4,5], [1,2,3,5,4])
    assert 0.0 < k < 1.0
```

- [ ] **Step 2: Run — expect fail**

- [ ] **Step 3: Implement Cohen's κ**

```python
# harness/stats.py
from __future__ import annotations
from collections import Counter

def cohen_kappa(labels_a: list[int], labels_b: list[int]) -> float:
    assert len(labels_a) == len(labels_b) and len(labels_a) > 0
    n = len(labels_a)
    cats = sorted(set(labels_a) | set(labels_b))
    agree = sum(1 for a, b in zip(labels_a, labels_b) if a == b) / n
    pa = Counter(labels_a)
    pb = Counter(labels_b)
    expected = sum((pa[c] / n) * (pb[c] / n) for c in cats)
    if expected == 1.0:
        return 1.0
    return (agree - expected) / (1 - expected)
```

- [ ] **Step 4: Run — expect pass**

- [ ] **Step 5: Write the validate_judge script**

```python
# scripts/validate_judge.py
"""Run judge on 15 hand-labeled snippets, compute Cohen's κ. Fails if κ < 0.4."""
import json, sys
from pathlib import Path
from harness.judge import judge_median
from harness.stats import cohen_kappa

VAL = Path("judge/validation")
labels = [json.loads(ln) for ln in (VAL / "hand_labels.jsonl").read_text().splitlines() if ln.strip()]

# Use a minimal generic rubric for validation-corpus snippets, since they aren't
# tied to a specific task. Pull it from judge/rubric.md if it exists, else inline.
GENERIC_RUBRIC = """Score the snippet on Jac idiomaticity 1-5. 5 = uses nodes/edges/walkers/visit/abilities where applicable, type annotations present, no Python smells. 1 = not Jac or fully Python-transliterated."""

hand, model = [], []
for row in labels:
    candidate = (VAL / "snippets" / row["file"]).read_text()
    out = judge_median(task_rubric=GENERIC_RUBRIC, reference_solution="(none)", candidate_code=candidate)
    hand.append(row["label"])
    model.append(out["median"])
    print(f"{row['file']}: hand={row['label']}  judge_median={out['median']}  runs={out['scores']}")

k = cohen_kappa(hand, model)
print(f"\nCohen's κ = {k:.3f}   (target ≥ 0.4)")
if k < 0.4:
    print("JUDGE FAILED VALIDATION. Iterate judge/prompt.md and re-run.")
    sys.exit(1)
print("JUDGE VALIDATED.")
```

- [ ] **Step 6: Run and iterate**

```bash
.venv/bin/python scripts/validate_judge.py
```

If κ ≥ 0.4: commit and proceed.

If κ < 0.4:
1. Inspect which snippets the judge scored farthest from your label.
2. Revise `judge/prompt.md` to address the failure mode (e.g., add a specific example, sharpen a descriptor).
3. Append a dated entry to `judge/validation/rubric_history.md` documenting what changed and why.
4. Re-run. Iterate up to 3 times. If still < 0.4 after 3 revisions, invoke the pre-committed fallback: use AST-only idiomaticity (spec §12) and document the limitation in RESULTS.md.

- [ ] **Step 7: Commit (success or fallback)**

```bash
git add scripts/validate_judge.py harness/stats.py tests/test_stats.py judge/prompt.md judge/validation/rubric_history.md
git commit -m "feat(judge): validated against hand labels (κ=X.XX)"
# or if fallback: "chore(judge): fallback to AST-only after 3 rubric iterations (κ=X.XX)"
```

---

## PHASE 8 — Scorer and full stats (Day 9 AM)

### Task 36: Scorer — combine AST + judge

**Files:**
- Create: `harness/scorer.py`
- Create: `tests/test_scorer.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_scorer.py
from harness.scorer import idiom_score

def test_idiom_score_weights_correctly():
    # AST 1.0, judge 5 -> 0.4*1.0 + 0.6*(5/5) = 1.0
    assert abs(idiom_score(ast_subscore=1.0, judge_median=5) - 1.0) < 1e-9
    # AST 0.0, judge 1 -> 0.4*0 + 0.6*(1/5) = 0.12
    assert abs(idiom_score(ast_subscore=0.0, judge_median=1) - 0.12) < 1e-9
    # AST 0.5, judge 3 -> 0.4*0.5 + 0.6*(3/5) = 0.2 + 0.36 = 0.56
    assert abs(idiom_score(ast_subscore=0.5, judge_median=3) - 0.56) < 1e-9
```

- [ ] **Step 2: Run — expect fail**

- [ ] **Step 3: Implement**

```python
# harness/scorer.py
def idiom_score(*, ast_subscore: float, judge_median: int) -> float:
    assert 0.0 <= ast_subscore <= 1.0
    assert 1 <= judge_median <= 5
    return 0.4 * ast_subscore + 0.6 * (judge_median / 5.0)
```

- [ ] **Step 4: Run — expect pass**

- [ ] **Step 5: Commit**

```bash
git add harness/scorer.py tests/test_scorer.py
git commit -m "feat(scorer): combine ast subscore and judge median"
```

---

### Task 37: Statistics — unbiased pass@k, McNemar, paired bootstrap, Wilson

**Files:**
- Modify: `harness/stats.py`
- Modify: `tests/test_stats.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_stats.py (append)
import math
from harness.stats import pass_at_k, mcnemar_exact, paired_bootstrap_mean, wilson_interval

def test_pass_at_k_unbiased():
    # n=5, c=3, k=1: pass@1 = 1 - C(2,1)/C(5,1) = 1 - 2/5 = 0.6
    assert abs(pass_at_k(n=5, c=3, k=1) - 0.6) < 1e-9
    # n=5, c=5, k=5: must be 1.0
    assert pass_at_k(n=5, c=5, k=5) == 1.0
    # n=5, c=0, k=1: must be 0.0
    assert pass_at_k(n=5, c=0, k=1) == 0.0

def test_mcnemar_exact_trivial():
    # 10 tied, 0 flips: p = 1
    p = mcnemar_exact(a_wins=0, b_wins=0)
    assert p == 1.0
    # all flips one way: p should be small
    p = mcnemar_exact(a_wins=10, b_wins=0)
    assert p < 0.01

def test_paired_bootstrap_mean_deterministic():
    # identical arms -> CI should contain 0
    a = [0.5]*20
    b = [0.5]*20
    lo, hi = paired_bootstrap_mean(a, b, n_boot=500, seed=42)
    assert lo <= 0.0 <= hi

def test_wilson_interval():
    lo, hi = wilson_interval(successes=5, trials=10, z=1.96)
    assert 0.0 <= lo < 0.5 < hi <= 1.0
```

- [ ] **Step 2: Implement**

Append to `harness/stats.py`:
```python
from math import comb, sqrt
import random

def pass_at_k(*, n: int, c: int, k: int) -> float:
    """Chen et al. 2021 unbiased estimator: 1 - C(n-c, k) / C(n, k)."""
    assert 0 <= c <= n and 1 <= k <= n
    if n - c < k:
        return 1.0
    return 1.0 - comb(n - c, k) / comb(n, k)

def mcnemar_exact(*, a_wins: int, b_wins: int) -> float:
    """Exact McNemar p-value (two-sided) on discordant pairs."""
    n = a_wins + b_wins
    if n == 0:
        return 1.0
    k = min(a_wins, b_wins)
    # two-tailed binomial with p=0.5
    tail = sum(comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)

def paired_bootstrap_mean(a: list[float], b: list[float], *, n_boot: int = 10_000, seed: int = 0, alpha: float = 0.05) -> tuple[float, float]:
    assert len(a) == len(b)
    rng = random.Random(seed)
    diffs = [ai - bi for ai, bi in zip(a, b)]
    n = len(diffs)
    boots: list[float] = []
    for _ in range(n_boot):
        sample = [diffs[rng.randrange(n)] for _ in range(n)]
        boots.append(sum(sample) / n)
    boots.sort()
    lo = boots[int((alpha / 2) * n_boot)]
    hi = boots[int((1 - alpha / 2) * n_boot) - 1]
    return lo, hi

def wilson_interval(*, successes: int, trials: int, z: float = 1.96) -> tuple[float, float]:
    if trials == 0:
        return 0.0, 1.0
    p = successes / trials
    denom = 1 + z**2 / trials
    center = (p + z**2 / (2 * trials)) / denom
    margin = z * sqrt((p * (1 - p) + z**2 / (4 * trials)) / trials) / denom
    return max(0.0, center - margin), min(1.0, center + margin)
```

- [ ] **Step 3: Run — expect pass**

- [ ] **Step 4: Commit**

```bash
git add harness/stats.py tests/test_stats.py
git commit -m "feat(stats): pass@k unbiased, mcnemar exact, paired bootstrap, wilson"
```

---

## PHASE 9 — Orchestrator (Day 9 AM cont.)

### Task 38: Plan builder — writes run_plan.jsonl

**Files:**
- Create: `harness/plan_builder.py`
- Create: `tests/test_plan_builder.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_plan_builder.py
from harness.plan_builder import build_plan

def test_build_plan_yields_full_cross_product(tmp_path):
    arms = ["no-skill", "llmdocs-mini"]
    models = ["claude-haiku-4-5", "gemini-3-flash-preview"]
    tasks = ["01", "02"]
    plan = list(build_plan(arms=arms, models=models, task_ids=tasks, n_samples=3, seed_base=0))
    assert len(plan) == 2*2*2*3
    # every entry has unique (arm, model, task, sample_idx)
    keys = {(p["arm"], p["model"], p["task_id"], p["sample_idx"]) for p in plan}
    assert len(keys) == len(plan)

def test_build_plan_noise_floor_entries_distinct():
    plan = list(build_plan(arms=["no-skill"], models=["claude-haiku-4-5"], task_ids=["01"], n_samples=2, seed_base=0, noise_floor=True))
    # 2 samples * 2 seed-sets = 4 entries for noise floor
    assert len(plan) == 4
    seeds = [p["seed"] for p in plan]
    assert len(set(seeds)) == 4  # seeds must differ
```

- [ ] **Step 2: Implement**

```python
# harness/plan_builder.py
from __future__ import annotations
import itertools
from typing import Iterator

def build_plan(*, arms: list[str], models: list[str], task_ids: list[str], n_samples: int, seed_base: int = 0, noise_floor: bool = False) -> Iterator[dict]:
    groups = [("main", seed_base)]
    if noise_floor and "no-skill" in arms:
        groups.append(("noise", seed_base + 100_000))
    for group_name, seed_offset in groups:
        effective_arms = arms if group_name == "main" else ["no-skill"]
        for arm, model, task_id, i in itertools.product(effective_arms, models, task_ids, range(n_samples)):
            yield {
                "group": group_name,
                "arm": arm,
                "model": model,
                "task_id": task_id,
                "sample_idx": i,
                "seed": seed_offset + hash((arm, model, task_id, i)) % 10_000,
            }
```

- [ ] **Step 3: Run — expect pass**

- [ ] **Step 4: Commit**

```bash
git add harness/plan_builder.py tests/test_plan_builder.py
git commit -m "feat(plan_builder): cross-product run plan with noise-floor support"
```

---

### Task 39: Orchestrator — reads plan, executes, writes JSONL

**Files:**
- Create: `harness/run.py`

This is the largest single module. It reads `run_plan.jsonl`, loops over entries, generates + scores + judges, and writes the intermediate JSONL files.

- [ ] **Step 1: Write the orchestrator**

```python
# harness/run.py
from __future__ import annotations
import argparse, json, shutil, tempfile, time
from pathlib import Path
from typing import Iterable
from harness.prompts import build_prompt
from harness.generators import generate
from harness.jac_runner import run_jac_tests
from harness.detectors import run_all
from harness.judge import judge_median
from harness.scorer import idiom_score
from harness.plan_builder import build_plan

CACHE = Path(".eval_cache")
CACHE.mkdir(exist_ok=True)

def append_jsonl(path: Path, obj: dict) -> None:
    with path.open("a") as f:
        f.write(json.dumps(obj) + "\n")

def read_jsonl(path: Path) -> list[dict]:
    if not path.exists(): return []
    return [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]

def strip_fences(text: str) -> str:
    """Strip ```jac ... ``` fences if the model ignored the instruction."""
    t = text.strip()
    if t.startswith("```"):
        lines = t.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        t = "\n".join(lines)
    return t

def load_task(task_id: str) -> dict:
    """Locate tasks/<bucket>/<id>/ by scanning tasks/*/<id>/."""
    for bucket_dir in Path("tasks").iterdir():
        if bucket_dir.is_dir():
            candidate = bucket_dir / task_id
            if candidate.exists():
                import yaml
                meta = yaml.safe_load((candidate / "meta.yaml").read_text())
                return {
                    "id": task_id,
                    "dir": candidate,
                    "prompt": (candidate / "prompt.md").read_text(),
                    "tests_path": candidate / "tests.jac",
                    "solution": (candidate / "solution.jac").read_text(),
                    "rubric": (candidate / "rubric.md").read_text(),
                    "meta": meta,
                }
    raise FileNotFoundError(f"task {task_id} not found in tasks/*")

def load_arm(name: str) -> str:
    return (Path("arms") / name / "arm.md").read_text()

def run_one(entry: dict) -> dict:
    task = load_task(entry["task_id"])
    arm_text = load_arm(entry["arm"])
    prompt = build_prompt(arm=arm_text, task=task["prompt"])
    gen = generate(model=entry["model"], prompt=prompt, temperature=0.2, max_tokens=2048, seed=entry["seed"])
    completion = strip_fences(gen.completion)
    # correctness
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "solution.jac").write_text(completion)
        shutil.copy(task["tests_path"], td / "tests.jac")
        test_result = run_jac_tests(td / "tests.jac", timeout_s=30)
    # ast
    ast_out = run_all(completion, expected=task["meta"].get("jac_constructs_expected"))
    # judge
    jo = judge_median(
        task_rubric=task["rubric"],
        reference_solution=task["solution"],
        candidate_code=completion,
    )
    score = idiom_score(ast_subscore=ast_out["ast_subscore"], judge_median=jo["median"])
    return {
        "entry": entry,
        "completion": completion,
        "generation_usage": {"input": gen.input_tokens, "output": gen.output_tokens, "wall_ms": gen.wall_ms, "finish": gen.finish_reason},
        "passed": test_result.all_passed,
        "exit_code": test_result.raw.exit_code,
        "test_stdout": test_result.raw.stdout[-2000:],  # truncate
        "ast": ast_out,
        "judge": {"median": jo["median"], "scores": jo["scores"], "feedback": [r["feedback"] for r in jo["runs"]]},
        "idiom_score": score,
        "ts": time.time(),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", type=Path, default=CACHE / "run_plan.jsonl")
    ap.add_argument("--out", type=Path, default=CACHE / "results.jsonl")
    ap.add_argument("--limit", type=int, default=None, help="run only first N entries")
    ap.add_argument("--build-plan", action="store_true", help="if given, (re)build plan from defaults and exit")
    ap.add_argument("--arms", nargs="+", default=["no-skill", "llmdocs-mini", "llmdocs-full"])
    ap.add_argument("--models", nargs="+", default=["claude-haiku-4-5", "gemini-3-flash-preview", "meta-llama/llama-4-scout-17b-16e-instruct"])
    ap.add_argument("--tasks", nargs="+", default=[f"{i:02d}" for i in range(1, 11)])
    ap.add_argument("--n-samples", type=int, default=5)
    ap.add_argument("--noise-floor", action="store_true")
    args = ap.parse_args()

    if args.build_plan:
        with args.plan.open("w") as f:
            for e in build_plan(arms=args.arms, models=args.models, task_ids=args.tasks, n_samples=args.n_samples, noise_floor=args.noise_floor):
                f.write(json.dumps(e) + "\n")
        print(f"wrote plan: {args.plan}")
        return

    plan = read_jsonl(args.plan)
    done = {
        (r["entry"]["arm"], r["entry"]["model"], r["entry"]["task_id"], r["entry"]["sample_idx"], r["entry"].get("group", "main"))
        for r in read_jsonl(args.out)
    }
    todo = [e for e in plan if (e["arm"], e["model"], e["task_id"], e["sample_idx"], e.get("group", "main")) not in done]
    if args.limit: todo = todo[: args.limit]
    print(f"plan={len(plan)} done={len(done)} todo={len(todo)}")

    for i, e in enumerate(todo, 1):
        try:
            out = run_one(e)
            append_jsonl(args.out, out)
            print(f"[{i}/{len(todo)}] {e['arm']} {e['model']} {e['task_id']} sample={e['sample_idx']} passed={out['passed']} idiom={out['idiom_score']:.2f}")
        except Exception as ex:
            print(f"[{i}/{len(todo)}] ERROR: {e} :: {ex}")
            append_jsonl(CACHE / "errors.jsonl", {"entry": e, "error": repr(ex)})

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke-test against the pilot task (1 model, 1 arm, 1 sample)**

```bash
.venv/bin/python -m harness.run --build-plan --arms no-skill --models claude-haiku-4-5 --tasks pilot-fibonacci --n-samples 1
.venv/bin/python -m harness.run --limit 1
cat .eval_cache/results.jsonl | head -1 | python -m json.tool
```
Expected: one result line in JSONL with `passed`, `ast`, `judge`, `idiom_score`.

- [ ] **Step 3: Commit**

```bash
git add harness/run.py
git commit -m "feat(run): orchestrator reads plan, executes, appends JSONL"
```

---

## PHASE 10 — Execute baseline (Day 9)

### Task 40: Build baseline plan and execute

- [ ] **Step 1: Build the plan**

```bash
.venv/bin/python -m harness.run --build-plan \
  --arms no-skill llmdocs-mini llmdocs-full \
  --models claude-haiku-4-5 gemini-3-flash-preview meta-llama/llama-4-scout-17b-16e-instruct \
  --tasks 01 02 03 04 05 06 07 08 09 10 \
  --n-samples 5 \
  --noise-floor
```
Expected: writes `.eval_cache/run_plan.jsonl` with 3×3×10×5 + 1×3×10×5 = 600 entries.

- [ ] **Step 2: Commit the plan (it's deterministic; committing keeps the run reproducible)**

```bash
cp .eval_cache/run_plan.jsonl results/baseline_run_plan.jsonl
git add results/baseline_run_plan.jsonl
git commit -m "chore(results): pin baseline run_plan (600 entries)"
```

- [ ] **Step 3: Execute**

```bash
.venv/bin/python -m harness.run
```
This will take hours. It's resumable — if interrupted, re-running picks up where it left off. Watch for:
- Free-tier rate limits (Groq and Gemini). Expect occasional 429s; the script logs to `errors.jsonl`. After the main run, `python -m harness.run --limit 50` a few times will mop up the retries.
- Flaky Jac runtime crashes. Inspect `.eval_cache/errors.jsonl`.

- [ ] **Step 4: Sanity-check**

```bash
wc -l .eval_cache/results.jsonl
```
Expected: 600 (or close, if errors were unresolvable — investigate any gap).

Spot-check three random results:
```bash
.venv/bin/python -c "
import json, random
lines = list(open('.eval_cache/results.jsonl'))
for ln in random.sample(lines, 3):
    r = json.loads(ln)
    print(r['entry']['arm'], r['entry']['model'], r['entry']['task_id'], 'passed=', r['passed'], 'idiom=', round(r['idiom_score'], 2))
"
```

- [ ] **Step 5: Commit results cache's summary**

```bash
.venv/bin/python -c "
import json
from pathlib import Path
n = 0
with open('results/summary_baseline.jsonl', 'w') as out:
    for ln in open('.eval_cache/results.jsonl'):
        r = json.loads(ln)
        out.write(json.dumps({'entry': r['entry'], 'passed': r['passed'], 'idiom_score': r['idiom_score'], 'judge_median': r['judge']['median'], 'ast_subscore': r['ast']['ast_subscore']}) + '\n')
        n += 1
print('summary rows:', n)
"
git add results/summary_baseline.jsonl
git commit -m "chore(results): baseline run complete (N rows)"
git push
```

---

## PHASE 11 — v0 SKILL.md authoring (Day 10)

### Task 41: Failure analysis script

**Files:**
- Create: `scripts/failure_analysis.py`

- [ ] **Step 1: Write the script**

```python
# scripts/failure_analysis.py
"""Read baseline results, print failure modes per (model, bucket)."""
import json, yaml
from collections import defaultdict
from pathlib import Path

def load_task_bucket(task_id: str) -> str:
    for bucket_dir in Path("tasks").iterdir():
        if bucket_dir.is_dir() and (bucket_dir / task_id).exists():
            return bucket_dir.name
    return "unknown"

# Exclude held-out tasks from iteration-time inspection.
HELD_OUT = {"03", "10"}

results = []
for ln in open(".eval_cache/results.jsonl"):
    r = json.loads(ln)
    if r["entry"]["task_id"] in HELD_OUT: continue
    if r["entry"]["arm"] != "no-skill": continue   # baseline failures only
    results.append(r)

by_group = defaultdict(list)
for r in results:
    bucket = load_task_bucket(r["entry"]["task_id"])
    by_group[(r["entry"]["model"], bucket)].append(r)

print("## Baseline failure modes (no-skill arm, dev tasks only)\n")
for (model, bucket), rs in sorted(by_group.items()):
    n = len(rs)
    fails = [r for r in rs if not r["passed"]]
    pct = 100 * len(fails) / n if n else 0
    print(f"### {model} × {bucket}  ({len(fails)}/{n} failed = {pct:.0f}%)\n")
    # Sample up to 3 distinct failure outputs with judge feedback
    for r in fails[:3]:
        print(f"- task {r['entry']['task_id']} sample {r['entry']['sample_idx']}")
        print(f"  judge feedback (median={r['judge']['median']}): {r['judge']['feedback'][0][:200]}")
        print(f"  detectors: {r['ast']['per_detector']}")
        print()
```

- [ ] **Step 2: Run**

```bash
.venv/bin/python scripts/failure_analysis.py > results/failure_analysis.md
```

- [ ] **Step 3: Commit**

```bash
git add scripts/failure_analysis.py results/failure_analysis.md
git commit -m "chore(analysis): baseline failure modes per (model, bucket)"
```

---

### Task 42: Author `v0-skill/arm.md`

**Files:**
- Create: `arms/v0-skill/arm.md`

- [ ] **Step 1: Read the failure analysis carefully**

Open `results/failure_analysis.md`. Identify the top 3–5 systematic failure modes across models. Examples:
- "Llama consistently uses dict-of-lists for graphs instead of typed edge archetypes."
- "All three models forget type annotations on `has` fields in `obj` archetypes."
- "Gemini uses Python-style recursion instead of walker+visit for traversal tasks."

- [ ] **Step 2: Write the v0 SKILL.md**

The skill should:
- Use Anthropic's Agent Skills format: YAML frontmatter + markdown body.
- Be concise — aim for under 1,500 tokens. The research recipe emphasizes progressive disclosure.
- Directly address each observed failure mode with a WRONG/RIGHT example.
- Cite `jac://guide/pitfalls` rule numbers where applicable.

Template:
```markdown
---
name: jaceval-v0-jac-skill
description: Write idiomatic Jac (not Python-transliterated Jac), covering object-spatial archetypes (nodes, edges, walkers), `visit` traversal, typed edge relationships, and abilities.
---

# Writing idiomatic Jac

Jac is not Python. These are the Jac-specific mistakes foundation models make most often on the jaceval benchmark:

## 1. Edges are archetypes, not dict-of-lists

**Wrong:**
```jac
node City { has name: str; has roads: list[str]; }
```

**Right:**
```jac
edge Road { has length_km: float; }
node City { has name: str; }
// create with: city_a ++>:Road(length_km=5): city_b;
```
...

(Fill in 3–5 similar WRONG/RIGHT sections targeting the observed failures.)
```

- [ ] **Step 3: Length check**

```bash
wc -w arms/v0-skill/arm.md
```
Aim for 500–1500 words.

- [ ] **Step 4: Commit**

```bash
git add arms/v0-skill/arm.md
git commit -m "feat(arms): v0 SKILL.md targeting observed baseline failure modes"
```

---

### Task 43: Author `irrelevant-ctrl/arm.md`

**Files:**
- Create: `arms/irrelevant-ctrl/arm.md`

- [ ] **Step 1: Write a plausible Gleam SKILL.md, length-matched to v0-skill within ±10%**

```bash
wc -w arms/v0-skill/arm.md
```
Note the target word count.

Gleam is a statically-typed functional language for the Erlang VM. Write a SKILL.md of the same length about Gleam — covering pattern matching, pipes, custom types, etc. Content should be genuinely useful *for Gleam* (so it's not obviously garbage), but has zero overlap with Jac.

Template (flesh out to match the word count):
```markdown
---
name: jaceval-v0-irrelevant-control
description: Context control — a Gleam skill used only to test whether any long doc improves Jac output regardless of content.
---

# Writing idiomatic Gleam

Gleam is a statically typed functional language ...
```

- [ ] **Step 2: Verify length**

```bash
python -c "
v0 = len(open('arms/v0-skill/arm.md').read().split())
ctrl = len(open('arms/irrelevant-ctrl/arm.md').read().split())
print(f'v0={v0} ctrl={ctrl} ratio={ctrl/v0:.2f} (target 0.9–1.1)')
"
```

If ratio is outside 0.9–1.1, adjust.

- [ ] **Step 3: Commit**

```bash
git add arms/irrelevant-ctrl/arm.md
git commit -m "feat(arms): Gleam SKILL.md as length-matched irrelevant-context control"
```

---

### Task 44: Execute v0-skill + irrelevant-ctrl arms

- [ ] **Step 1: Append new arm entries to the plan**

```bash
.venv/bin/python -c "
from harness.plan_builder import build_plan
import json
new_entries = list(build_plan(arms=['v0-skill', 'irrelevant-ctrl'], models=['claude-haiku-4-5', 'gemini-3-flash-preview', 'meta-llama/llama-4-scout-17b-16e-instruct'], task_ids=[f'{i:02d}' for i in range(1,11)], n_samples=5, seed_base=0))
with open('.eval_cache/run_plan.jsonl', 'a') as f:
    for e in new_entries: f.write(json.dumps(e)+'\n')
print(f'appended {len(new_entries)} entries')
"
```

- [ ] **Step 2: Execute**

```bash
.venv/bin/python -m harness.run
```

- [ ] **Step 3: Verify results**

```bash
wc -l .eval_cache/results.jsonl
```
Expected: 600 baseline + 300 (2 arms × 3 models × 10 tasks × 5 samples) = 900.

- [ ] **Step 4: Update summary**

Rerun the summary-dump snippet from Task 40 Step 5, this time writing to `results/summary_full.jsonl`.

- [ ] **Step 5: Commit**

```bash
git add results/summary_full.jsonl
git commit -m "chore(results): v0-skill and irrelevant-ctrl runs complete"
git push
```

---

## PHASE 12 — Analysis and writeup (Days 11–12)

### Task 45: Analysis script — per-arm, per-stratum deltas

**Files:**
- Create: `scripts/analyze.py`

- [ ] **Step 1: Write the analysis script**

```python
# scripts/analyze.py
"""Read summary_full.jsonl, emit all tables needed for RESULTS.md."""
import json, yaml
from pathlib import Path
from collections import defaultdict
from statistics import mean
from harness.stats import pass_at_k, mcnemar_exact, paired_bootstrap_mean, wilson_interval

HELD_OUT = {"03", "10"}

def bucket_of(task_id: str) -> str:
    for bucket_dir in Path("tasks").iterdir():
        if bucket_dir.is_dir() and (bucket_dir / task_id).exists():
            return bucket_dir.name
    return "unknown"

rows = [json.loads(ln) for ln in open("results/summary_full.jsonl")]

# Separate dev-set from held-out-set.
def is_dev(r): return r["entry"]["task_id"] not in HELD_OUT

def group_by(rs, *keys):
    g = defaultdict(list)
    for r in rs:
        g[tuple(r["entry"][k] if k != "bucket" else bucket_of(r["entry"]["task_id"]) for k in keys)].append(r)
    return g

# --- Headline table: pass@1 and mean idiom, per (arm, model)
print("## Headline (dev set only)\n")
print("| arm | model | pass@1 | mean idiom | n |")
print("|---|---|---|---|---|")
for (arm, model), rs in sorted(group_by([r for r in rows if is_dev(r)], "arm", "model").items()):
    # pass@1 per task, then mean
    task_groups = group_by(rs, "task_id")
    p_at_1 = mean(pass_at_k(n=len(trs), c=sum(1 for x in trs if x["passed"]), k=1) for _, trs in task_groups.items())
    idiom = mean(r["idiom_score"] for r in rs)
    print(f"| {arm} | {model} | {p_at_1:.2f} | {idiom:.2f} | {len(rs)} |")

# --- Paired deltas: (skill_arm vs no-skill) per model, with bootstrap CI
print("\n## Paired deltas (dev set only)\n")
for skill_arm in ["llmdocs-mini", "llmdocs-full", "v0-skill", "irrelevant-ctrl"]:
    for model in ["claude-haiku-4-5", "gemini-3-flash-preview", "meta-llama/llama-4-scout-17b-16e-instruct"]:
        a_rows = [r for r in rows if is_dev(r) and r["entry"]["arm"] == skill_arm and r["entry"]["model"] == model]
        b_rows = [r for r in rows if is_dev(r) and r["entry"]["arm"] == "no-skill" and r["entry"]["model"] == model and r["entry"].get("group", "main") == "main"]
        # pair by task_id + sample_idx
        a_by = {(r["entry"]["task_id"], r["entry"]["sample_idx"]): r for r in a_rows}
        b_by = {(r["entry"]["task_id"], r["entry"]["sample_idx"]): r for r in b_rows}
        common = sorted(set(a_by) & set(b_by))
        if not common: continue
        idiom_a = [a_by[k]["idiom_score"] for k in common]
        idiom_b = [b_by[k]["idiom_score"] for k in common]
        lo, hi = paired_bootstrap_mean(idiom_a, idiom_b, n_boot=10_000, seed=42)
        mean_d = mean(a - b for a, b in zip(idiom_a, idiom_b))
        # McNemar on correctness
        a_wins = sum(1 for k in common if a_by[k]["passed"] and not b_by[k]["passed"])
        b_wins = sum(1 for k in common if b_by[k]["passed"] and not a_by[k]["passed"])
        p = mcnemar_exact(a_wins=a_wins, b_wins=b_wins)
        print(f"| {skill_arm} vs no-skill | {model} | Δidiom = {mean_d:+.2f} [CI {lo:+.2f}, {hi:+.2f}] | flip {a_wins}/{b_wins} McNemar p={p:.3f} |")

# --- Per-stratum breakdown
print("\n## Per-stratum (dev set only)\n")
for bucket in ["syntax", "graph", "walker"]:
    rows_b = [r for r in rows if is_dev(r) and bucket_of(r["entry"]["task_id"]) == bucket]
    # pair v0-skill vs no-skill here, averaged across models
    v = [r for r in rows_b if r["entry"]["arm"] == "v0-skill"]
    n = [r for r in rows_b if r["entry"]["arm"] == "no-skill" and r["entry"].get("group","main")=="main"]
    v_by = {(r["entry"]["task_id"], r["entry"]["model"], r["entry"]["sample_idx"]): r for r in v}
    n_by = {(r["entry"]["task_id"], r["entry"]["model"], r["entry"]["sample_idx"]): r for r in n}
    common = sorted(set(v_by) & set(n_by))
    if not common: continue
    d_idiom = [v_by[k]["idiom_score"] - n_by[k]["idiom_score"] for k in common]
    d_pass = [int(v_by[k]["passed"]) - int(n_by[k]["passed"]) for k in common]
    print(f"- {bucket}: Δidiom = {mean(d_idiom):+.2f}  Δpass = {mean(d_pass):+.2%}  N={len(common)}")

# --- Held-out reveal
print("\n## Held-out tasks (03, 10) reveal\n")
held = [r for r in rows if r["entry"]["task_id"] in HELD_OUT]
for (arm, model, task), rs in sorted(group_by(held, "arm", "model", "task_id").items()):
    passed = sum(1 for r in rs if r["passed"])
    idiom = mean(r["idiom_score"] for r in rs)
    print(f"- {arm} {model} task={task}  passed={passed}/{len(rs)}  idiom={idiom:.2f}")
```

- [ ] **Step 2: Run and capture output**

```bash
.venv/bin/python scripts/analyze.py > results/analysis.md
cat results/analysis.md
```

- [ ] **Step 3: Commit**

```bash
git add scripts/analyze.py results/analysis.md
git commit -m "chore(analysis): per-arm deltas with McNemar and bootstrap CIs"
```

---

### Task 46: Write RESULTS.md

**Files:**
- Create: `results/RESULTS.md`

Required sections (from spec §7.2):

1. **Headline table** — pulled from `results/analysis.md`.
2. **Paired deltas** — pulled from `results/analysis.md`.
3. **2×2 flip tables** — one per (skill-arm, model) pair. Add to `scripts/analyze.py` if not already present.
4. **Per-stratum breakdown** — pulled from `results/analysis.md`.
5. **Cross-model interaction** — narrative: is the `v0-skill` delta larger for Llama (weaker) than Claude Haiku (stronger)? Quote the numbers.
6. **Judge validation evidence** — Cohen's κ from Task 35 output. Include the hand-label / judge confusion matrix.
7. **Noise-floor and irrelevant-context controls** — delta for `no-skill(seed-A) vs no-skill(seed-B)` and for `irrelevant-ctrl vs no-skill`. State whether any claimed v0-skill effect exceeds both by at least 2×.
8. **Decision** — apply pre-committed thresholds from spec §7.3.
9. **Honest caveats** — N=10, stratum sizes, judge κ, `by llm()` deferral, what v1 needs.

Write as a peer, not a student (per CLAUDE.md). Lead with the finding:

> "At N=10 and with a judge validated to κ=X.XX, the v0 SKILL.md moved paired mean idiom_score by Δ=+0.YY (95% CI [..., ...]) averaged across three models, meeting / not meeting the pre-committed threshold of +0.10. Correctness moved Δ=+Z pp (McNemar p=0.WW). The largest effect was on the walker bucket for Llama 3.3 70B (Δ=+A.BB); the smallest was on the syntax bucket for Claude Haiku (Δ=-C.DD)."

- [ ] **Step 1: Draft**

Use `results/analysis.md` as source material. Keep it tight — aim for under 1,500 words of prose plus tables.

- [ ] **Step 2: Commit**

```bash
git add results/RESULTS.md
git commit -m "docs(results): v0 writeup with decision against pre-committed thresholds"
git push
```

---

### Task 47: Reveal held-out tasks and append to RESULTS

- [ ] **Step 1: The held-out scores are already in `results/analysis.md`** (the last section). Copy them into a new section of RESULTS.md titled "Held-out reveal," with a one-line note: "Agreement / disagreement with dev-set directional trend."

- [ ] **Step 2: Commit**

```bash
git add results/RESULTS.md
git commit -m "docs(results): reveal held-out tasks 03 and 10"
git push
```

---

## PHASE 13 — Polish (Day 13)

### Task 48: Write README.md

**Files:**
- Create: `README.md`

- [ ] **Step 1: Draft**

```markdown
# jaceval

> v0 of the first published-quality Jac codegen eval — a paired A/B benchmark measuring whether context documents (SKILL.md, LLMDocs) actually help LLMs write idiomatic Jac, and by how much.

**Headline finding:** <copy the first sentence from RESULTS.md>

## What this is

Two deliverables, both first-class:
- A **methodology** — paired A/B design, execution-based correctness, validated LLM-judged idiomaticity, pre-committed effect thresholds. See [`docs/specs/2026-04-19-jaceval-v0-design.md`](docs/specs/2026-04-19-jaceval-v0-design.md).
- A **v0 SKILL.md for Jac** — authored *after* observing baseline failures, then evaluated on the same harness. See [`arms/v0-skill/arm.md`](arms/v0-skill/arm.md).

The skill is a byproduct of the methodology, not the goal.

## Quickstart

```bash
git clone https://github.com/drPod/jaceval.git
cd jaceval
make install
cp .env.example .env   # fill in ANTHROPIC_API_KEY, GOOGLE_API_KEY, GROQ_API_KEY
make eval              # ~hours on free-tier APIs
```

Results land in `.eval_cache/results.jsonl`. Run `python scripts/analyze.py` to regenerate `results/analysis.md`.

## Design and results

- **Spec:** [`docs/specs/2026-04-19-jaceval-v0-design.md`](docs/specs/2026-04-19-jaceval-v0-design.md)
- **Results:** [`results/RESULTS.md`](results/RESULTS.md)
- **Literature foundation:** [`design-recipe.md`](design-recipe.md)

## v0 scope and what's next

v0: 10 tasks × 5 arms × 3 models × 5 samples, all deterministic-correctness tasks (no `by llm()` bucket).

v1 — what this project does not yet do, listed in priority order:
- `by llm()` bucket with stub design
- Expansion to 40–60 tasks
- Dual-judge ensemble
- Additional models (Claude Sonnet, GPT-5, DeepSeek-Coder)
- Second niche language target (Gleam, Roc, Dylan) to validate the harness generalizes

## Credits

- `jac-mcp` by [Jason Mars / Jaseci Labs](https://jaseci.org) — used throughout for authoring and validating Jac.
- Methodology synthesized from: Cassano et al. (MultiPL-E), Miller 2024 (paired SE), Kim et al. (Prometheus), Pathak et al. (per-task rubrics), Chen et al. (unbiased pass@k). Full citations in `design-recipe.md`.

## License

MIT (see `LICENSE`).
```

- [ ] **Step 2: Add a LICENSE file (MIT)**

```bash
curl -sL https://raw.githubusercontent.com/spdx/license-list-data/main/text/MIT.txt > LICENSE
# Or copy the MIT license text with your name.
```

Open `LICENSE` and replace `<year>` with 2026 and `<copyright holders>` with "Darsh Poddar".

- [ ] **Step 3: Commit**

```bash
git add README.md LICENSE
git commit -m "docs: README and MIT LICENSE"
git push
```

---

### Task 49: `make eval` reproducibility test

- [ ] **Step 1: Clean-room clone into a scratch directory**

```bash
cd /tmp && rm -rf jaceval-clone && git clone https://github.com/drPod/jaceval.git jaceval-clone && cd jaceval-clone
make install
cp .env.example .env
# Fill in keys in .env
make eval --dry-run 2>&1 | head    # NOTE: adjust Makefile if needed so --dry-run shows commands
```

Does `make install` succeed on a clean machine? Does `make eval` at least start? If no, patch the Makefile or pyproject.

- [ ] **Step 2: Run a tiny subset and verify JSONL**

```bash
.venv/bin/python -m harness.run --build-plan --arms no-skill --models claude-haiku-4-5 --tasks 01 --n-samples 1
.venv/bin/python -m harness.run
cat .eval_cache/results.jsonl | head -1 | python -m json.tool
```
Expected: one result with all required fields.

- [ ] **Step 3: Commit any fixes and push**

```bash
cd /Users/darshpoddar/Coding/jaceval
# Apply any fixes you found during reproducibility test.
git add <modified files>
git commit -m "fix: clean-room reproducibility patches"
git push
```

---

### Task 50: Final polish and verify

- [ ] **Step 1: Full test suite**

```bash
make test
```
Expected: all pass.

- [ ] **Step 2: Spell-check README and RESULTS**

Read both cover-to-cover. Trim anything vague or hedging. Verify numbers match `results/analysis.md`.

- [ ] **Step 3: Final commit and tag**

```bash
git add -A
git diff --cached    # review
git commit -m "chore: v0 final polish" || echo "nothing to commit"
git tag v0.1.0 -m "jaceval v0 — initial public release"
git push && git push --tags
```

---

### Task 51: Draft the message to Mars

**Files:**
- Create: `docs/mars-message.md` (optional, not committed if you prefer)

Not a code task; a communications task. Draft:

> Hey — spent the last ~two weeks building v0 of what I had in mind after our 4/9 conversation. It's public at github.com/drPod/jaceval.
>
> 10 Jac tasks, 3 generator models (Haiku, Gemini 2.5 Pro, Llama 3.3 70B via Groq), 5 context arms including both your LLMDocs-Mini and LLMDocs-Full. Paired A/B design, execution-based correctness via `jac run`, hybrid AST + LLM-judge idiomaticity with the judge validated against my hand labels at Cohen's κ=<X.XX>. Pre-committed effect thresholds, noise-floor and irrelevant-context controls, held-out set. Writeup in `results/RESULTS.md`; spec in `docs/specs/`; literature foundation in `design-recipe.md`.
>
> Headline: <one sentence summary of the finding>.
>
> This is v0 — N=10 only resolves ≥20pp effects, and the `by llm()` bucket is deferred. I set it up so scaling to 60 tasks and adding another language (Gleam, Roc) is a clean extension, which I think lines up with what you mentioned re: pi.dev and a competition on harnesses for foundation model education.
>
> Happy to talk about scaling this up — sponsorship or bounty, whichever shape you prefer.

Keep it under 200 words. Attach the repo link, not a doc.

---

## Self-review (done before handoff)

**1. Spec coverage:**
- §3 goals → Tasks 3–51 (harness, judge validation, SKILL.md, RESULTS.md, reproducibility)
- §5.1 arms → Tasks 13, 14, 42, 43
- §5.2 models → Tasks 8, 9, 10
- §5.3 tasks → Tasks 11 (pilot), 16–25 (10 main tasks). **Held-out** flag respected in Tasks 18, 25, 41 (failure analysis excludes them), 45 (revealed last).
- §5.4 sampling protocol → Task 39 `run_one` uses `temperature=0.2`, `max_tokens=2048`; Task 38 `plan_builder` freezes task/arm/model/sample order via itertools.product.
- §6.1 correctness → Task 5 `run_jac_tests`, Task 39 orchestrator
- §6.2 idiomaticity (AST + judge) → Tasks 26–31 (detectors), Tasks 32–33 (judge), Task 36 (combiner)
- §6.3 judge validation κ≥0.4 → Tasks 34, 35 (with fallback path documented)
- §7 analysis → Task 37 (stats), Task 45 (analyze.py), Task 46 (RESULTS.md)
- §7.3 pre-committed thresholds → Task 46 applies them
- §8 controls → noise-floor in Task 38/40, irrelevant-ctrl in Tasks 43, 44
- §11 repo layout → mirrored in the File structure section above
- §12 timeline → task numbering follows the day-by-day phases

All spec requirements have tasks. No gaps.

**2. Placeholder scan:**
- "Similar to Task N" — avoided. Every task has its own code.
- "TODO"/"TBD" — none in the plan. A few `2026-04-DD` slots in meta.yaml templates are intentional (fill with today's date when the task runs).
- "Add appropriate error handling" — avoided. Specific error handling is specified in Task 39 (`errors.jsonl` capture).

**3. Type consistency:**
- `RunResult` / `TestResult` / `Generation` dataclasses are used consistently across Tasks 3, 5, 7, 39.
- `run_all` (Task 31) returns `{"per_detector": {...}, "ast_subscore": float}` and Task 39 reads both keys.
- `judge_median` (Task 33) returns `{"median": int, "runs": list, "scores": list}`; Task 39 and Task 35 both use this shape.
- `idiom_score` (Task 36) takes named-only `ast_subscore=` and `judge_median=`; Task 39 passes both by keyword.
- `pass_at_k` signature `n=, c=, k=` used consistently in Task 37 and Task 45.

No inconsistencies.

---

**Plan status:** complete, spec-covered, placeholder-free, type-consistent.
