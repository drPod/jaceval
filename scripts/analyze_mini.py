"""Analysis for the jaceval mini-run.

Reads a results JSONL (default `.eval_cache/results.jsonl`) and emits the
four methodological cuts the Mars-note is built around:

1. Per-arm pass rate and mean idiomaticity.
2. **v0-skill vs llmdocs** — paired deltas per task with McNemar's on binary
   pass/fail and paired-bootstrap CI on ordinal idiomaticity.
3. **Per-construct AST breakdown** — which Jac idioms each arm teaches.
4. **Correctness vs idiomaticity dissociation** — contingency of
   (passed-tests × high-idiomaticity) per arm, showing the cases a
   correctness-only eval would miss.

Bonus (5): **v0-skill vs irrelevant-ctrl** — the tokens-don't-matter
falsification.

Outputs:
- `results/mini/summary.json` — machine-readable.
- stdout — human-readable table-y output.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean, median

from harness.stats import (
    mcnemar_exact,
    paired_bootstrap_mean,
    pass_at_k,
    wilson_interval,
)

DETECTORS = [
    "uses_walker",
    "uses_visit",
    "uses_typed_edge_archetype",
    "uses_connect_op",
    "has_type_annotations",
    "uses_abilities_on_nodes",
]

HIGH_IDIOM_THRESHOLD = 0.6


def load_results(path: Path) -> list[dict]:
    if not path.exists():
        print(f"FATAL: {path} missing", file=sys.stderr)
        sys.exit(2)
    return [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]


def group_by(rows: list[dict]) -> dict[tuple[str, str], list[dict]]:
    """Group rows by (arm, task_id). Order within task preserved."""
    out: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in rows:
        out[(r["entry"]["arm"], r["entry"]["task_id"])].append(r)
    return out


def bucket_of(task_id: str, rows: list[dict]) -> str:
    """Read bucket from any row's task dir path via the meta file."""
    # Cheap: infer from meta if available (we don't have direct meta here, so
    # fall back to id-based heuristic matching the 01..10 numbering.)
    try:
        n = int(task_id)
    except ValueError:
        return "pilot"
    if 1 <= n <= 3:
        return "syntax"
    if 4 <= n <= 6:
        return "graph"
    return "walker"


def cut_1_per_arm_summary(grouped: dict) -> dict:
    """Cut 1: pass rate and mean idiomaticity per arm, plus Wilson 95% CI on pass."""
    per_arm: dict = {}
    by_arm_pass: dict[str, list[bool]] = defaultdict(list)
    by_arm_idiom: dict[str, list[float]] = defaultdict(list)
    for (arm, _task), rs in grouped.items():
        for r in rs:
            by_arm_pass[arm].append(bool(r["passed"]))
            by_arm_idiom[arm].append(float(r["idiom_score"]))
    for arm in sorted(by_arm_pass):
        passes = sum(by_arm_pass[arm])
        total = len(by_arm_pass[arm])
        lo, hi = wilson_interval(successes=passes, trials=total)
        per_arm[arm] = {
            "n": total,
            "pass_rate": passes / total if total else 0.0,
            "pass_wilson_95": [lo, hi],
            "idiom_mean": mean(by_arm_idiom[arm]) if by_arm_idiom[arm] else 0.0,
            "idiom_median": median(by_arm_idiom[arm]) if by_arm_idiom[arm] else 0.0,
        }
    return per_arm


