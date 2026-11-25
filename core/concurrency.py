"""Bounded thread helpers for independent I/O work."""

from __future__ import annotations

import os
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar

T = TypeVar("T")
R = TypeVar("R")


def worker_count(env_name: str, default: int) -> int:
    try:
        return max(1, int(os.getenv(env_name, str(default))))
    except ValueError:
        return default


def map_parallel(
    function: Callable[[T], R], items: Iterable[T], workers: int = 4
) -> list[R]:
    """Map a function over items in bounded parallel, preserving input order."""
    ordered = list(items)
    if not ordered:
        return []
    if workers <= 1:
        return [function(item) for item in ordered]
    with ThreadPoolExecutor(max_workers=min(workers, len(ordered))) as pool:
        return list(pool.map(function, ordered))
