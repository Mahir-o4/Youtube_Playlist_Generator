"""State schema for the LangGraph workflow."""

from __future__ import annotations

from typing import TypedDict

from schemas import SyllabusBreakdown, SyllabusInput


class WorkflowState(TypedDict, total=False):
    subject: str
    level: str
    language: str
    syllabus: str
    syllabus_input: SyllabusInput | None
    breakdown: SyllabusBreakdown | None
    error: str | None