def _paired_arm_vs_arm(grouped: dict, arm_a: str, arm_b: str) -> dict:
    """Pair arm_a vs arm_b per task, aggregating across samples per task."""
    task_ids = sorted({t for (a, t) in grouped if a in (arm_a, arm_b)})
    per_task = []
    # For McNemar: discordant pairs at the sample level. For each (arm, task)
    # we pair sample_idx across arms — assumes same plan builder seeds.
    a_wins = b_wins = tie_pass = tie_fail = 0
    idiom_a_per_task: list[float] = []
    idiom_b_per_task: list[float] = []

    for t in task_ids:
        rs_a = grouped.get((arm_a, t), [])
        rs_b = grouped.get((arm_b, t), [])
        if not rs_a or not rs_b:
            continue
        # sort by sample_idx for paired comparison
        rs_a = sorted(rs_a, key=lambda r: r["entry"]["sample_idx"])
        rs_b = sorted(rs_b, key=lambda r: r["entry"]["sample_idx"])
        n = min(len(rs_a), len(rs_b))
        for ra, rb in zip(rs_a[:n], rs_b[:n]):
            pa, pb = bool(ra["passed"]), bool(rb["passed"])
            if pa and not pb:
                a_wins += 1
            elif pb and not pa:
                b_wins += 1
            elif pa and pb:
                tie_pass += 1
            else:
                tie_fail += 1
        # Per-task mean idiomaticity, one float per task for paired bootstrap.
        idiom_a_per_task.append(mean(r["idiom_score"] for r in rs_a))
        idiom_b_per_task.append(mean(r["idiom_score"] for r in rs_b))
        per_task.append({
            "task_id": t,
            "bucket": bucket_of(t, rs_a),
            f"{arm_a}_pass_rate": sum(r["passed"] for r in rs_a) / len(rs_a),
            f"{arm_b}_pass_rate": sum(r["passed"] for r in rs_b) / len(rs_b),
            f"{arm_a}_idiom": idiom_a_per_task[-1],
            f"{arm_b}_idiom": idiom_b_per_task[-1],
            "idiom_delta": idiom_a_per_task[-1] - idiom_b_per_task[-1],
        })

    mcnemar_p = mcnemar_exact(a_wins=a_wins, b_wins=b_wins)
    if len(idiom_a_per_task) > 1:
        ci_lo, ci_hi = paired_bootstrap_mean(
            idiom_a_per_task, idiom_b_per_task, n_boot=10_000, seed=0
        )
        mean_delta = mean(a - b for a, b in zip(idiom_a_per_task, idiom_b_per_task))
    else:
        ci_lo = ci_hi = 0.0
        mean_delta = (idiom_a_per_task[0] - idiom_b_per_task[0]) if idiom_a_per_task else 0.0

    return {
        "arm_a": arm_a,
        "arm_b": arm_b,
        "flip_table": {
            f"{arm_a}_only": a_wins,
            f"{arm_b}_only": b_wins,
            "both_pass": tie_pass,
            "both_fail": tie_fail,
        },
        "mcnemar_p_two_sided": mcnemar_p,
        "idiom_mean_delta": mean_delta,
        "idiom_bootstrap_95ci": [ci_lo, ci_hi],
        "per_task": per_task,
    }


def cut_2_v0skill_vs_llmdocs(grouped: dict) -> dict | None:
    """Cut 2: SKILL.md vs Jaseci's canonical LLMDocs."""
    arms = {a for (a, _t) in grouped}
    if "v0-skill" not in arms or "llmdocs" not in arms:
        return None
    return _paired_arm_vs_arm(grouped, "v0-skill", "llmdocs")


def cut_3_per_construct(grouped: dict) -> dict:
    """Cut 3: per-detector activation rate per arm. Shows which idioms
    each arm actually teaches."""
    by_arm: dict[str, dict[str, list[int]]] = defaultdict(
        lambda: {d: [] for d in DETECTORS}
    )
    for (arm, _task), rs in grouped.items():
        for r in rs:
            per = r["ast"]["per_detector"]
            for d in DETECTORS:
                by_arm[arm][d].append(1 if per.get(d) else 0)
    result: dict[str, dict[str, float]] = {}
    for arm in sorted(by_arm):
        result[arm] = {}
        for d in DETECTORS:
            vals = by_arm[arm][d]
            result[arm][d] = sum(vals) / len(vals) if vals else 0.0
    return result


