import os

import pytest
from dotenv import load_dotenv

load_dotenv()

from harness.judge import judge_median, judge_once


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
