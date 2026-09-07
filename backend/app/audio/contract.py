"""
The internal audio contract.

Every AI module in VoiceShield agrees to receive audio in exactly this form,
so the contract lives in one place. Values default from application settings
(which read the environment), keeping them configurable and un-hard-coded.
"""

from dataclasses import dataclass

import numpy as np

from app.config import get_settings


@dataclass(frozen=True)
class AudioContract:
    """Canonical audio parameters shared across the system."""

    sample_rate: int = 16_000
    channels: int = 1
    chunk_seconds: float = 2.0
    overlap_seconds: float = 1.0
    min_seconds: float = 1.0
    max_seconds: float = 30.0

    @property
    def chunk_samples(self) -> int:
        return int(self.sample_rate * self.chunk_seconds)

    @property
    def overlap_samples(self) -> int:
        return int(self.sample_rate * self.overlap_seconds)

    @property
    def min_samples(self) -> int:
        return int(self.sample_rate * self.min_seconds)

    @property
    def hop_samples(self) -> int:
        """Samples to advance between consecutive chunks (chunk - overlap)."""
        hop = self.chunk_samples - self.overlap_samples
        # Guard against a misconfigured overlap >= chunk, which would stall.
        return hop if hop > 0 else self.chunk_samples


@dataclass(frozen=True)
class AudioChunk:
    """A single analysis-ready audio chunk.

    `samples` is float32 in [-1, 1]. `index` is its position in the stream,
    and `start_sample` is where it begins in the source signal.
    """

    samples: np.ndarray
    index: int
    start_sample: int
    sample_rate: int

    @property
    def duration_seconds(self) -> float:
        return len(self.samples) / self.sample_rate


def get_contract() -> AudioContract:
    """Build the contract from current application settings."""
    s = get_settings()
    return AudioContract(
        sample_rate=s.audio_sample_rate,
        channels=s.audio_channels,
        chunk_seconds=s.audio_chunk_seconds,
        overlap_seconds=s.audio_overlap_seconds,
    )
