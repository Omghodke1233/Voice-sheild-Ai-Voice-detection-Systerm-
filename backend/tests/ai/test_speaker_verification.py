"""Tests for mock speaker verification."""

import numpy as np

from app.ai.speaker_verification.config import SpeakerConfig
from app.ai.speaker_verification.embedding import cosine_similarity, embed
from app.ai.speaker_verification.enrollment import EnrollmentStore
from app.ai.speaker_verification.verification import MockSpeakerVerifier

CONTRACT_LEN = 32_000


def _audio(seed):
    rng = np.random.default_rng(seed)
    return rng.standard_normal(CONTRACT_LEN).astype(np.float32) * 0.3


def test_embedding_is_normalized_and_deterministic():
    a = _audio(1)
    e1 = embed(a.copy())
    e2 = embed(a.copy())
    assert np.allclose(e1, e2)
    assert abs(np.linalg.norm(e1) - 1.0) < 1e-5


def test_same_audio_matches_itself():
    store = EnrollmentStore()
    audio = _audio(5)
    store.enroll("spk", audio.copy())
    verifier = MockSpeakerVerifier(SpeakerConfig(match_threshold=0.5), store)
    out = verifier.verify(audio.copy(), "spk")
    assert out["status"] == "MATCH"
    assert out["similarity"] > 0.99


def test_different_audio_mismatches():
    store = EnrollmentStore()
    store.enroll("spk", _audio(10))
    verifier = MockSpeakerVerifier(SpeakerConfig(match_threshold=0.5), store)
    out = verifier.verify(_audio(999), "spk")
    assert out["status"] in {"MISMATCH", "INCONCLUSIVE"}
    assert out["module"] == "speaker_verification"


def test_unknown_speaker_is_inconclusive():
    verifier = MockSpeakerVerifier(SpeakerConfig(), EnrollmentStore())
    out = verifier.verify(_audio(3), "does_not_exist")
    assert out["status"] == "INCONCLUSIVE"
    assert out["reason"] == "speaker_not_enrolled"


def test_empty_audio_is_inconclusive():
    store = EnrollmentStore()
    store.enroll("spk", _audio(2))
    verifier = MockSpeakerVerifier(SpeakerConfig(), store)
    out = verifier.verify(np.zeros(0, dtype=np.float32), "spk")
    assert out["status"] == "INCONCLUSIVE"


def test_output_contract_keys_and_time():
    store = EnrollmentStore()
    store.enroll("spk", _audio(2))
    out = MockSpeakerVerifier(SpeakerConfig(), store).verify(_audio(2), "spk")
    for key in ("module", "claimed_speaker", "similarity", "confidence",
                "status", "processing_time_ms"):
        assert key in out
    assert isinstance(out["processing_time_ms"], int)


def test_cosine_similarity_edge_cases():
    assert cosine_similarity(np.zeros(4), np.zeros(4)) == 0.0
    assert cosine_similarity(np.ones(4), np.ones(3)) == 0.0
