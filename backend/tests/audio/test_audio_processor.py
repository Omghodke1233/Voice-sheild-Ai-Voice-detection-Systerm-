"""Tests for the Phase 2 audio preprocessing pipeline."""

import io
import wave

import numpy as np
import pytest

from app.audio.contract import AudioContract
from app.audio.errors import InsufficientAudioError, UnsupportedFormatError
from app.audio.processor import (
    chunk_samples,
    pcm16_to_float32,
    process_wav_bytes,
    resample_linear,
    to_mono,
)

CONTRACT = AudioContract()  # 16kHz, mono, 2s chunk, 1s overlap, 1s min


def _make_wav_bytes(
    samples: np.ndarray, sample_rate: int, channels: int
) -> bytes:
    """Encode int16 samples into WAV container bytes for testing."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(2)  # 16-bit
        wav.setframerate(sample_rate)
        wav.writeframes(samples.astype(np.int16).tobytes())
    return buf.getvalue()


def _tone(seconds: float, sample_rate: int, channels: int = 1) -> np.ndarray:
    """Generate an int16 sine tone; if stereo, interleave two channels."""
    n = int(seconds * sample_rate)
    t = np.linspace(0, seconds, n, endpoint=False)
    wave_f = (np.sin(2 * np.pi * 220 * t) * 10000).astype(np.int16)
    if channels == 1:
        return wave_f
    return np.repeat(wave_f, channels)  # interleaved L,R,L,R,...


# --- Unit-level conversions -------------------------------------------------


def test_pcm16_to_float32_range():
    pcm = np.array([-32768, 0, 32767], dtype=np.int16)
    out = pcm16_to_float32(pcm)
    assert out.dtype == np.float32
    assert out.min() >= -1.0 and out.max() <= 1.0


def test_to_mono_averages_channels():
    interleaved = np.array([100, 300, 200, 400], dtype=np.int16)  # 2 frames
    mono = to_mono(interleaved, channels=2)
    assert np.allclose(mono, [200, 300])


def test_resample_changes_length_to_target_rate():
    src = np.zeros(48_000, dtype=np.float32)  # 1s @ 48kHz
    out = resample_linear(src, 48_000, 16_000)
    assert abs(len(out) - 16_000) <= 1
    assert out.dtype == np.float32


def test_resample_noop_when_rates_match():
    src = np.ones(1000, dtype=np.float32)
    out = resample_linear(src, 16_000, 16_000)
    assert len(out) == 1000


# --- Chunking ---------------------------------------------------------------


def test_chunk_count_and_shape_for_5s():
    # 5s @ 16kHz, 2s chunk, 1s hop -> starts at 0,1,2,3s; the 3s chunk spans
    # 3-5s and reaches the end, so the loop stops -> 4 chunks total.
    samples = np.zeros(5 * CONTRACT.sample_rate, dtype=np.float32)
    chunks = chunk_samples(samples, CONTRACT)
    assert len(chunks) == 4
    # Every chunk padded to a full 2s length.
    for c in chunks:
        assert len(c.samples) == CONTRACT.chunk_samples
        assert c.samples.dtype == np.float32
    # Indices and start positions are monotonic and correctly spaced.
    assert [c.index for c in chunks] == [0, 1, 2, 3]
    assert chunks[1].start_sample == CONTRACT.hop_samples


def test_chunk_rejects_too_short_audio():
    samples = np.zeros(int(0.5 * CONTRACT.sample_rate), dtype=np.float32)
    with pytest.raises(InsufficientAudioError):
        chunk_samples(samples, CONTRACT)


def test_short_but_usable_audio_yields_one_padded_chunk():
    # 1.2s: above 1s minimum, below one 2s chunk -> single zero-padded chunk.
    samples = np.ones(int(1.2 * CONTRACT.sample_rate), dtype=np.float32)
    chunks = chunk_samples(samples, CONTRACT)
    assert len(chunks) == 1
    assert len(chunks[0].samples) == CONTRACT.chunk_samples


# --- Full WAV pipeline ------------------------------------------------------


def test_process_wav_resamples_and_chunks():
    wav_bytes = _make_wav_bytes(_tone(3.0, 44_100), 44_100, channels=1)
    chunks = process_wav_bytes(wav_bytes, CONTRACT)
    assert len(chunks) >= 1
    assert all(c.sample_rate == 16_000 for c in chunks)
    assert all(c.samples.max() <= 1.0 and c.samples.min() >= -1.0 for c in chunks)


def test_process_wav_downmixes_stereo():
    wav_bytes = _make_wav_bytes(_tone(2.0, 16_000, channels=2), 16_000, 2)
    chunks = process_wav_bytes(wav_bytes, CONTRACT)
    assert len(chunks) >= 1
    assert all(c.samples.ndim == 1 for c in chunks)


def test_process_wav_truncates_over_max_length():
    # 35s clip should be truncated to 30s -> at most 30 one-second-hop chunks.
    wav_bytes = _make_wav_bytes(_tone(35.0, 16_000), 16_000, 1)
    chunks = process_wav_bytes(wav_bytes, CONTRACT)
    assert chunks[-1].start_sample < 30 * CONTRACT.sample_rate


def test_process_rejects_non_wav_bytes():
    with pytest.raises(UnsupportedFormatError):
        process_wav_bytes(b"this is not a wav file", CONTRACT)


def test_process_rejects_empty_bytes():
    with pytest.raises(UnsupportedFormatError):
        process_wav_bytes(b"", CONTRACT)
