"""Node: re-validate LLM output before it reaches the UI."""

from __future__ import annotations

from core.validator import format_error, validate_breakdown
from graph.state import WorkflowState


def output_validation(state: WorkflowState) -> dict:
    if state.get("error") or state.get("breakdown") is None:
        return {}
    try:
        return {"breakdown": validate_breakdown(state["breakdown"]), "error": None}
    except Exception as exc:
        return {
            "error": format_error("Invalid decomposition output", exc),
            "breakdown": None,
        }
