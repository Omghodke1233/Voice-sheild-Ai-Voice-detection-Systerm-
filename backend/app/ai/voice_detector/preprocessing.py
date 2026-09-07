"""
Lightweight acoustic feature extraction for the voice detector.

These are cheap, explainable numpy features (not a learned frontend). They give
the mock detector something real to react to and give a future real model a
stable place to plug in. No librosa dependency yet.
"""

from __future__ import annotations

import numpy as np


def extract_features(samples: np.ndarray) -> dict[str, float]:
    """Return a few basic time-domain features from a float32 mono chunk."""
    if samples.size == 0:
        return {"rms": 0.0, "zero_crossing_rate": 0.0, "silence_ratio": 1.0}

    rms = float(np.sqrt(np.mean(samples**2)))

    # Zero-crossing rate: fraction of adjacent samples that change sign.
    signs = np.signbit(samples)
    zcr = float(np.mean(signs[1:] != signs[:-1])) if samples.size > 1 else 0.0

    # Silence ratio: fraction of samples below a small amplitude threshold.
    silence_ratio = float(np.mean(np.abs(samples) < 1e-3))

    return {
        "rms": rms,
        "zero_crossing_rate": zcr,
        "silence_ratio": silence_ratio,
    }
