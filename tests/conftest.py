from __future__ import annotations

import pytest

from schemas import SyllabusBreakdown


@pytest.fixture
def valid_input() -> dict[str, str]:
    return {
        "subject": "Linear Algebra",
        "level": "Undergraduate",
        "language": "English",
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
            "language": "English",
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
