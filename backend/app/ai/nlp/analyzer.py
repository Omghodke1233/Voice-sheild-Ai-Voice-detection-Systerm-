"""
Conversation analysis orchestrator.

Question this module answers:
    "Is the caller using suspicious social-engineering behavior?"

Ties together ASR -> language -> signal detection -> intent scoring and emits
the module contract:

    {
      "module": "conversation_analysis",
      "language": "en",
      "transcript": "...",
      "social_engineering_probability": 0.91,
      "signals": { ...bool per signal... },
      "events": [ {"type": "...", "confidence": 0.9, "description": "..."} ],
      "status": "OK",           # OK | INCONCLUSIVE | ERROR
      "processing_time_ms": 12
    }
"""

from __future__ import annotations

import logging
from typing import Protocol

import numpy as np

from app.ai.base import measure_ms
from app.ai.nlp.asr import Transcriber, get_transcriber
from app.ai.nlp.config import NlpConfig, get_config
from app.ai.nlp.intent_detector import score_conversation
from app.ai.nlp.language import detect_language
from app.ai.nlp.signal_detector import detect_signals

logger = logging.getLogger("voiceshield.ai.nlp")

MODULE_NAME = "conversation_analysis"


class ConversationAnalyzer(Protocol):
    def analyze(
        self, samples: np.ndarray, injected_transcript: str | None = None
    ) -> dict:
        ...


class MockConversationAnalyzer:
    def __init__(
        self,
        config: NlpConfig | None = None,
        transcriber: Transcriber | None = None,
    ) -> None:
        self.config = config or get_config()
        self.transcriber = transcriber or get_transcriber()

    def analyze(
        self, samples: np.ndarray, injected_transcript: str | None = None
    ) -> dict:
        with measure_ms() as elapsed:
            try:
                asr = self.transcriber.transcribe(samples, injected_transcript)
                transcript = asr.get("text", "")

                # No usable transcript => inconclusive, not an error.
                if (
                    asr.get("status") != "OK"
                    or len(transcript) < self.config.min_transcript_chars
                ):
                    return {
                        "module": MODULE_NAME,
                        "language": "unknown",
                        "transcript": transcript,
                        "social_engineering_probability": 0.0,
                        "signals": {},
                        "events": [],
                        "status": "INCONCLUSIVE",
                        "processing_time_ms": elapsed(),
                    }

                language = detect_language(transcript)
                signals = detect_signals(transcript)
                probability, events = score_conversation(signals, self.config)

                result = {
                    "module": MODULE_NAME,
                    "language": language,
                    "transcript": transcript,
                    "social_engineering_probability": probability,
                    "signals": signals,
                    "events": events,
                    "status": "OK",
                    "processing_time_ms": elapsed(),
                }
                logger.info(
                    "conversation analysis complete",
                    extra={"component": "ai.nlp",
                           "status": "OK",
                           "processing_time": result["processing_time_ms"]},
                )
                return result

            except Exception as exc:
                logger.exception("nlp analyzer failed",
                                 extra={"component": "ai.nlp",
                                        "error_type": type(exc).__name__})
                return {
                    "module": MODULE_NAME,
                    "language": "unknown",
                    "transcript": "",
                    "social_engineering_probability": 0.0,
                    "signals": {},
                    "events": [],
                    "status": "ERROR",
                    "processing_time_ms": elapsed(),
                }


def get_analyzer() -> ConversationAnalyzer:
    return MockConversationAnalyzer()
