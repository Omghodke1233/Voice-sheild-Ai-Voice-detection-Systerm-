"""Tests for the risk fusion engine."""

import pytest

from app.risk.config import RiskWeights
from app.risk.fusion import fuse
from app.risk.thresholds import level_for_score


# --- Helpers to build module outputs ---------------------------------------

def voice(prob, status="SUSPICIOUS"):
    return {"module": "voice_authenticity", "synthetic_probability": prob,
            "confidence": 0.8, "status": status}


def speaker(sim, status):
    return {"module": "speaker_verification", "claimed_speaker": "x",
            "similarity": sim, "confidence": 0.8, "status": status}


def nlp(prob, events=None, status="OK"):
    return {"module": "conversation_analysis", "language": "en",
            "social_engineering_probability": prob,
            "signals": {}, "events": events or [], "status": status}


# --- Banding ----------------------------------------------------------------

@pytest.mark.parametrize("score,expected", [
    (0.0, "LOW"), (0.24, "LOW"),
    (0.25, "MEDIUM"), (0.49, "MEDIUM"),
    (0.50, "HIGH"), (0.74, "HIGH"),
    (0.75, "CRITICAL"), (1.0, "CRITICAL"),
])
def test_level_banding(score, expected):
    assert level_for_score(score) == expected


# --- Weighted fusion with all modules present -------------------------------

def test_full_fusion_matches_formula():
    # voice .82, speaker MISMATCH sim .0 -> 0.6+0.4=1.0 risk,
    # social .91, anomaly from 3 hard events -> 1.0
    hard_events = [{"type": "FINANCIAL_REQUEST"}, {"type": "EMERGENCY_CLAIM"},
                   {"type": "OTP_REQUEST"}]
    out = fuse(voice(0.82), speaker(0.0, "MISMATCH"),
               nlp(0.91, hard_events))
    # 0.35*0.82 + 0.30*1.0 + 0.25*0.91 + 0.10*1.0 = 0.9145
    assert out["overall_risk"] == pytest.approx(0.9145, abs=1e-3)
    assert out["risk_level"] == "CRITICAL"
    assert out["contributing_modules"] == 4


def test_genuine_call_is_low():
    out = fuse(voice(0.05, "NORMAL"), speaker(0.95, "MATCH"), nlp(0.0))
    assert out["risk_level"] == "LOW"
    assert out["overall_risk"] < 0.25


def test_cloned_voice_mismatch_high_or_critical():
    out = fuse(voice(0.8, "SUSPICIOUS"), speaker(0.2, "MISMATCH"), nlp(0.0))
    assert out["risk_level"] in {"HIGH", "CRITICAL"}


# --- Missing / inconclusive / error modules ---------------------------------

def test_missing_voice_module_renormalizes():
    # Voice absent; remaining weights (0.30+0.25+0.10=0.65) renormalize.
    out = fuse(None, speaker(0.0, "MISMATCH"), nlp(0.0))
    assert out["voice_suspicion"] is None
    assert out["contributing_modules"] == 3
    # speaker risk 1.0 dominates: 0.30/0.65 * 1.0 ~= 0.4615
    assert out["overall_risk"] == pytest.approx(0.4615, abs=1e-3)


def test_inconclusive_module_excluded():
    out = fuse(voice(0.0, "INCONCLUSIVE"), speaker(0.9, "MATCH"), nlp(0.0))
    assert out["voice_suspicion"] is None


def test_error_module_excluded():
    out = fuse(voice(0.0, "ERROR"), speaker(0.9, "MATCH"), nlp(0.5))
    assert out["voice_suspicion"] is None
    assert out["contributing_modules"] == 3


def test_all_modules_unusable_is_low_not_crash():
    out = fuse(None, None, None)
    assert out["overall_risk"] == 0.0
    assert out["risk_level"] == "LOW"
    assert out["contributing_modules"] == 0


def test_speaker_risk_not_one_minus_similarity():
    # MISMATCH with similarity 0.3 must NOT yield speaker_risk == 0.7.
    out = fuse(None, speaker(0.3, "MISMATCH"), None)
    assert out["speaker_risk"] != pytest.approx(0.7)
    # It uses 0.6 + 0.4*(1-0.3) = 0.88
    assert out["speaker_risk"] == pytest.approx(0.88, abs=1e-3)


def test_weights_must_sum_to_one():
    with pytest.raises(ValueError):
        RiskWeights(voice=0.5, speaker=0.5, social_engineering=0.5,
                    conversation_anomaly=0.5)


def test_recommended_action_present():
    out = fuse(voice(0.9), speaker(0.0, "MISMATCH"), nlp(0.9))
    assert "recommended_action" in out
    assert isinstance(out["recommended_action"], str)
