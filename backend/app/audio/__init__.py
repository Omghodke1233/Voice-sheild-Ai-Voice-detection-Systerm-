"""
Audio preprocessing package.

Shared, cross-cutting audio utilities used by all three AI modules
(deepfake detection, speaker verification, ASR+NLP). Converts arbitrary
incoming audio into the project's internal contract: 16 kHz, mono, float32,
normalized to [-1, 1], split into fixed-length analysis chunks.
"""

from app.audio.contract import AudioChunk, AudioContract, get_contract
from app.audio.errors import (
    AudioError,
    InsufficientAudioError,
    UnsupportedFormatError,
)
from app.audio.processor import (
    chunk_samples,
    pcm16_to_float32,
    process_wav_bytes,
    resample_linear,
    to_mono,
)

__all__ = [
    "AudioChunk",
    "AudioContract",
    "get_contract",
    "AudioError",
    "InsufficientAudioError",
    "UnsupportedFormatError",
    "chunk_samples",
    "pcm16_to_float32",
    "process_wav_bytes",
    "resample_linear",
    "to_mono",
]
