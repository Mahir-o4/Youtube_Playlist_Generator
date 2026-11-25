"""LangGraph workflow wiring: input -> parse -> validate."""

from __future__ import annotations

from typing import Literal

from langgraph.graph import END, START, StateGraph

from graph.nodes.input_validation import input_validation
from graph.nodes.output_validation import output_validation
from graph.nodes.syllabus_parser import make_syllabus_parser
from graph.state import WorkflowState
from services.llm import Decomposer, make_decomposer


def _route_after(state: WorkflowState, next_node: str) -> Literal["__end__", str]:
    return END if state.get("error") else next_node


def build_workflow(decomposer: Decomposer | None = None):
    """Compile the graph. Inject a decomposer for offline tests."""
    resolved: Decomposer | None = decomposer

    def get_decomposer() -> Decomposer:
        nonlocal resolved
        if resolved is None:
            resolved = make_decomposer()
        return resolved

    def lazy_decomposer(data) -> object:
        return get_decomposer()(data)

    builder = StateGraph(WorkflowState)
    builder.add_node("input_validation", input_validation)
    builder.add_node("syllabus_parser", make_syllabus_parser(lazy_decomposer))
    builder.add_node("output_validation", output_validation)
    builder.add_edge(START, "input_validation")
    builder.add_conditional_edges(
        "input_validation", lambda state: _route_after(state, "syllabus_parser")
    )
    builder.add_conditional_edges(
        "syllabus_parser", lambda state: _route_after(state, "output_validation")
    )
    builder.add_edge("output_validation", END)
    return builder.compile()
