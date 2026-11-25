from __future__ import annotations

import pytest

from schemas import SyllabusBreakdown, VideoCandidate


class FakeYouTubeClient:
    def __init__(self, candidates: dict[str, list[VideoCandidate]] | None = None) -> None:
        self.candidates = candidates or {}

    def candidates_for_query(self, query: str, unit_key: str) -> list[VideoCandidate]:
        return self.candidates.get(unit_key, [])


@pytest.fixture
def fake_youtube_client() -> FakeYouTubeClient:
    return FakeYouTubeClient()


class FakeTranscriptFetcher:
    def fetch(self, video_id: str, languages=("en", "hi")):
        return None


@pytest.fixture
def fake_transcript_fetcher() -> FakeTranscriptFetcher:
    return FakeTranscriptFetcher()


@pytest.fixture
def valid_input() -> dict[str, str]:
    return {
        "subject": "Linear Algebra",
        "level": "Undergraduate",
        "syllabus": (
            "Week 1: vectors, vector addition and scalar multiplication. "
            "Week 2: dot products, norms and orthogonality. "
            "Week 3: matrices and systems of linear equations."
        ),
    }


@pytest.fixture
def valid_breakdown() -> SyllabusBreakdown:
    return SyllabusBreakdown.model_validate(
        {
            "subject": "Linear Algebra",
            "level": "Undergraduate",
            "topics": [
                {
                    "title": "Vectors",
                    "summary": "Vector operations and geometry.",
                    "units": [
                        {
                            "title": "Vector basics",
                            "objective": "Explain vectors and their notation.",
                            "checklist": [{"text": "Define a vector in R^n."}],
                            "search_query": "linear algebra vectors introduction",
                        }
                    ],
                }
            ],
        }
    )
