"""
Best-effort language detection.

MVP stub: returns "en" for Latin-script text and "unknown" for empty input.
A real langid/fastText detector can replace `detect_language` later behind the
same signature. Kept intentionally simple and honest about its limits.
"""

from __future__ import annotations


def detect_language(text: str) -> str:
    if not text or not text.strip():
        return "unknown"
    # Extremely light heuristic; not a real detector.
    ascii_ratio = sum(c.isascii() for c in text) / max(len(text), 1)
    return "en" if ascii_ratio > 0.8 else "unknown"
