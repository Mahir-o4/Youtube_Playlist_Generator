from __future__ import annotations

import threading
import time

from core.concurrency import map_parallel


def test_map_parallel_preserves_input_order() -> None:
    assert map_parallel(lambda value: value * 2, [3, 1, 2], workers=3) == [6, 2, 4]


def test_map_parallel_actually_overlaps_work() -> None:
    active = 0
    peak = 0
    lock = threading.Lock()

    def work(value: int) -> int:
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        time.sleep(0.05)
        with lock:
            active -= 1
        return value

    map_parallel(work, range(6), workers=3)
    assert peak > 1
