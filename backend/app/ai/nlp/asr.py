"""
Automatic speech recognition (ASR).

For the MVP this is a mock transcriber behind the same interface a real Whisper
model will use. It does NOT invent speech from audio; instead it accepts an
optional injected transcript (e.g. from demo scenarios or the WebSocket layer)
and otherwise returns an empty transcript with a clear status.

This honors the project rule against pretending mock output is real ASR: the
mock is explicit and the interface is stable for a real model swap.
"""

from __future__ import annotations

from typing import Protocol

import numpy as np


class Transcriber(Protocol):
    def transcribe(
        self, samples: np.ndarray, injected_text: str | None = None
    ) -> dict:
        ...


class MockTranscriber:
    """Returns injected text if provided; otherwise an empty transcript."""

    def transcribe(
        self, samples: np.ndarray, injected_text: str | None = None
    ) -> dict:
        if injected_text is not None:
            text = injected_text.strip()
            return {
                "text": text,
                "status": "OK" if text else "EMPTY",
                "source": "injected",
            }

        # No real ASR in the MVP mock and no injected text.
        return {"text": "", "status": "EMPTY", "source": "mock"}


def get_transcriber() -> Transcriber:
    return MockTranscriber()
