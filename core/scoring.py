"""Deterministic popularity scoring for the 20 -> 5 shortlist."""

from __future__ import annotations

import math
from collections.abc import Sequence

from schemas import VideoCandidate

POPULARITY_WEIGHTS = {"views": 0.40, "likes": 0.35, "comments": 0.25}


def _log_normalize(values: Sequence[int]) -> list[float]:
    logs = [math.log1p(max(int(value), 0)) for value in values]
    low, high = min(logs), max(logs)
    if high == low:
        return [0.5] * len(logs)
    return [(value - low) / (high - low) for value in logs]


def score_candidates(candidates: Sequence[VideoCandidate]) -> list[VideoCandidate]:
    """Score within the candidate pool and return a descending copy."""
    if not candidates:
        return []
    views = _log_normalize([c.views for c in candidates])
    likes = _log_normalize([c.likes for c in candidates])
    comments = _log_normalize([c.comments for c in candidates])

    scored: list[VideoCandidate] = []
    for candidate, v, l, c in zip(candidates, views, likes, comments):
        scored.append(
            candidate.model_copy(
                update={
                    "popularity_score": round(
                        POPULARITY_WEIGHTS["views"] * v
                        + POPULARITY_WEIGHTS["likes"] * l
                        + POPULARITY_WEIGHTS["comments"] * c,
                        6,
                    )
                }
            )
        )
    return sorted(scored, key=lambda item: (-item.popularity_score, -item.views))
