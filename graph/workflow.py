"""LangGraph workflow: syllabus -> validated units -> videos -> playlist."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Literal

from langgraph.graph import END, START, StateGraph

from graph.nodes.input_validation import input_validation
from graph.nodes.output_validation import output_validation
from graph.nodes.playlist_selection import playlist_selection
from graph.nodes.popularity_ranking import popularity_ranking
from graph.nodes.syllabus_parser import make_syllabus_parser
from graph.nodes.transcript_evaluation import make_transcript_evaluation
from graph.nodes.transcript_fetch import make_transcript_fetcher
from graph.nodes.video_retrieval import make_video_retrieval
from graph.state import WorkflowState
from schemas import SegmentEvaluation
from services.llm import (
    Decomposer,
    cached_structured_invoke,
    make_decomposer,
    structured_model,
)
from services.transcripts import TranscriptFetcher
from services.youtube import YouTubeClient


def _route_after(state: WorkflowState, next_node: str) -> Literal["__end__", str]:
    return END if state.get("error") else next_node


def build_workflow(
    decomposer: Decomposer | None = None,
    youtube_client=None,
    transcript_fetcher=None,
    evaluator=None,
):
    """Compile the graph. Inject services for offline tests."""
    resolved_decomposer: Decomposer | None = decomposer
    resolved_youtube = youtube_client
    resolved_transcripts = transcript_fetcher
    resolved_evaluator = evaluator

    def get_decomposer() -> Decomposer:
        nonlocal resolved_decomposer
        if resolved_decomposer is None:
            resolved_decomposer = make_decomposer()
        return resolved_decomposer

    def lazy_decomposer(data) -> object:
        return get_decomposer()(data)

    def get_youtube():
        nonlocal resolved_youtube
        if resolved_youtube is None:
            resolved_youtube = YouTubeClient()
        return resolved_youtube

    def get_transcripts():
        nonlocal resolved_transcripts
        if resolved_transcripts is None:
            resolved_transcripts = TranscriptFetcher()
        return resolved_transcripts

    def get_evaluator():
        nonlocal resolved_evaluator
        if resolved_evaluator is None:
            model = structured_model(SegmentEvaluation)
            resolved_evaluator = lambda messages: cached_structured_invoke(
                model, list(messages), SegmentEvaluation
            )
        return resolved_evaluator

    lazy_youtube = SimpleNamespace(
        candidates_for_query=lambda query, unit_key: (
            get_youtube().candidates_for_query(query, unit_key)
        )
    )
    lazy_fetcher = SimpleNamespace(
        fetch=lambda video_id, languages: get_transcripts().fetch(video_id, languages)
    )

    builder = StateGraph(WorkflowState)
    builder.add_node("input_validation", input_validation)
    builder.add_node("syllabus_parser", make_syllabus_parser(lazy_decomposer))
    builder.add_node("output_validation", output_validation)
    builder.add_node("video_retrieval", make_video_retrieval(lazy_youtube))
    builder.add_node("popularity_ranking", popularity_ranking)
    builder.add_node("transcript_fetch", make_transcript_fetcher(lazy_fetcher))
    def lazy_evaluator(messages):
        return get_evaluator()(messages)

    builder.add_node("transcript_evaluation", make_transcript_evaluation(lazy_evaluator))
    builder.add_node("playlist_selection", playlist_selection)
    builder.add_edge(START, "input_validation")
    builder.add_conditional_edges(
        "input_validation", lambda state: _route_after(state, "syllabus_parser")
    )
    builder.add_conditional_edges(
        "syllabus_parser", lambda state: _route_after(state, "output_validation")
    )
    builder.add_conditional_edges(
        "output_validation", lambda state: _route_after(state, "video_retrieval")
    )
    builder.add_conditional_edges(
        "video_retrieval", lambda state: _route_after(state, "popularity_ranking")
    )
    builder.add_conditional_edges(
        "popularity_ranking", lambda state: _route_after(state, "transcript_fetch")
    )
    builder.add_conditional_edges(
        "transcript_fetch", lambda state: _route_after(state, "transcript_evaluation")
    )
    builder.add_conditional_edges(
        "transcript_evaluation", lambda state: _route_after(state, "playlist_selection")
    )
    builder.add_edge("playlist_selection", END)
    return builder.compile()
