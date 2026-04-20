"""jaceval orchestrator.

Reads a ``run_plan.jsonl`` produced by `harness.plan_builder.build_plan`, executes
each entry — generate, run the hidden tests in an isolated temp dir, run the AST
detectors, run the LLM judge against the task's own rubric, compose the hybrid
idiomaticity score — and appends the resulting record to ``results.jsonl``.

The results file is append-only and keyed by
``(group, arm, model, task_id, sample_idx)``; on restart the orchestrator skips
every plan entry whose key is already present, so the run is fully resumable.

A transient exception in any single entry is caught, recorded to
``.eval_cache/errors.jsonl``, and the orchestrator moves to the next entry
rather than aborting the whole run.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any

import yaml

from harness.detectors import run_all
from harness.generators import generate
from harness.jac_runner import run_jac_tests
from harness.judge import judge_median
from harness.plan_builder import build_plan
from harness.prompts import build_prompt
from harness.scorer import idiom_score

CACHE = Path(".eval_cache")
CACHE.mkdir(exist_ok=True)


def append_jsonl(path: Path, obj: dict) -> None:
    with path.open("a") as f:
        f.write(json.dumps(obj) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]


_FENCE_RE = re.compile(r"^```[\w]*\n|\n```\s*$")


def strip_fences(text: str) -> str:
    """Strip ``` ... ``` fences if the model ignored the output-format instruction."""
    t = text.strip()
    if t.startswith("```"):
        lines = t.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        t = "\n".join(lines)
    return t


_MULTI_BLANK_RE = re.compile(r"\n{3,}")


def normalize_for_judge(text: str) -> str:
    """Lightly normalise formatting before handing code to the judge.

    Strips trailing whitespace on each line, collapses runs of 3+ blank lines
    to a single blank line, and strips leading/trailing whitespace overall.
    Does NOT reformat indentation, strip comments, or reorder code — those
    are idiomaticity signal, not noise.
    """
    lines = [ln.rstrip() for ln in text.splitlines()]
    normalized = "\n".join(lines).strip()
    return _MULTI_BLANK_RE.sub("\n\n", normalized)


def load_task(task_id: str) -> dict[str, Any]:
    """Locate ``tasks/<bucket>/<task_id>/`` and load its components."""
    for bucket_dir in Path("tasks").iterdir():
        if not bucket_dir.is_dir():
            continue
        candidate = bucket_dir / task_id
        if candidate.exists():
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
    raise FileNotFoundError(f"task {task_id} not found under tasks/*/")


def load_arm(name: str) -> str:
    return (Path("arms") / name / "arm.md").read_text()


def run_one(entry: dict, *, skip_judge: bool = False) -> dict:
    task = load_task(entry["task_id"])
    arm_text = load_arm(entry["arm"])
    prompt = build_prompt(arm=arm_text, task=task["prompt"])

    gen = generate(
        model=entry["model"],
        prompt=prompt,
        temperature=0.2,
        max_tokens=2048,
        seed=entry["seed"],
    )
    completion = strip_fences(gen.completion)
    judge_input = normalize_for_judge(completion)

    with tempfile.TemporaryDirectory() as td_str:
        td = Path(td_str)
        (td / "solution.jac").write_text(completion)
        shutil.copy(task["tests_path"], td / "tests.jac")
        test_result = run_jac_tests(td / "tests.jac", timeout_s=30)

    ast_out = run_all(completion, expected=task["meta"].get("jac_constructs_expected"))

    record: dict[str, Any] = {
        "entry": entry,
        "completion": completion,
        "judge_input": judge_input,
        "generation_usage": {
            "input": gen.input_tokens,
            "output": gen.output_tokens,
            "wall_ms": gen.wall_ms,
            "finish": gen.finish_reason,
        },
        "passed": test_result.all_passed,
        "exit_code": test_result.raw.exit_code,
        "test_stdout": test_result.raw.stdout[-2000:],
        "ast": ast_out,
        "ts": time.time(),
    }

    if skip_judge:
        record["judge"] = None
        record["idiom_score"] = None
        return record

    try:
        jo = judge_median(
            task_rubric=task["rubric"],
            reference_solution=task["solution"],
            candidate_code=judge_input,
        )
        record["judge"] = {
            "median": jo["median"],
            "scores": jo["scores"],
            "feedback": [r["feedback"] for r in jo["runs"]],
        }
        record["idiom_score"] = idiom_score(
            ast_subscore=ast_out["ast_subscore"], judge_median=jo["median"]
        )
    except Exception as ex:
        # Judge failure must NOT lose the generation + test + AST work already
        # done. Persist the partial record and let `--judge-only` fill in the
        # judge result on a later run (after quota reset or judge swap).
        record["judge"] = {"error": repr(ex)}
        record["idiom_score"] = None

    return record


def rejudge_one(record: dict) -> dict:
    """Re-run the judge on a partial record that has completion + test + AST
    but no idiom score. Returns a new record with judge + idiom_score filled in.
    """
    task = load_task(record["entry"]["task_id"])
    jo = judge_median(
        task_rubric=task["rubric"],
        reference_solution=task["solution"],
        candidate_code=record["judge_input"],
    )
    new = dict(record)
    new["judge"] = {
        "median": jo["median"],
        "scores": jo["scores"],
        "feedback": [r["feedback"] for r in jo["runs"]],
    }
    new["idiom_score"] = idiom_score(
        ast_subscore=record["ast"]["ast_subscore"], judge_median=jo["median"]
    )
    new["ts_judge"] = time.time()
    return new


def _key(entry: dict) -> tuple:
    return (
        entry.get("group", "main"),
        entry["arm"],
        entry["model"],
        entry["task_id"],
        entry["sample_idx"],
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", type=Path, default=CACHE / "run_plan.jsonl")
    ap.add_argument("--out", type=Path, default=CACHE / "results.jsonl")
    ap.add_argument("--limit", type=int, default=None, help="run at most N entries")
    ap.add_argument("--build-plan", action="store_true", help="write the plan file and exit")
    ap.add_argument("--arms", nargs="+", default=["no-skill", "llmdocs"])
    ap.add_argument(
        "--models",
        nargs="+",
        default=[
            "claude-haiku-4-5",
            "gemini-3-flash-preview",
            "meta-llama/llama-4-scout-17b-16e-instruct",
        ],
    )
    ap.add_argument("--tasks", nargs="+", default=[f"{i:02d}" for i in range(1, 11)])
    ap.add_argument("--n-samples", type=int, default=5)
    ap.add_argument("--noise-floor", action="store_true")
    ap.add_argument(
        "--skip-judge",
        action="store_true",
        help="run generator + tests + AST only; leave judge/idiom_score null "
             "so they can be filled in later by --judge-only (useful when the "
             "judge provider has a daily quota cap).",
    )
    ap.add_argument(
        "--judge-only",
        action="store_true",
        help="re-read results JSONL, and for every record whose idiom_score is "
             "null, run judge + scorer and append an updated record.",
    )
    args = ap.parse_args()

    if args.build_plan:
        with args.plan.open("w") as f:
            for e in build_plan(
                arms=args.arms,
                models=args.models,
                task_ids=args.tasks,
                n_samples=args.n_samples,
                noise_floor=args.noise_floor,
            ):
                f.write(json.dumps(e) + "\n")
        print(f"wrote plan: {args.plan}")
        return

    if args.judge_only:
        existing = read_jsonl(args.out)
        needs = [r for r in existing if r.get("idiom_score") is None]
        print(f"records={len(existing)} need_judge={len(needs)}")
        if args.limit:
            needs = needs[: args.limit]
        # Stream in place: rewrite the out file with updated records,
        # preserving original order for deterministic downstream analysis.
        key_to_update: dict[tuple, dict] = {}
        for i, r in enumerate(needs, 1):
            try:
                new = rejudge_one(r)
                key_to_update[_key(r["entry"])] = new
                print(
                    f"[{i}/{len(needs)}] judged {r['entry']['arm']:18s} "
                    f"{r['entry']['task_id']:8s} sample={r['entry']['sample_idx']} "
                    f"idiom={new['idiom_score']:.2f}"
                )
            except Exception as ex:
                print(f"[{i}/{len(needs)}] JUDGE ERROR: {r['entry']} :: {ex}")
                append_jsonl(CACHE / "errors.jsonl", {"entry": r["entry"], "error": repr(ex)})
        # Rewrite the output file with merged records.
        merged = [key_to_update.get(_key(r["entry"]), r) for r in existing]
        with args.out.open("w") as f:
            for r in merged:
                f.write(json.dumps(r) + "\n")
        return

    plan = read_jsonl(args.plan)
    done = {_key(r["entry"]) for r in read_jsonl(args.out)}
    todo = [e for e in plan if _key(e) not in done]
    if args.limit:
        todo = todo[: args.limit]
    print(f"plan={len(plan)} done={len(done)} todo={len(todo)}")

    for i, e in enumerate(todo, 1):
        try:
            out = run_one(e, skip_judge=args.skip_judge)
            append_jsonl(args.out, out)
            idiom = out.get("idiom_score")
            idiom_s = f"{idiom:.2f}" if isinstance(idiom, float) else "—"
            print(
                f"[{i}/{len(todo)}] {e['arm']:18s} {e['model']:40s} "
                f"{e['task_id']:8s} sample={e['sample_idx']} "
                f"passed={out['passed']} idiom={idiom_s}"
            )
        except Exception as ex:
            print(f"[{i}/{len(todo)}] ERROR: {e} :: {ex}")
            append_jsonl(CACHE / "errors.jsonl", {"entry": e, "error": repr(ex)})


if __name__ == "__main__":
    main()
