"""Smoke tests for the mini-run analysis script. Sanity-checks the cuts on a
small synthetic JSONL so we know the math isn't obviously wrong before pointing
it at real results."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import analyze_mini  # noqa: E402


def _row(arm: str, task: str, sample: int, passed: bool, idiom: float, per_detector: dict) -> dict:
    return {
        "entry": {
            "group": "main",
            "arm": arm,
            "model": "llama",
            "task_id": task,
            "sample_idx": sample,
            "seed": 0,
        },
        "passed": passed,
        "idiom_score": idiom,
        "ast": {"per_detector": per_detector, "ast_subscore": sum(per_detector.values()) / len(per_detector)},
        "judge": {"median": 3, "scores": [3, 3, 3], "feedback": ["ok"] * 3},
    }


def _all_dets(walker: bool = False) -> dict:
    return {
        "uses_walker": walker,
        "uses_visit": walker,
        "uses_typed_edge_archetype": False,
        "uses_connect_op": False,
        "has_type_annotations": True,
        "uses_abilities_on_nodes": False,
    }


def test_cut_1_computes_pass_rate_and_idiom_mean():
    rows = [
        _row("no-skill", "01", 0, False, 0.12, _all_dets()),
        _row("no-skill", "01", 1, False, 0.12, _all_dets()),
        _row("v0-skill", "01", 0, True, 0.80, _all_dets(walker=True)),
        _row("v0-skill", "01", 1, True, 0.80, _all_dets(walker=True)),
    ]
    grouped = analyze_mini.group_by(rows)
    out = analyze_mini.cut_1_per_arm_summary(grouped)
    assert out["no-skill"]["pass_rate"] == 0.0
    assert out["v0-skill"]["pass_rate"] == 1.0
    assert abs(out["v0-skill"]["idiom_mean"] - 0.80) < 1e-9


def test_cut_3_per_detector_rates():
    rows = [
        _row("no-skill", "01", 0, False, 0.12, _all_dets()),
        _row("v0-skill", "01", 0, True, 0.80, _all_dets(walker=True)),
        _row("v0-skill", "01", 1, True, 0.80, _all_dets(walker=True)),
    ]
    grouped = analyze_mini.group_by(rows)
    out = analyze_mini.cut_3_per_construct(grouped)
    assert out["no-skill"]["uses_walker"] == 0.0
    assert out["v0-skill"]["uses_walker"] == 1.0
    assert out["no-skill"]["has_type_annotations"] == 1.0


def test_cut_4_dissociation_detects_pass_without_idiom():
    # Arm that passes tests with low idiom → dissociation > 0.
    rows = [
        _row("tricky", "01", 0, True, 0.20, _all_dets()),   # pass_lo
        _row("tricky", "01", 1, False, 0.80, _all_dets()),  # fail_hi
    ]
    grouped = analyze_mini.group_by(rows)
    out = analyze_mini.cut_4_correctness_vs_idiom_dissociation(grouped)
    c = out["tricky"]
    assert c["pass_lo"] == 1
    assert c["fail_hi"] == 1
    assert c["dissociation_rate"] == 1.0


def test_cut_2_returns_none_when_arm_missing():
    rows = [_row("no-skill", "01", 0, False, 0.12, _all_dets())]
    grouped = analyze_mini.group_by(rows)
    assert analyze_mini.cut_2_v0skill_vs_llmdocs(grouped) is None


def test_paired_v0skill_vs_llmdocs_flip_table():
    rows = [
        # task 01: v0-skill passes both, llmdocs fails both — 2 v0-skill-only wins
        _row("v0-skill", "01", 0, True, 0.9, _all_dets(walker=True)),
        _row("v0-skill", "01", 1, True, 0.9, _all_dets(walker=True)),
        _row("llmdocs", "01", 0, False, 0.3, _all_dets()),
        _row("llmdocs", "01", 1, False, 0.3, _all_dets()),
        # task 02: both pass (tie)
        _row("v0-skill", "02", 0, True, 0.7, _all_dets(walker=True)),
        _row("llmdocs", "02", 0, True, 0.5, _all_dets(walker=True)),
    ]
    grouped = analyze_mini.group_by(rows)
    out = analyze_mini.cut_2_v0skill_vs_llmdocs(grouped)
    assert out["flip_table"]["v0-skill_only"] == 2
    assert out["flip_table"]["llmdocs_only"] == 0
    assert out["flip_table"]["both_pass"] == 1
    assert out["flip_table"]["both_fail"] == 0
    assert out["idiom_mean_delta"] > 0  # v0-skill higher idiom


def test_analyze_mini_end_to_end_cli(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    rows = [
        _row("no-skill", "01", 0, False, 0.12, _all_dets()),
        _row("v0-skill", "01", 0, True, 0.80, _all_dets(walker=True)),
        _row("llmdocs", "01", 0, False, 0.30, _all_dets()),
        _row("irrelevant-ctrl", "01", 0, False, 0.14, _all_dets()),
    ]
    results = tmp_path / "results.jsonl"
    results.write_text("\n".join(json.dumps(r) for r in rows))
    out = tmp_path / "summary.json"

    import sys as _sys

    argv_bak = _sys.argv
    try:
        _sys.argv = ["analyze_mini", "--results", str(results), "--out", str(out)]
        rc = analyze_mini.main()
    finally:
        _sys.argv = argv_bak

    assert rc == 0
    assert out.exists()
    summary = json.loads(out.read_text())
    assert set(summary["cut_1_per_arm"].keys()) == {"no-skill", "v0-skill", "llmdocs", "irrelevant-ctrl"}
    captured = capsys.readouterr()
    assert "CUT 1" in captured.out
    assert "CUT 2" in captured.out
    assert "CUT 3" in captured.out
    assert "CUT 4" in captured.out
