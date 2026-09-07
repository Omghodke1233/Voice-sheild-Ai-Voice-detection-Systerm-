"""Risk-level banding."""

from __future__ import annotations

from app.risk.config import RiskThresholds, get_thresholds


def level_for_score(score: float, thresholds: RiskThresholds | None = None) -> str:
    """Map a [0,1] risk score to LOW / MEDIUM / HIGH / CRITICAL."""
    t = thresholds or get_thresholds()
    if score < t.low:
        return "LOW"
    if score < t.medium:
        return "MEDIUM"
    if score < t.high:
        return "HIGH"
    return "CRITICAL"
