"""Configuration for the ASR + conversational analysis module."""

from dataclasses import dataclass


@dataclass(frozen=True)
class NlpConfig:
    # Each detected signal contributes this much toward the social-engineering
    # probability, capped at 1.0. Kept explicit and explainable per project
    # rules — this is rule-based scoring, not a learned classifier.
    per_signal_weight: float = 0.28
    # Minimum transcript length (chars) to attempt analysis.
    min_transcript_chars: int = 2


def get_config() -> NlpConfig:
    return NlpConfig()
