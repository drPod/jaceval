from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Literal

ModelName = Literal["claude-haiku-4-5", "gemini-2.5-pro", "llama-3.3-70b-versatile"]


@dataclass
class Generation:
    model: str
    completion: str
    finish_reason: str
    input_tokens: int
    output_tokens: int
    wall_ms: int


def generate(
    model: ModelName,
    prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 2048,
    seed: int = 0,
) -> Generation:
    if model == "claude-haiku-4-5":
        return _call_claude(prompt, temperature, max_tokens, seed)
    elif model == "gemini-2.5-pro":
        return _call_gemini(prompt, temperature, max_tokens, seed)
    elif model == "llama-3.3-70b-versatile":
        return _call_groq(prompt, temperature, max_tokens, seed)
    else:
        raise ValueError(f"unknown model: {model}")


def _call_claude(prompt: str, temperature: float, max_tokens: int, seed: int) -> Generation:
    from dotenv import load_dotenv
    load_dotenv()
    from anthropic import Anthropic
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    start = time.monotonic()
    resp = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
    )
    wall_ms = int((time.monotonic() - start) * 1000)
    completion = "".join(b.text for b in resp.content if b.type == "text")
    return Generation(
        model="claude-haiku-4-5",
        completion=completion,
        finish_reason=resp.stop_reason or "stop",
        input_tokens=resp.usage.input_tokens,
        output_tokens=resp.usage.output_tokens,
        wall_ms=wall_ms,
    )


def _call_gemini(prompt: str, temperature: float, max_tokens: int, seed: int) -> Generation:
    raise NotImplementedError("implemented in Task 9")


def _call_groq(prompt: str, temperature: float, max_tokens: int, seed: int) -> Generation:
    raise NotImplementedError("implemented in Task 10")
