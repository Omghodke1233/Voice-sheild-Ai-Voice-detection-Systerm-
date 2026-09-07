"""Tests for the mock voice deepfake detector."""

import numpy as np

from app.ai.voice_detector.config import VoiceDetectorConfig
from app.ai.voice_detector.detector import MockVoiceDetector

CONTRACT_LEN = 32_000  # 2s @ 16kHz


def _noise(n=CONTRACT_LEN, seed=0):
    rng = np.random.default_rng(seed)
    return rng.standard_normal(n).astype(np.float32) * 0.2


def test_output_contract_keys():
    out = MockVoiceDetector().analyze(_noise())
    for key in ("module", "synthetic_probability", "confidence", "status",
                "processing_time_ms"):
        assert key in out
    assert out["module"] == "voice_authenticity"
    assert out["status"] in {"NORMAL", "SUSPICIOUS", "INCONCLUSIVE", "ERROR"}


def test_probability_in_range_and_time_reported():
    out = MockVoiceDetector().analyze(_noise())
    assert 0.0 <= out["synthetic_probability"] <= 1.0
    assert 0.0 <= out["confidence"] <= 1.0
    assert isinstance(out["processing_time_ms"], int)
    assert out["processing_time_ms"] >= 0


def test_deterministic_for_same_audio():
    audio = _noise(seed=42)
    a = MockVoiceDetector().analyze(audio.copy())
    b = MockVoiceDetector().analyze(audio.copy())
    assert a["synthetic_probability"] == b["synthetic_probability"]
    assert a["status"] == b["status"]


def test_empty_audio_is_inconclusive():
    out = MockVoiceDetector().analyze(np.zeros(0, dtype=np.float32))
    assert out["status"] == "INCONCLUSIVE"


def test_silence_is_inconclusive():
    out = MockVoiceDetector().analyze(np.zeros(CONTRACT_LEN, dtype=np.float32))
    assert out["status"] == "INCONCLUSIVE"


def test_threshold_controls_status():
    audio = _noise(seed=7)
    # Force everything suspicious with threshold 0, then normal with 1.
    low = MockVoiceDetector(VoiceDetectorConfig(threshold=0.0)).analyze(audio.copy())
    high = MockVoiceDetector(VoiceDetectorConfig(threshold=1.01)).analyze(audio.copy())
    assert low["status"] in {"SUSPICIOUS", "INCONCLUSIVE"}
    assert high["status"] in {"NORMAL", "INCONCLUSIVE"}
