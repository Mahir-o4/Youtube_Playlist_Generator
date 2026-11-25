from __future__ import annotations

from prompts import build_decomposition_messages, load_prompt
from schemas import SyllabusInput


def test_prompt_carries_every_input(valid_input: dict[str, str]) -> None:
    data = SyllabusInput.model_validate(valid_input)
    system, human = build_decomposition_messages(data)
    for value in valid_input.values():
        assert value in human.content
    assert "do not invent" in system.content.lower()


def test_decomposition_prompt_loads_from_text_file() -> None:
    assert "curriculum designer" in load_prompt("decomposition")


def test_transcript_scoring_prompt_loads_from_text_file() -> None:
    prompt = load_prompt("transcript_scoring")
    assert '"explained"' in prompt
    assert '"absent"' in prompt
    assert "valid JSON only" in prompt
