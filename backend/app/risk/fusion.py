"""
Risk fusion engine.

Combines the three AI module outputs into a single normalized risk score and
level. Design rules enforced here:

  * Weighted fusion:
        0.35 voice + 0.30 speaker + 0.25 social_eng + 0.10 conv_anomaly
  * A module that is missing / INCONCLUSIVE / ERROR is EXCLUDED, and the
    remaining weights are renormalized so one failed module never crashes or
    zeroes the whole assessment.
  * Speaker RISK is derived from the verification STATUS + similarity, not by
    naively computing (1 - similarity). Similarity is not a probability.
  * The output score is "normalized evidence/severity of a POSSIBLE
    impersonation attack" — not proof, not a fraud probability.
"""

from __future__ import annotations

import logging

from app.risk.config import RiskWeights, get_weights
from app.risk.decision import action_for_level
from app.risk.thresholds import level_for_score

logger = logging.getLogger("voiceshield.risk")

# Statuses that mean "no usable signal from this module".
_UNUSABLE = {"INCONCLUSIVE", "ERROR"}


def _voice_component(voice: dict | None) -> float | None:
    if not voice or voice.get("status") in _UNUSABLE:
        return None
    return _clamp(float(voice.get("synthetic_probability", 0.0)))


def _speaker_component(speaker: dict | None) -> float | None:
    """Derive speaker RISK from status + similarity (never 1 - similarity)."""
    if not speaker or speaker.get("status") in _UNUSABLE:
        return None

    status = speaker.get("status")
    similarity = _clamp(float(speaker.get("similarity", 0.0)))

    if status == "MISMATCH":
        # Lower similarity => higher risk, but scaled into a high band so a
        # mismatch is meaningfully risky without equating risk to 1-similarity.
        return _clamp(0.6 + 0.4 * (1.0 - similarity))
    if status == "MATCH":
        # A genuine match contributes low risk.
        return _clamp(0.2 * (1.0 - similarity))
    return None


def _social_component(nlp: dict | None) -> float | None:
    if not nlp or nlp.get("status") in _UNUSABLE:
        return None
    return _clamp(float(nlp.get("social_engineering_probability", 0.0)))


def _conversation_anomaly_component(nlp: dict | None) -> float | None:
    """A coarse anomaly proxy: presence of high-severity event types.

    Distinct from the social-engineering probability so the two NLP-derived
    inputs aren't identical. Uses the count of 'hard' events.
    """
    if not nlp or nlp.get("status") in _UNUSABLE:
        return None
    events = nlp.get("events", []) or []
    hard = {"OTP_REQUEST", "CREDENTIAL_REQUEST", "FINANCIAL_REQUEST",
            "PAYMENT_REQUEST", "EMERGENCY_CLAIM"}
    hard_count = sum(1 for e in events if e.get("type") in hard)
    if not events:
        return 0.0
    return _clamp(hard_count / 3.0)


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def fuse(
    voice: dict | None,
    speaker: dict | None,
    nlp: dict | None,
    weights: RiskWeights | None = None,
) -> dict:
    """Fuse module outputs into an overall risk assessment.

    Any argument may be None or carry an INCONCLUSIVE/ERROR status; such
    modules are dropped and the remaining weights renormalized.
    """
    weights = weights or get_weights()

    components = {
        "voice_suspicion": (_voice_component(voice), weights.voice),
        "speaker_risk": (_speaker_component(speaker), weights.speaker),
        "social_engineering": (_social_component(nlp), weights.social_engineering),
        "conversation_anomaly": (
            _conversation_anomaly_component(nlp), weights.conversation_anomaly),
    }

    usable = {k: (v, w) for k, (v, w) in components.items() if v is not None}
    total_weight = sum(w for _, w in usable.values())

    if total_weight <= 0:
        # No usable modules at all: report an inconclusive, zero-risk result
        # rather than crashing.
        overall = 0.0
        level = "LOW"
        contributing = 0
    else:
        overall = sum(v * w for v, w in usable.values()) / total_weight
        overall = round(_clamp(overall), 4)
        level = level_for_score(overall)
        contributing = len(usable)

    # Report each component's value (None -> unavailable) for transparency.
    breakdown = {k: (round(v, 4) if v is not None else None)
                 for k, (v, w) in components.items()}

    result = {
        "voice_suspicion": breakdown["voice_suspicion"],
        "speaker_risk": breakdown["speaker_risk"],
        "social_engineering": breakdown["social_engineering"],
        "conversation_anomaly": breakdown["conversation_anomaly"],
        "overall_risk": overall,
        "risk_level": level,
        "recommended_action": action_for_level(level),
        "contributing_modules": contributing,
    }
    logger.info(
        "risk fusion complete",
        extra={"component": "risk", "status": level,
               "contributing_modules": contributing},
    )
    return result