def cut_4_correctness_vs_idiom_dissociation(grouped: dict) -> dict:
    """Cut 4: contingency of (passed, high_idiom) per arm. High idiom = >0.6."""
    by_arm: dict[str, dict[str, int]] = defaultdict(
        lambda: {"pass_hi": 0, "pass_lo": 0, "fail_hi": 0, "fail_lo": 0}
    )
    for (arm, _task), rs in grouped.items():
        for r in rs:
            p = bool(r["passed"])
            hi = r["idiom_score"] > HIGH_IDIOM_THRESHOLD
            key = ("pass" if p else "fail") + ("_hi" if hi else "_lo")
            by_arm[arm][key] += 1
    out = {}
    for arm in sorted(by_arm):
        c = by_arm[arm]
        total = sum(c.values())
        out[arm] = {
            **c,
            "total": total,
            "passed_but_low_idiom": c["pass_lo"],
            "failed_but_high_idiom": c["fail_hi"],
            "dissociation_rate": (c["pass_lo"] + c["fail_hi"]) / total if total else 0.0,
        }
    return out


def cut_5_v0skill_vs_irrelevant(grouped: dict) -> dict | None:
    """Bonus: v0-skill vs length-matched Gleam SKILL.md."""
    arms = {a for (a, _t) in grouped}
    if "v0-skill" not in arms or "irrelevant-ctrl" not in arms:
        return None
    return _paired_arm_vs_arm(grouped, "v0-skill", "irrelevant-ctrl")


def render_cut_1(per_arm: dict) -> str:
    lines = ["CUT 1 — per-arm pass rate and idiomaticity", ""]
    lines.append(f"{'arm':20s}  {'n':>4s}  {'pass':>8s}  {'95% CI':>16s}  {'idiom_mean':>11s}")
    for arm, v in per_arm.items():
        lo, hi = v["pass_wilson_95"]
        lines.append(
            f"{arm:20s}  {v['n']:>4d}  "
            f"{v['pass_rate']:>7.0%}  "
            f"[{lo:>5.2f},{hi:>5.2f}]  "
            f"{v['idiom_mean']:>11.3f}"
        )
    return "\n".join(lines)


def render_cut_2(cut2: dict | None) -> str:
    if not cut2:
        return "CUT 2 — v0-skill vs llmdocs: SKIPPED (missing arm)."
    lines = [f"CUT 2 — v0-skill vs llmdocs"]
    f = cut2["flip_table"]
    lines.append(f"  flip table: v0-skill_only={f['v0-skill_only']}  "
                 f"llmdocs_only={f['llmdocs_only']}  "
                 f"both_pass={f['both_pass']}  both_fail={f['both_fail']}")
    lines.append(f"  McNemar two-sided p = {cut2['mcnemar_p_two_sided']:.4f}")
    ci = cut2["idiom_bootstrap_95ci"]
    lines.append(
        f"  mean Δ idiomaticity (v0-skill − llmdocs) = {cut2['idiom_mean_delta']:+.3f}  "
        f"95% paired-bootstrap CI = [{ci[0]:+.3f}, {ci[1]:+.3f}]"
    )
    if ci[0] > 0:
        lines.append("  ⇒ CI excludes 0 strictly positive: v0-skill significantly > llmdocs on idiomaticity.")
    elif ci[1] < 0:
        lines.append("  ⇒ CI excludes 0 strictly negative: llmdocs significantly > v0-skill on idiomaticity.")
    else:
        lines.append("  ⇒ CI spans 0: no significant difference on idiomaticity at this N.")
    return "\n".join(lines)


