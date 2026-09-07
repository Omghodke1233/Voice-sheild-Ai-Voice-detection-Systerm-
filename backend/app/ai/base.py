"""
Shared contracts for all AI modules.

Every detector (voice, speaker, NLP) returns a small typed result plus a
standardized status vocabulary. The rest of the system depends only on these
shapes — never on whether a Mock or Real implementation produced them. This is
what lets us build the whole MVP before any model is trained.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from enum import Enum


class ModuleStatus(str, Enum):
    """Status values common in spirit across modules.

    Individual modules narrow these to their documented sets (e.g. the voice
    detector uses NORMAL/SUSPICIOUS/INCONCLUSIVE/ERROR).
    """

    # voice
    NORMAL = "NORMAL"
    SUSPICIOUS = "SUSPICIOUS"
    # speaker
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    # shared
    INCONCLUSIVE = "INCONCLUSIVE"
    ERROR = "ERROR"


@contextmanager
def measure_ms():
    """Context manager yielding a callable that returns elapsed milliseconds.

        with measure_ms() as elapsed:
            ...work...
        result["processing_time_ms"] = elapsed()
    """
    start = time.perf_counter()
    done: dict[str, float] = {}

    def elapsed() -> int:
        # Freeze on first read so the reported value is stable.
        if "v" not in done:
            done["v"] = (time.perf_counter() - start) * 1000.0
        return int(round(done["v"]))

    yield elapsed
