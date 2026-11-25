"""Node: deterministically reduce 20 candidates to 5 finalists per unit."""

from __future__ import annotations

import os

from core.scoring import score_candidates
from graph.state import WorkflowState


def popularity_ranking(state: WorkflowState) -> dict:
    candidates = state.get("candidates") or {}
    if not candidates:
        return {"finalists": {}, "error": None}
    limit = int(os.getenv("YOUTUBE_FINALISTS", "5"))
    finalists = {
        key: score_candidates(items)[:limit] for key, items in candidates.items()
    }
    return {"finalists": finalists, "error": None}
