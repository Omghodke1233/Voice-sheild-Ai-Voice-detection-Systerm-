"""
Voice deepfake detection.

Question this module answers:
    "Does this voice contain evidence of synthetic generation?"

Contract (output dict):
    {
      "module": "voice_authenticity",
      "synthetic_probability": 0.82,
      "confidence": 0.78,
      "status": "SUSPICIOUS",       # NORMAL | SUSPICIOUS | INCONCLUSIVE | ERROR
      "processing_time_ms": 145
    }

Two implementations sit behind one interface:
  - MockVoiceDetector: deterministic, feature-driven heuristic. No ML.
  - (future) RealVoiceDetector: a trained anti-spoofing model.

IMPORTANT: this MVP makes no accuracy claims. The mock is a stand-in that
produces plausible, explainable outputs so the rest of the system can be built
and demoed.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Protocol

import numpy as np

from app.ai.base import measure_ms
from app.ai.voice_detector.config import VoiceDetectorConfig, get_config
from app.ai.voice_detector.preprocessing import extract_features

logger = logging.getLogger("voiceshield.ai.voice")

MODULE_NAME = "voice_authenticity"


class VoiceDetector(Protocol):
    """Interface every voice detector implementation must satisfy."""

    def analyze(self, samples: np.ndarray) -> dict:
        ...


def _status_from(prob: float, confidence: float, cfg: VoiceDetectorConfig) -> str:
    if confidence < cfg.min_confidence:
        return "INCONCLUSIVE"
    return "SUSPICIOUS" if prob >= cfg.threshold else "NORMAL"


class MockVoiceDetector:
    """Deterministic mock detector driven by cheap acoustic features.

    The score is derived from the audio itself (so identical audio yields
    identical results, and tests are stable) but is explicitly NOT a real
    spoofing model. It combines a feature signal with a per-chunk hash jitter
    to produce varied, plausible probabilities for the demo.
    """

    def __init__(self, config: VoiceDetectorConfig | None = None) -> None:
        self.config = config or get_config()

    def analyze(self, samples: np.ndarray) -> dict:
        with measure_ms() as elapsed:
            try:
                if samples is None or samples.size == 0:
                    return {
                        "module": MODULE_NAME,
                        "synthetic_probability": 0.0,
                        "confidence": 0.0,
                        "status": "INCONCLUSIVE",
                        "processing_time_ms": elapsed(),
                    }

                feats = extract_features(samples)

                # Mostly-silent chunks can't support a verdict.
                if feats["silence_ratio"] > 0.9:
                    return {
                        "module": MODULE_NAME,
                        "synthetic_probability": 0.0,
                        "confidence": 0.2,
                        "status": "INCONCLUSIVE",
                        "processing_time_ms": elapsed(),
                        "features": feats,
                    }

                # Deterministic pseudo-signal from the audio content.
                digest = hashlib.sha256(samples.tobytes()).digest()
                jitter = digest[0] / 255.0  # 0..1

                # Blend an (arbitrary but stable) feature term with jitter.
                # High ZCR + very smooth RMS are loosely "synthetic-ish" here.
                feature_term = min(1.0, feats["zero_crossing_rate"] * 1.5)
                prob = float(np.clip(0.5 * feature_term + 0.5 * jitter, 0.0, 1.0))
                confidence = float(np.clip(0.6 + 0.4 * (1 - feats["silence_ratio"]), 0, 1))

                status = _status_from(prob, confidence, self.config)
                result = {
                    "module": MODULE_NAME,
                    "synthetic_probability": round(prob, 4),
                    "confidence": round(confidence, 4),
                    "status": status,
                    "processing_time_ms": elapsed(),
                }
                logger.info(
                    "voice analysis complete",
                    extra={"component": "ai.voice", "status": status,
                           "processing_time": result["processing_time_ms"]},
                )
                return result

            except Exception as exc:  # never let one module crash the call
                logger.exception("voice detector failed",
                                 extra={"component": "ai.voice",
                                        "error_type": type(exc).__name__})
                return {
                    "module": MODULE_NAME,
                    "synthetic_probability": 0.0,
                    "confidence": 0.0,
                    "status": "ERROR",
                    "processing_time_ms": elapsed(),
                }


def get_detector() -> VoiceDetector:
    """Factory. Returns the mock detector for the MVP.

    When a real model is available, select it here (e.g. via settings) without
    changing any caller.
    """
    return MockVoiceDetector()
