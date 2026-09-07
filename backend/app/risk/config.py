"""
Risk fusion configuration.

Weights and thresholds are centralized and configurable. Thresholds read from
application settings (env), weights are defined here and sum to 1.0.
"""

from dataclasses import dataclass

from app.config import get_settings


@dataclass(frozen=True)
class RiskWeights:
    """Fusion weights. Must sum to 1.0 (validated at construction)."""

    voice: float = 0.35
    speaker: float = 0.30
    social_engineering: float = 0.25
    conversation_anomaly: float = 0.10

    def __post_init__(self) -> None:
        total = self.voice + self.speaker + self.social_engineering + \
            self.conversation_anomaly
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"risk weights must sum to 1.0, got {total}")


@dataclass(frozen=True)
class RiskThresholds:
    """Upper bounds (inclusive lower) for each risk band.

        [0, low)        -> LOW
        [low, medium)   -> MEDIUM
        [medium, high)  -> HIGH
        [high, 1.0]     -> CRITICAL
    """

    low: float = 0.25
    medium: float = 0.50
    high: float = 0.75


def get_weights() -> RiskWeights:
    return RiskWeights()


def get_thresholds() -> RiskThresholds:
    s = get_settings()
    return RiskThresholds(
        low=s.risk_threshold_low,
        medium=s.risk_threshold_medium,
        high=s.risk_threshold_high,
    )
