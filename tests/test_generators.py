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
