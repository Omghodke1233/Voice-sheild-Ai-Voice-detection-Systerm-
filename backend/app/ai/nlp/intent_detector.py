"""
Conversation-level intent scoring and risk-event generation.

Turns the boolean signals from signal_detector into:
  - a social_engineering_probability (bounded, explainable), and
  - a list of discrete risk events with confidences.

The mapping is transparent and rule-based by design.
"""

from __future__ import annotations

from app.ai.nlp.config import NlpConfig, get_config

# Human-readable event metadata per signal.
_EVENT_META: dict[str, tuple[str, str, float]] = {
    # signal: (EVENT_TYPE, description, base_confidence)
    "financial_request": ("FINANCIAL_REQUEST",
                          "Caller requested a financial transaction.", 0.9),
    "payment_request": ("PAYMENT_REQUEST",
                        "Caller pushed for an immediate payment.", 0.88),
    "emergency_claim": ("EMERGENCY_CLAIM",
                       "Caller claimed an emergency to create pressure.", 0.9),
    "urgency": ("URGENCY",
               "Caller used urgency/time-pressure language.", 0.8),
    "credential_request": ("CREDENTIAL_REQUEST",
                          "Caller asked for credentials.", 0.92),
    "otp_request": ("OTP_REQUEST",
                   "Caller asked for a one-time password / code.", 0.95),
    "isolation_tactic": ("ISOLATION_TACTIC",
                        "Caller tried to isolate the target.", 0.85),
    "secret_request": ("SECRET_REQUEST",
                      "Caller asked to keep the matter secret.", 0.75),
    "identity_claim": ("IDENTITY_CLAIM",
                      "Caller asserted a trusted identity.", 0.7),
}


def score_conversation(
    signals: dict[str, bool], config: NlpConfig | None = None
) -> tuple[float, list[dict]]:
    """Return (social_engineering_probability, events)."""
    config = config or get_config()

    active = [s for s, present in signals.items() if present]
    probability = min(1.0, len(active) * config.per_signal_weight)

    events: list[dict] = []
    for signal in active:
        event_type, description, confidence = _EVENT_META.get(
            signal, (signal.upper(), signal, 0.6)
        )
        events.append(
            {"type": event_type, "confidence": confidence,
             "description": description}
        )

    return round(probability, 4), events
