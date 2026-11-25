"""Deterministic validation helpers shared by graph nodes."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from schemas import SyllabusBreakdown, SyllabusInput


def validate_input(values: Mapping[str, Any]) -> SyllabusInput:
    """Validate the four raw form fields into a SyllabusInput."""
    return SyllabusInput.model_validate(
        {
            "subject": values["subject"],
            "level": values["level"],
            "syllabus": values["syllabus"],
        }
    )


def validate_breakdown(value: object) -> SyllabusBreakdown:
    """Re-validate LLM output before it reaches the UI."""
    return SyllabusBreakdown.model_validate(value)


def format_error(prefix: str, exc: Exception) -> str:
    return f"{prefix}: {exc}"
