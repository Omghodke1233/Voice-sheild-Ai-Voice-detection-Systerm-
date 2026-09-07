"""
Analysis orchestration.

Runs the three AI modules over one audio chunk and fuses their outputs into a
risk assessment. This is the single seam the WebSocket layer (Phase 5) will
call per chunk. Modules are constructed once and reused.

Each module is wrapped defensively: if any raises unexpectedly, its result is
treated as ERROR and fusion continues with the others (project rule: one
module failing must not crash the call).
"""

from __future__ import annotations

import logging

import numpy as np

from app.ai.nlp.analyzer import ConversationAnalyzer, get_analyzer
from app.ai.speaker_verification.verification import (
    SpeakerVerifier,
    get_verifier,
)
from app.ai.voice_detector.detector import VoiceDetector, get_detector
from app.risk.fusion import fuse

logger = logging.getLogger("voiceshield.services.analysis")


class AnalysisService:
    def __init__(
        self,
        voice: VoiceDetector | None = None,
        speaker: SpeakerVerifier | None = None,
        nlp: ConversationAnalyzer | None = None,
    ) -> None:
        self.voice = voice or get_detector()
        self.speaker = speaker or get_verifier()
        self.nlp = nlp or get_analyzer()

    def analyze_chunk(
        self,
        samples: np.ndarray,
        claimed_speaker_id: str | None = None,
        injected_transcript: str | None = None,
    ) -> dict:
        """Analyze one chunk and return module outputs + fused risk."""
        voice_out = self._safe(lambda: self.voice.analyze(samples), "voice")
        speaker_out = None
        if claimed_speaker_id is not None:
            speaker_out = self._safe(
                lambda: self.speaker.verify(samples, claimed_speaker_id),
                "speaker",
            )
        nlp_out = self._safe(
            lambda: self.nlp.analyze(samples, injected_transcript), "nlp"
        )

        risk = fuse(voice_out, speaker_out, nlp_out)

        return {
            "voice": voice_out,
            "speaker": speaker_out,
            "nlp": nlp_out,
            "risk": risk,
        }

    @staticmethod
    def _safe(fn, component: str) -> dict:
        """Run a module call, converting any hard failure into an ERROR dict."""
        try:
            return fn()
        except Exception as exc:  # defensive; modules already catch internally
            logger.exception(
                "module raised unexpectedly",
                extra={"component": f"ai.{component}",
                       "error_type": type(exc).__name__},
            )
            return {"module": component, "status": "ERROR"}
