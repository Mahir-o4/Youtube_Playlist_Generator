"""Node: score transcript windows against checklist items with the user rubric."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from core.concurrency import map_parallel, worker_count
from graph.state import WorkflowState
from prompts import load_prompt
from schemas import SegmentEvaluation, TranscriptSegment

Evaluator = Callable[[list[BaseMessage]], SegmentEvaluation]
_RUBRIC = "transcript_scoring"


def _format_time(seconds: float) -> str:
    total = max(int(seconds), 0)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def _chunks(
    segments: Sequence[TranscriptSegment], max_words: int = 700
) -> Iterator[list[TranscriptSegment]]:
    current: list[TranscriptSegment] = []
    words = 0
    for segment in segments:
        count = len(segment.text.split())
        if current and words + count > max_words:
            yield current
            current, words = [], 0
        current.append(segment)
        words += count
    if current:
        yield current


def _unit_lookup(state: WorkflowState) -> dict[str, tuple[str, list]]:
    breakdown = state.get("breakdown")
    if not breakdown:
        return {}
    lookup: dict[str, tuple[str, list]] = {}
    for topic_index, topic in enumerate(breakdown.topics, start=1):
        for unit_index, unit in enumerate(topic.units, start=1):
            lookup[f"{topic_index}.{unit_index}"] = (
                f"{topic.title} — {unit.title}",
                unit.checklist,
            )
    return lookup


def make_transcript_evaluation(
    evaluator: Evaluator, max_words: int = 700, workers: int | None = None
) -> Callable[[WorkflowState], dict]:
    """Build an evaluation node around an injectable structured evaluator."""

    def transcript_evaluation(state: WorkflowState) -> dict:
        finalists = state.get("finalists") or {}
        transcripts = state.get("transcripts") or {}
        lookup = _unit_lookup(state)
        rubric = load_prompt(_RUBRIC)
        tasks: list[tuple[str, list[BaseMessage]]] = []

        for unit_key, videos in finalists.items():
            unit_title, checklist = lookup.get(unit_key, (unit_key, []))
            checklist_text = "\n".join(
                f"{index}. {item.text}"
                for index, item in enumerate(checklist, start=1)
            )
            for video in videos:
                segments = transcripts.get(video.video_id)
                if not segments:
                    continue
                for chunk in _chunks(segments, max_words):
                    transcript_text = "\n".join(
                        f"[{_format_time(segment.start)}] {segment.text}"
                        for segment in chunk
                    )
                    human = (
                        f"UNIT_TITLE: {unit_title}\n\n"
                        f"CHECKLIST:\n{checklist_text}\n\n"
                        f"TRANSCRIPT_SEGMENT:\n{transcript_text}"
                    )
                    tasks.append(
                        (
                            f"{unit_key}:{video.video_id}",
                            [
                                SystemMessage(content=rubric),
                                HumanMessage(content=human),
                            ],
                        )
                    )

        def evaluate(task: tuple[str, list[BaseMessage]]):
            key, messages = task
            return key, SegmentEvaluation.model_validate(evaluator(messages))

        try:
            evaluations: dict[str, list[SegmentEvaluation]] = {}
            for key, result in map_parallel(
                evaluate, tasks, workers or worker_count("EVALUATION_WORKERS", 4)
            ):
                evaluations.setdefault(key, []).append(result)
        except Exception as exc:
            return {
                "error": f"Transcript evaluation failed: {exc}",
                "evaluations": {},
            }
        return {"evaluations": evaluations, "error": None}

    return transcript_evaluation
