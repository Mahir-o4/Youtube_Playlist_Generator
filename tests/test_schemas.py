from __future__ import annotations

import pytest
from pydantic import ValidationError

from schemas import SyllabusBreakdown, SyllabusInput


def test_syllabus_input_strips_whitespace() -> None:
    data = SyllabusInput.model_validate(
        {
            "subject": "  Math  ",
            "level": "  BSc ",
            "syllabus": "  Week 1: sets and proofs.  ",
        }
    )
    assert data.subject == "Math"
    assert data.syllabus == "Week 1: sets and proofs."


def test_syllabus_input_rejects_blank_field(valid_input: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        SyllabusInput.model_validate({**valid_input, "subject": "   "})


def test_breakdown_rejects_duplicate_topics(valid_breakdown: SyllabusBreakdown) -> None:
    payload = valid_breakdown.model_dump()
    payload["topics"].append(payload["topics"][0])
    with pytest.raises(ValidationError, match="topic titles must be unique"):
        SyllabusBreakdown.model_validate(payload)


def test_breakdown_rejects_duplicate_units(valid_breakdown: SyllabusBreakdown) -> None:
    payload = valid_breakdown.model_dump()
    payload["topics"][0]["units"].append(payload["topics"][0]["units"][0])
    with pytest.raises(ValidationError, match="unit titles must be unique"):
        SyllabusBreakdown.model_validate(payload)


def test_breakdown_rejects_empty_topics(valid_breakdown: SyllabusBreakdown) -> None:
    payload = valid_breakdown.model_dump()
    payload["topics"] = []
    with pytest.raises(ValidationError):
        SyllabusBreakdown.model_validate(payload)
