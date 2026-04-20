from harness.prompts import build_prompt


def test_build_prompt_combines_arm_and_task():
    arm = "Helpful context about Jac.\n"
    task = "Write a function foo(x: int) -> int."
    prompt = build_prompt(arm=arm, task=task)
    assert arm.strip() in prompt
    assert task.strip() in prompt
    assert "Return only the Jac code" in prompt


def test_build_prompt_no_arm():
    prompt = build_prompt(arm="", task="Write foo")
    assert "Write foo" in prompt
    assert "---" in prompt  # structure preserved


def test_build_prompt_strips_whitespace():
    prompt = build_prompt(arm="  ctx  \n", task="  task  \n")
    assert "ctx" in prompt
    assert "task" in prompt
    assert "  ctx" not in prompt  # leading spaces stripped
