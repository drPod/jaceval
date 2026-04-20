from harness.plan_builder import build_plan


def test_build_plan_yields_full_cross_product():
    arms = ["no-skill", "llmdocs"]
    models = ["claude-haiku-4-5", "gemini-3-flash-preview"]
    tasks = ["01", "02"]
    plan = list(build_plan(arms=arms, models=models, task_ids=tasks, n_samples=3, seed_base=0))
    assert len(plan) == 2 * 2 * 2 * 3
    keys = {(p["arm"], p["model"], p["task_id"], p["sample_idx"]) for p in plan}
    assert len(keys) == len(plan)


def test_build_plan_noise_floor_adds_second_no_skill_group():
    plan = list(
        build_plan(
            arms=["no-skill"],
            models=["claude-haiku-4-5"],
            task_ids=["01"],
            n_samples=2,
            seed_base=0,
            noise_floor=True,
        )
    )
    # 2 samples * 2 groups (main + noise) = 4 entries
    assert len(plan) == 4
    # Distinct seeds across the two groups
    seeds = [p["seed"] for p in plan]
    assert len(set(seeds)) == 4
    # Group labels must cover both main and noise
    groups = {p["group"] for p in plan}
    assert groups == {"main", "noise"}


def test_build_plan_noise_floor_is_noop_when_no_skill_absent():
    plan = list(
        build_plan(
            arms=["llmdocs"],
            models=["claude-haiku-4-5"],
            task_ids=["01"],
            n_samples=2,
            noise_floor=True,
        )
    )
    # No-skill not in arms, so noise-floor group adds nothing.
    assert all(p["group"] == "main" for p in plan)
    assert len(plan) == 2


def test_build_plan_seeds_are_deterministic_across_calls():
    kwargs = dict(arms=["no-skill"], models=["gemini-3-flash-preview"], task_ids=["01"], n_samples=3, seed_base=42)
    a = list(build_plan(**kwargs))
    b = list(build_plan(**kwargs))
    assert [e["seed"] for e in a] == [e["seed"] for e in b]


def test_build_plan_noise_group_seeds_differ_from_main():
    plan = list(
        build_plan(
            arms=["no-skill"],
            models=["claude-haiku-4-5"],
            task_ids=["01"],
            n_samples=3,
            noise_floor=True,
        )
    )
    main_seeds = {p["seed"] for p in plan if p["group"] == "main"}
    noise_seeds = {p["seed"] for p in plan if p["group"] == "noise"}
    assert main_seeds.isdisjoint(noise_seeds)
