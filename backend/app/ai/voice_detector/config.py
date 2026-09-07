"""Configuration for the voice deepfake detector."""

from dataclasses import dataclass

from app.config import get_settings


@dataclass(frozen=True)
class VoiceDetectorConfig:
    # synthetic_probability at/above this is flagged SUSPICIOUS.
    threshold: float = 0.5
    # Below this confidence the verdict is downgraded to INCONCLUSIVE.
    min_confidence: float = 0.4


def get_config() -> VoiceDetectorConfig:
    s = get_settings()
    return VoiceDetectorConfig(threshold=s.voice_threshold)