def render_cut_3(per_arm_per_detector: dict) -> str:
    lines = ["CUT 3 — per-construct AST detector activation rate"]
    arms = list(per_arm_per_detector.keys())
    header = f"{'detector':32s}  " + "  ".join(f"{a:>16s}" for a in arms)
    lines.append(header)
    for d in DETECTORS:
        row = f"{d:32s}  " + "  ".join(
            f"{per_arm_per_detector[a].get(d, 0):>15.0%} " for a in arms
        )
        lines.append(row)
    return "\n".join(lines)


def render_cut_4(cut4: dict) -> str:
    lines = ["CUT 4 — correctness-vs-idiomaticity dissociation  (high-idiom = score > 0.6)"]
    lines.append(f"{'arm':20s}  {'pass_hi':>8s}  {'pass_lo':>8s}  {'fail_hi':>8s}  {'fail_lo':>8s}  {'dissoc':>7s}")
    for arm, c in cut4.items():
        lines.append(
            f"{arm:20s}  "
            f"{c['pass_hi']:>8d}  {c['pass_lo']:>8d}  {c['fail_hi']:>8d}  {c['fail_lo']:>8d}  "
            f"{c['dissociation_rate']:>6.0%}"
        )
    lines.append("")
    lines.append("  pass_lo = tests pass, code not idiomatic — correctness-only eval misses the miss.")
    lines.append("  fail_hi = tests fail, code looks idiomatic — judge caught what compilation missed.")
    return "\n".join(lines)


def render_cut_5(cut5: dict | None) -> str:
    if not cut5:
        return "CUT 5 — v0-skill vs irrelevant-ctrl: SKIPPED (missing arm)."
    lines = ["CUT 5 — v0-skill vs irrelevant-ctrl (tokens-don't-matter falsification)"]
    f = cut5["flip_table"]
    lines.append(f"  flip table: v0-skill_only={f['v0-skill_only']}  "
                 f"irrelevant-ctrl_only={f['irrelevant-ctrl_only']}  "
                 f"both_pass={f['both_pass']}  both_fail={f['both_fail']}")
    lines.append(f"  McNemar two-sided p = {cut5['mcnemar_p_two_sided']:.4f}")
    ci = cut5["idiom_bootstrap_95ci"]
    lines.append(
        f"  mean Δ idiomaticity (v0-skill − irrelevant-ctrl) = {cut5['idiom_mean_delta']:+.3f}  "
        f"95% paired-bootstrap CI = [{ci[0]:+.3f}, {ci[1]:+.3f}]"
    )
    if ci[0] > 0:
        lines.append("  ⇒ Jac-content matters: irrelevant-ctrl does NOT explain the v0-skill lift.")
    elif ci[1] < 0:
        lines.append("  ⇒ Uh-oh: irrelevant-ctrl outperforms v0-skill. Investigate.")
    else:
        lines.append("  ⇒ CI spans 0: can't rule out 'more tokens' as the mechanism at this N.")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", type=Path, default=Path(".eval_cache/results.jsonl"))
    ap.add_argument("--out", type=Path, default=Path("results/mini/summary.json"))
    args = ap.parse_args()

    rows = load_results(args.results)
    grouped = group_by(rows)

    per_arm = cut_1_per_arm_summary(grouped)
    cut2 = cut_2_v0skill_vs_llmdocs(grouped)
    cut3 = cut_3_per_construct(grouped)
    cut4 = cut_4_correctness_vs_idiom_dissociation(grouped)
    cut5 = cut_5_v0skill_vs_irrelevant(grouped)

    print(render_cut_1(per_arm))
    print()
    print(render_cut_2(cut2))
    print()
    print(render_cut_3(cut3))
    print()
    print(render_cut_4(cut4))
    print()
    print(render_cut_5(cut5))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {
                "n_rows": len(rows),
                "cut_1_per_arm": per_arm,
                "cut_2_v0skill_vs_llmdocs": cut2,
                "cut_3_per_construct": cut3,
                "cut_4_dissociation": cut4,
                "cut_5_v0skill_vs_irrelevant": cut5,
            },
            indent=2,
        )
    )
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
