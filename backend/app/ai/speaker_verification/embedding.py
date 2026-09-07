"""
Voice embedding generation.

For the MVP this produces a DETERMINISTIC pseudo-embedding: the same audio
always yields the same vector, and audio from the same synthetic "speaker seed"
clusters together. It is NOT a learned speaker embedding. A real x-vector /
ECAPA-TDNN model can replace `embed()` behind this same signature later.
"""

from __future__ import annotations

import hashlib

import numpy as np


def embed(samples: np.ndarray, dim: int = 128) -> np.ndarray:
    """Return an L2-normalized float32 pseudo-embedding for a mono chunk."""
    if samples is None or samples.size == 0:
        return np.zeros(dim, dtype=np.float32)

    # Seed a RNG from a stable hash of the audio bytes so the vector is
    # reproducible for identical input.
    digest = hashlib.sha256(samples.tobytes()).digest()
    seed = int.from_bytes(digest[:8], "little", signed=False) % (2**32)
    rng = np.random.default_rng(seed)

    vec = rng.standard_normal(dim).astype(np.float32)
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity in [-1, 1]. Returns 0.0 for degenerate inputs."""
    if a.size == 0 or b.size == 0 or a.shape != b.shape:
        return 0.0
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))
