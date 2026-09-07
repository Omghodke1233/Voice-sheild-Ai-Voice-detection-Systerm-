"""Configuration and thresholds for speaker verification."""

from dataclasses import dataclass

from app.config import get_settings


@dataclass(frozen=True)
class SpeakerConfig:
    # Cosine similarity at/above this => MATCH. This is a SIMILARITY threshold,
    # NOT a probability. Documented and configurable per project rules.
    match_threshold: float = 0.5
    # Band below match_threshold within which we report INCONCLUSIVE rather
    # than a hard MISMATCH (avoids overconfident rejection near the boundary).
    inconclusive_margin: float = 0.1
    # Dimensionality of the mock embedding vector.
    embedding_dim: int = 128


def get_config() -> SpeakerConfig:
    s = get_settings()
    return SpeakerConfig(match_threshold=s.speaker_threshold)
