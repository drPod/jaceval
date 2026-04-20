from harness.run import _key, normalize_for_judge, strip_fences


def test_strip_fences_removes_triple_backticks():
    src = "```jac\nnode Foo { has x: int; }\n```"
    assert strip_fences(src) == "node Foo { has x: int; }"


def test_strip_fences_no_fences_is_passthrough():
    src = "node Foo { has x: int; }"
    assert strip_fences(src) == src


def test_strip_fences_handles_surrounding_whitespace():
    src = "\n\n```\nx = 1;\n```\n\n"
    assert strip_fences(src) == "x = 1;"


def test_normalize_for_judge_strips_trailing_whitespace():
    src = "x = 1;   \ny = 2;\t\n"
    assert normalize_for_judge(src) == "x = 1;\ny = 2;"


def test_normalize_for_judge_collapses_multi_blank_lines():
    src = "x = 1;\n\n\n\n\ny = 2;"
    assert normalize_for_judge(src) == "x = 1;\n\ny = 2;"


def test_normalize_for_judge_preserves_single_blank():
    src = "x = 1;\n\ny = 2;"
    assert normalize_for_judge(src) == "x = 1;\n\ny = 2;"


def test_normalize_for_judge_preserves_comments():
    # Comments are idiomaticity signal — don't strip them.
    src = "# idiomatic comment\nnode Foo { has x: int; }"
    assert "idiomatic comment" in normalize_for_judge(src)


def test_key_round_trips_plan_entry():
    entry = {
        "group": "main",
        "arm": "no-skill",
        "model": "claude-haiku-4-5",
        "task_id": "01",
        "sample_idx": 3,
        "seed": 42,
    }
    assert _key(entry) == ("main", "no-skill", "claude-haiku-4-5", "01", 3)


def test_key_defaults_group_to_main_when_missing():
    entry = {"arm": "no-skill", "model": "m", "task_id": "01", "sample_idx": 0, "seed": 0}
    assert _key(entry)[0] == "main"
