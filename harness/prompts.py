from __future__ import annotations

PROMPT_TEMPLATE = """{arm}

---

{task}

---

Return only the Jac code, no prose, no fences."""


def build_prompt(arm: str, task: str) -> str:
    return PROMPT_TEMPLATE.format(arm=arm.strip(), task=task.strip())
