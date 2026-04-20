"""Run 5 samples of no-skill / Haiku on a task; report pass rate."""
import argparse
import tempfile
import shutil
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
        g = generate(
            model="claude-haiku-4-5",
            prompt=full_prompt,
            temperature=0.2,
            max_tokens=2048,
            seed=i,
        )
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            (td / "solution.jac").write_text(g.completion)
            shutil.copy(args.task_dir / "tests.jac", td / "tests.jac")
            result = run_jac_tests(td / "tests.jac", timeout_s=30)
            print(f"sample {i}: all_passed={result.all_passed}")
            if result.all_passed:
                passes += 1

    rate = passes / args.n
    print(f"\nBASELINE PASS RATE: {passes}/{args.n} = {rate:.0%}")
    if rate == 0.0 or rate == 1.0:
        print("WARN: task does not discriminate at baseline. Revise or reject.")


if __name__ == "__main__":
    main()
