"""
Speaker verification.

Question this module answers:
    "Is this actually the claimed person?"

Contract (output dict):
    {
      "module": "speaker_verification",
      "claimed_speaker": "Rahul",
      "similarity": 0.31,
      "confidence": 0.87,
      "status": "MISMATCH",     # MATCH | MISMATCH | INCONCLUSIVE | ERROR
      "processing_time_ms": 92
    }

IMPORTANT (project rule): similarity is NOT probability. We compare the live
embedding against the enrolled reference using cosine similarity and apply a
documented, configurable threshold. We never report `1 - similarity` as risk;
the risk engine derives speaker risk separately.
"""

from __future__ import annotations

import logging
from typing import Protocol

import numpy as np

from app.ai.base import measure_ms
from app.ai.speaker_verification.config import SpeakerConfig, get_config
from app.ai.speaker_verification.embedding import cosine_similarity, embed
from app.ai.speaker_verification.enrollment import EnrollmentStore, get_store

logger = logging.getLogger("voiceshield.ai.speaker")

MODULE_NAME = "speaker_verification"


class SpeakerVerifier(Protocol):
    def verify(self, samples: np.ndarray, claimed_speaker_id: str) -> dict:
        ...


def _status_from_similarity(similarity: float, cfg: SpeakerConfig) -> str:
    """Map a cosine similarity to a MATCH/MISMATCH/INCONCLUSIVE decision."""
    if similarity >= cfg.match_threshold:
        return "MATCH"
    if similarity >= cfg.match_threshold - cfg.inconclusive_margin:
        return "INCONCLUSIVE"
    return "MISMATCH"


class MockSpeakerVerifier:
    """Verifier using deterministic pseudo-embeddings + cosine similarity."""

    def __init__(
        self,
        config: SpeakerConfig | None = None,
        store: EnrollmentStore | None = None,
    ) -> None:
        self.config = config or get_config()
        self.store = store or get_store()

    def verify(self, samples: np.ndarray, claimed_speaker_id: str) -> dict:
        with measure_ms() as elapsed:
            try:
                reference = self.store.get(claimed_speaker_id)
                if reference is None:
                    # No enrolled profile => cannot verify.
                    return {
                        "module": MODULE_NAME,
                        "claimed_speaker": claimed_speaker_id,
                        "similarity": 0.0,
                        "confidence": 0.0,
                        "status": "INCONCLUSIVE",
                        "processing_time_ms": elapsed(),
                        "reason": "speaker_not_enrolled",
                    }

                if samples is None or samples.size == 0:
                    return {
                        "module": MODULE_NAME,
                        "claimed_speaker": claimed_speaker_id,
                        "similarity": 0.0,
                        "confidence": 0.0,
                        "status": "INCONCLUSIVE",
                        "processing_time_ms": elapsed(),
                        "reason": "empty_audio",
                    }

                live = embed(samples, dim=self.config.embedding_dim)
                similarity = cosine_similarity(live, reference)
                status = _status_from_similarity(similarity, self.config)

                # Confidence reflects distance from the decision boundary, not
                # the similarity itself — a value near the threshold is less
                # certain regardless of MATCH/MISMATCH.
                confidence = float(
                    np.clip(abs(similarity - self.config.match_threshold) * 2, 0, 1)
                )

                result = {
                    "module": MODULE_NAME,
                    "claimed_speaker": claimed_speaker_id,
                    "similarity": round(similarity, 4),
                    "confidence": round(confidence, 4),
                    "status": status,
                    "processing_time_ms": elapsed(),
                }
                logger.info(
                    "speaker verification complete",
                    extra={"component": "ai.speaker", "status": status,
                           "processing_time": result["processing_time_ms"]},
                )
                return result

            except Exception as exc:
                logger.exception("speaker verifier failed",
                                 extra={"component": "ai.speaker",
                                        "error_type": type(exc).__name__})
                return {
                    "module": MODULE_NAME,
                    "claimed_speaker": claimed_speaker_id,
                    "similarity": 0.0,
                    "confidence": 0.0,
                    "status": "ERROR",
                    "processing_time_ms": elapsed(),
                }


def get_verifier() -> SpeakerVerifier:
    """Factory. Returns the mock verifier for the MVP."""
    return MockSpeakerVerifier()
