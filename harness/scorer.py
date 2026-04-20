"""Combine the AST-detector subscore and the LLM-judge median into a single
idiomaticity score in [0, 1]. Weights per spec: 0.4 × AST + 0.6 × judge (where
the judge median 1-5 is normalised to 0.2-1.0).

Correctness is scored separately (binary pass/fail from `jac_runner`). The final
per-task score is composed in the orchestrator as 0.4 × correctness + 0.6 ×
idiomaticity.
"""
from __future__ import annotations


def idiom_score(*, ast_subscore: float, judge_median: int) -> float:
    """Return the hybrid idiomaticity score in [0, 1].

    ``ast_subscore`` is the mean over the task's expected detectors (0-1).
    ``judge_median`` is the 1-5 median of three judge runs; normalised by /5.
    """
    assert 0.0 <= ast_subscore <= 1.0
    assert 1 <= judge_median <= 5
    return 0.4 * ast_subscore + 0.6 * (judge_median / 5.0)
