"""
Core audio preprocessing.

Pipeline: decode -> mono -> resample to 16 kHz -> normalize to float32 [-1, 1]
-> split into overlapping fixed-length chunks.

Dependencies are intentionally minimal (numpy + stdlib `wave`). No ffmpeg,
librosa, or scipy yet — resampling uses linear interpolation, which is fine
for the MVP contract. Higher-quality resampling can be swapped in at Phase 3
behind these same function signatures.
"""

from __future__ import annotations

import io
import logging
import wave

import numpy as np

from app.audio.contract import AudioChunk, AudioContract, get_contract
from app.audio.errors import InsufficientAudioError, UnsupportedFormatError

logger = logging.getLogger("voiceshield.audio")


def pcm16_to_float32(pcm: np.ndarray) -> np.ndarray:
    """Convert int16 PCM samples to float32 normalized to [-1, 1]."""
    if pcm.dtype != np.int16:
        pcm = pcm.astype(np.int16)
    # 32768 = 2**15; dividing by it maps int16 range into [-1, 1).
    return (pcm.astype(np.float32)) / 32768.0


def to_mono(samples: np.ndarray, channels: int) -> np.ndarray:
    """Downmix interleaved multi-channel audio to mono by averaging channels."""
    if channels <= 1:
        return samples.reshape(-1)
    # Interleaved layout: [L0, R0, L1, R1, ...] -> (n_frames, channels).
    frames = samples.reshape(-1, channels)
    return frames.mean(axis=1)


def resample_linear(
    samples: np.ndarray, src_rate: int, dst_rate: int
) -> np.ndarray:
    """Resample a 1-D float signal via linear interpolation.

    Adequate for the MVP. Returns float32. No-op when rates already match.
    """
    if src_rate == dst_rate or samples.size == 0:
        return samples.astype(np.float32, copy=False)

    duration = samples.size / src_rate
    dst_count = int(round(duration * dst_rate))
    if dst_count <= 0:
        return np.zeros(0, dtype=np.float32)

    # Sample positions in the source timeline for each destination sample.
    src_positions = np.linspace(0, samples.size - 1, num=dst_count)
    src_index = np.arange(samples.size)
    resampled = np.interp(src_positions, src_index, samples)
    return resampled.astype(np.float32)


def decode_wav_bytes(data: bytes) -> tuple[np.ndarray, int, int]:
    """Decode WAV bytes into (samples int16, sample_rate, channels).

    Raises UnsupportedFormatError for anything the stdlib `wave` module can't
    read (e.g. non-PCM, non-WAV, or corrupt data).
    """
    try:
        with wave.open(io.BytesIO(data), "rb") as wav:
            channels = wav.getnchannels()
            sample_rate = wav.getframerate()
            sample_width = wav.getsampwidth()
            frames = wav.readframes(wav.getnframes())
    except (wave.Error, EOFError, OSError) as exc:
        raise UnsupportedFormatError(f"cannot decode WAV: {exc}") from exc

    if sample_width != 2:
        raise UnsupportedFormatError(
            f"unsupported sample width {sample_width * 8}-bit; expected 16-bit"
        )

    samples = np.frombuffer(frames, dtype=np.int16)
    if samples.size == 0:
        raise UnsupportedFormatError("WAV contained no audio frames")

    return samples, sample_rate, channels


def chunk_samples(
    samples: np.ndarray, contract: AudioContract | None = None
) -> list[AudioChunk]:
    """Split a mono float32 signal into overlapping fixed-length chunks.

    The final partial segment is zero-padded up to one full chunk so every
    returned chunk has a consistent length for the AI models. A signal shorter
    than the minimum usable duration raises InsufficientAudioError.
    """
    contract = contract or get_contract()

    if samples.size < contract.min_samples:
        raise InsufficientAudioError(
            f"got {samples.size} samples; need at least {contract.min_samples}"
        )

    chunk_len = contract.chunk_samples
    hop = contract.hop_samples

    chunks: list[AudioChunk] = []
    start = 0
    index = 0
    n = samples.size

    while start < n:
        end = start + chunk_len
        segment = samples[start:end]

        if segment.size < chunk_len:
            # Zero-pad the trailing segment to a full chunk length.
            segment = np.pad(segment, (0, chunk_len - segment.size))

        chunks.append(
            AudioChunk(
                samples=segment.astype(np.float32, copy=False),
                index=index,
                start_sample=start,
                sample_rate=contract.sample_rate,
            )
        )
        index += 1

        # Stop once this chunk has consumed the remainder of the signal.
        if end >= n:
            break
        start += hop

    return chunks


def process_wav_bytes(
    data: bytes, contract: AudioContract | None = None
) -> list[AudioChunk]:
    """Full pipeline for an uploaded WAV clip -> analysis-ready chunks.

    Enforces the maximum clip length, decodes, downmixes to mono, resamples to
    the contract sample rate, normalizes to float32 [-1, 1], then chunks.
    """
    contract = contract or get_contract()

    raw, src_rate, channels = decode_wav_bytes(data)

    mono_int16 = to_mono(raw, channels)
    mono_float = pcm16_to_float32(mono_int16)
    resampled = resample_linear(mono_float, src_rate, contract.sample_rate)

    # Enforce the max-clip contract AFTER resampling (in target-rate samples).
    max_samples = int(contract.max_seconds * contract.sample_rate)
    if resampled.size > max_samples:
        logger.info(
            "clip exceeded max length; truncating",
            extra={
                "component": "audio",
                "received_samples": int(resampled.size),
                "max_samples": max_samples,
            },
        )
        resampled = resampled[:max_samples]

    return chunk_samples(resampled, contract)
