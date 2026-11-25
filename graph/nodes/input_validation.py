"""Node: validate raw form values into SyllabusInput."""

from __future__ import annotations

from core.validator import format_error, validate_input
from graph.state import WorkflowState


def input_validation(state: WorkflowState) -> dict:
    try:
        parsed = validate_input(
            {
                "subject": state["subject"],
                "level": state["level"],
                "language": state["language"],
                "syllabus": state["syllabus"],
            }
        )
    except Exception as exc:
        return {
            "error": format_error("Invalid syllabus input", exc),
            "syllabus_input": None,
        }
    return {"syllabus_input": parsed, "error": None}
