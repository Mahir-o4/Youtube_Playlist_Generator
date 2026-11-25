"""Node: call the LLM decomposer with a validated syllabus."""

from __future__ import annotations

from collections.abc import Callable

from core.validator import format_error
from graph.state import WorkflowState
from schemas import SyllabusInput
from services.llm import Decomposer

ParserNode = Callable[[WorkflowState], dict]


def make_syllabus_parser(decomposer: Decomposer) -> ParserNode:
    """Build a parser node around an injected decomposer."""

    def syllabus_parser(state: WorkflowState) -> dict:
        parsed: SyllabusInput | None = state.get("syllabus_input")
        if parsed is None:
            return {"error": "Missing validated syllabus input", "breakdown": None}
        try:
            return {"breakdown": decomposer(parsed), "error": None}
        except Exception as exc:
            return {
                "error": format_error("Syllabus decomposition failed", exc),
                "breakdown": None,
            }

    return syllabus_parser
