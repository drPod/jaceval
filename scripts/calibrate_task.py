"""Sample N completions per generator on a task; report pass rates per model + aggregate.

Default runs the free-tier generators (Gemini 3 Flash Preview, Llama 4 Scout via Groq).
Pass --include-haiku to also sample Claude Haiku (paid). Pass --models to restrict.
"""
import argparse
import shutil
import tempfile
from pathlib import Path

from harness.generators import generate
from harness.jac_runner import run_jac_tests
from harness.prompts import build_prompt

FREE_MODELS = [
    "gemini-3-flash-preview",
    "meta-llama/llama-4-scout-17b-16e-instruct",
]
PAID_MODELS = ["claude-haiku-4-5"]


def sample_rate(task_dir: Path, model: str, n: int, prompt: str) -> tuple[int, int]:
    passes = 0
    for i in range(n):
        g = generate(model=model, prompt=prompt, temperature=0.2, max_tokens=2048, seed=i)
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            (td / "solution.jac").write_text(g.completion)
            shutil.copy(task_dir / "tests.jac", td / "tests.jac")
            result = run_jac_tests(td / "tests.jac", timeout_s=30)
            print(f"  [{model}] sample {i}: all_passed={result.all_passed}")
            if result.all_passed:
                passes += 1
    return passes, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task_dir", type=Path)
    ap.add_argument("--n", type=int, default=5, help="samples per model")
    ap.add_argument("--include-haiku", action="store_true", help="also sample Claude Haiku (paid)")
    ap.add_argument("--models", nargs="+", help="explicit model list (overrides defaults)")
    args = ap.parse_args()

    models = args.models or (FREE_MODELS + (PAID_MODELS if args.include_haiku else []))

    prompt_text = (args.task_dir / "prompt.md").read_text()
    no_skill_arm = Path("arms/no-skill/arm.md").read_text()
    full_prompt = build_prompt(arm=no_skill_arm, task=prompt_text)

    totals = []
    print(f"Calibrating {args.task_dir} against {len(models)} model(s), n={args.n} each:")
    for model in models:
        print(f"\n{model}:")
        passes, n = sample_rate(args.task_dir, model, args.n, full_prompt)
        rate = passes / n
        print(f"  rate: {passes}/{n} = {rate:.0%}")
        totals.append((model, passes, n))

    print("\nSUMMARY")
    total_passes = sum(p for _, p, _ in totals)
    total_n = sum(n for _, _, n in totals)
    for model, passes, n in totals:
        print(f"  {model}: {passes}/{n} = {passes / n:.0%}")
    agg = total_passes / total_n if total_n else 0.0
    print(f"  aggregate: {total_passes}/{total_n} = {agg:.0%}")
    if agg in (0.0, 1.0):
        print("WARN: aggregate pass rate at floor/ceiling — task may not discriminate.")


if __name__ == "__main__":
    main()
