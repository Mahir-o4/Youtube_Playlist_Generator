from __future__ import annotations

import pytest

from graph.workflow import build_workflow
from schemas import SyllabusBreakdown, SyllabusInput


def test_workflow_returns_validated_breakdown(
    valid_input: dict[str, str],
    valid_breakdown: SyllabusBreakdown,
    fake_youtube_client: object,
    fake_transcript_fetcher: object,
) -> None:
    seen: list[SyllabusInput] = []

    def fake_decomposer(data: SyllabusInput) -> SyllabusBreakdown:
        seen.append(data)
        return valid_breakdown

    result = build_workflow(
        fake_decomposer, fake_youtube_client, fake_transcript_fetcher
    ).invoke(dict(valid_input))

    assert result["error"] is None
    assert result["breakdown"] == valid_breakdown
    assert seen[0].subject == valid_input["subject"]
    assert result["finalists"] == {"1.1": []}
    assert result["transcripts"] == {}


def test_malformed_output_becomes_error(
    valid_input: dict[str, str],
    fake_youtube_client: object,
    fake_transcript_fetcher: object,
) -> None:
    def bad_decomposer(_: SyllabusInput) -> dict:  # type: ignore[return-type]
        return {
            "subject": "Linear Algebra",
            "level": "Undergraduate",
            "topics": [],
        }

    result = build_workflow(
        bad_decomposer, fake_youtube_client, fake_transcript_fetcher
    ).invoke(dict(valid_input))

    assert result["breakdown"] is None
    assert "Invalid decomposition output" in result["error"]


def test_invalid_input_stops_before_llm(
    valid_input: dict[str, str],
    fake_youtube_client: object,
    fake_transcript_fetcher: object,
) -> None:
    def must_not_run(_: SyllabusInput) -> SyllabusBreakdown:
        raise AssertionError("decomposer must not be called")

    result = build_workflow(
        must_not_run, fake_youtube_client, fake_transcript_fetcher
    ).invoke({**valid_input, "subject": "   "})

    assert result["error"].startswith("Invalid syllabus input")
    assert result.get("breakdown") is None


def test_build_workflow_does_not_need_a_key(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called() -> None:
        raise AssertionError("make_decomposer must stay lazy")

    monkeypatch.setattr("graph.workflow.make_decomposer", fail_if_called)
    assert build_workflow() is not None
