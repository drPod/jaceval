"""GPT-OSS 120B via Groq as a Jac idiomaticity judge.

Loads the Prometheus-format prompt template from `judge/prompt.md`, fills in the
task rubric, reference solution, and candidate code, calls the judge model three
times, and returns per-run dicts + the median score. The judge is deliberately
non-Anthropic, non-Google, and non-Meta so it can't self-prefer any of the three
generator families in the eval.
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from statistics import median

PROMPT_TEMPLATE = Path(__file__).resolve().parent.parent.joinpath("judge/prompt.md").read_text()
_RESULT_RE = re.compile(r"\[RESULT\]\s*([1-5])")
_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)

JUDGE_MODEL = "openai/gpt-oss-120b"


def _call_judge(prompt: str, *, temperature: float = 0.3, max_tokens: int = 1024, seed: int = 0) -> str:
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


def judge_once(*, task_rubric: str, reference_solution: str, candidate_code: str, seed: int | None = None) -> dict:
    prompt = PROMPT_TEMPLATE.format(
        task_rubric=task_rubric,
        reference_solution=reference_solution,
        candidate_code=candidate_code,
    )
    actual_seed = seed if seed is not None else int(time.time() * 1000) % 10_000
    text = _call_judge(prompt=prompt, temperature=0.3, max_tokens=1024, seed=actual_seed)
    m = _RESULT_RE.search(text)
    score = int(m.group(1)) if m else 1
    jm = _JSON_RE.search(text)
    parsed: dict = {}
    if jm:
        try:
            parsed = json.loads(jm.group(0))
        except Exception:
            parsed = {}
    return {
        "score": score,
        "feedback": parsed.get("feedback", text[:200]),
        "constructs_present": parsed.get("constructs_present", []),
        "raw": text,
    }


def judge_median(*, task_rubric: str, reference_solution: str, candidate_code: str) -> dict:
    runs = [
        judge_once(
            task_rubric=task_rubric,
            reference_solution=reference_solution,
            candidate_code=candidate_code,
            seed=i,
        )
        for i in range(3)
    ]
    scores = [r["score"] for r in runs]
    return {"median": int(median(scores)), "runs": runs, "scores": scores}
