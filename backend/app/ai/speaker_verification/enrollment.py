"""
Speaker enrollment store.

Holds enrolled speakers' reference embeddings for the MVP. This is an in-memory
store keyed by speaker_id; a real deployment would persist encrypted embeddings
(see privacy rules) rather than keep them in process memory.

We deliberately store only embeddings (derived vectors), never raw audio.
"""

from __future__ import annotations

import threading

import numpy as np

from app.ai.speaker_verification.embedding import embed


class EnrollmentStore:
    """Thread-safe in-memory map of speaker_id -> reference embedding."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._embeddings: dict[str, np.ndarray] = {}

    def enroll(self, speaker_id: str, samples: np.ndarray, dim: int = 128) -> None:
        """Create/replace a speaker's reference embedding from audio."""
        vector = embed(samples, dim=dim)
        with self._lock:
            self._embeddings[speaker_id] = vector

    def enroll_vector(self, speaker_id: str, vector: np.ndarray) -> None:
        """Register a precomputed embedding directly (used in tests/seeding)."""
        with self._lock:
            self._embeddings[speaker_id] = vector.astype(np.float32)

    def get(self, speaker_id: str) -> np.ndarray | None:
        with self._lock:
            return self._embeddings.get(speaker_id)

    def is_enrolled(self, speaker_id: str) -> bool:
        with self._lock:
            return speaker_id in self._embeddings

    def clear(self) -> None:
        with self._lock:
            self._embeddings.clear()


# Process-wide singleton for the MVP.
_store = EnrollmentStore()


def get_store() -> EnrollmentStore:
    return _store
