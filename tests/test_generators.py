import os
import pytest
from dotenv import load_dotenv

load_dotenv()

from harness.generators import Generation, generate


def test_generate_returns_generation(monkeypatch):
    # monkeypatch the underlying SDK call
    from harness import generators

    def fake_claude(prompt, temperature, max_tokens, seed):
        return Generation(
            model="claude-haiku-4-5",
            completion="walker foo { }",
            finish_reason="stop",
            input_tokens=10,
            output_tokens=5,
            wall_ms=123,
        )

    monkeypatch.setattr(generators, "_call_claude", fake_claude)
    g = generate(
        model="claude-haiku-4-5",
        prompt="Write a walker",
        temperature=0.2,
        max_tokens=512,
        seed=42,
    )
    assert g.completion == "walker foo { }"
    assert g.model == "claude-haiku-4-5"


@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="no Anthropic key")
def test_claude_live_roundtrip():
    g = generate(model="claude-haiku-4-5", prompt="Reply with exactly the word: ok", temperature=0.0, max_tokens=8, seed=0)
    assert "ok" in g.completion.lower()
    assert g.input_tokens > 0
    assert g.output_tokens > 0


@pytest.mark.skipif(not os.getenv("GOOGLE_API_KEY"), reason="no Google key")
def test_gemini_live_roundtrip():
    g = generate(model="gemini-2.5-pro", prompt="Reply with exactly the word: ok", temperature=0.0, max_tokens=8, seed=0)
    assert "ok" in g.completion.lower()


@pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="no Groq key")
def test_groq_live_roundtrip():
    g = generate(model="llama-3.3-70b-versatile", prompt="Reply with exactly the word: ok", temperature=0.0, max_tokens=8, seed=0)
    assert "ok" in g.completion.lower()
