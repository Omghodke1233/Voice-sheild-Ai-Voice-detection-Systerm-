"""Tests for ASR + conversational analysis (mock)."""

import numpy as np

from app.ai.nlp.analyzer import MockConversationAnalyzer
from app.ai.nlp.signal_detector import detect_signals

DUMMY_AUDIO = np.zeros(32_000, dtype=np.float32)


def analyze(text):
    return MockConversationAnalyzer().analyze(DUMMY_AUDIO, injected_transcript=text)


def test_normal_conversation_low_probability():
    out = analyze("Hi, are we still meeting for lunch tomorrow?")
    assert out["status"] == "OK"
    assert out["social_engineering_probability"] < 0.3
    assert out["events"] == []


def test_financial_request_detected():
    out = analyze("Please transfer the money to this bank account now.")
    assert out["signals"]["financial_request"] is True
    assert any(e["type"] == "FINANCIAL_REQUEST" for e in out["events"])


def test_otp_request_detected():
    out = analyze("Read me the OTP you just received.")
    assert out["signals"]["otp_request"] is True
    assert any(e["type"] == "OTP_REQUEST" for e in out["events"])


def test_full_attack_high_probability():
    text = ("This is an emergency, I need you to transfer money immediately. "
            "Don't tell anyone, and read me the OTP right now.")
    out = analyze(text)
    assert out["social_engineering_probability"] >= 0.75
    types = {e["type"] for e in out["events"]}
    assert "EMERGENCY_CLAIM" in types
    assert "FINANCIAL_REQUEST" in types
    assert "URGENCY" in types


def test_empty_transcript_is_inconclusive():
    out = analyze("")
    assert out["status"] == "INCONCLUSIVE"
    assert out["social_engineering_probability"] == 0.0


def test_no_injected_text_is_inconclusive():
    out = MockConversationAnalyzer().analyze(DUMMY_AUDIO)
    assert out["status"] == "INCONCLUSIVE"


def test_short_token_word_boundary_no_false_positive():
    # "pin" must not trigger inside "shipping".
    signals = detect_signals("the shipping update is ready")
    assert signals["credential_request"] is False


def test_output_contract_keys():
    out = analyze("hello there friend")
    for key in ("module", "language", "transcript",
                "social_engineering_probability", "signals", "events",
                "status", "processing_time_ms"):
        assert key in out
    assert out["module"] == "conversation_analysis"
