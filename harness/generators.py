from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Literal

ModelName = Literal["claude-haiku-4-5", "gemini-3-flash-preview", "meta-llama/llama-4-scout-17b-16e-instruct"]


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
    elif model == "gemini-3-flash-preview":
        return _call_gemini(prompt, temperature, max_tokens, seed)
    elif model == "meta-llama/llama-4-scout-17b-16e-instruct":
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
    from dotenv import load_dotenv
    load_dotenv()
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    start = time.monotonic()
    resp = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            seed=seed,
        ),
    )
    wall_ms = int((time.monotonic() - start) * 1000)
    text = resp.text or ""
    usage = resp.usage_metadata
    return Generation(
        model="gemini-3-flash-preview",
        completion=text,
        finish_reason=(resp.candidates[0].finish_reason.name if resp.candidates else "stop"),
        input_tokens=(usage.prompt_token_count if usage else 0),
        output_tokens=(usage.candidates_token_count if usage else 0),
        wall_ms=wall_ms,
    )


def _call_groq(prompt: str, temperature: float, max_tokens: int, seed: int) -> Generation:
    from dotenv import load_dotenv
    load_dotenv()
    from groq import Groq
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    start = time.monotonic()
    resp = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        temperature=temperature,
        max_tokens=max_tokens,
        seed=seed,
        messages=[{"role": "user", "content": prompt}],
    )
    wall_ms = int((time.monotonic() - start) * 1000)
    choice = resp.choices[0]
    return Generation(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        completion=choice.message.content or "",
        finish_reason=choice.finish_reason or "stop",
        input_tokens=resp.usage.prompt_tokens,
        output_tokens=resp.usage.completion_tokens,
        wall_ms=wall_ms,
    )
