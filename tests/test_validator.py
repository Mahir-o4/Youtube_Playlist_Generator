from __future__ import annotations

import pytest
from pydantic import ValidationError

from core.validator import validate_breakdown, validate_input
from schemas import SyllabusBreakdown


def test_validate_input_normalizes_values(valid_input: dict[str, str]) -> None:
    parsed = validate_input({**valid_input, "subject": "  Linear Algebra  "})
    assert parsed.subject == "Linear Algebra"


def test_validate_input_rejects_short_syllabus(valid_input: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        validate_input({**valid_input, "syllabus": "short"})


def test_validate_breakdown_accepts_model(valid_breakdown: SyllabusBreakdown) -> None:
    assert validate_breakdown(valid_breakdown) == valid_breakdown


def test_validate_breakdown_rejects_bad_payload() -> None:
    with pytest.raises(ValidationError):
        validate_breakdown({"subject": "Math", "topics": []})
