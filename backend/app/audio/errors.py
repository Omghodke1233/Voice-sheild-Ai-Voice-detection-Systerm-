"""Typed exceptions for the audio pipeline.

Keeping these distinct lets callers (AI modules, WebSocket handler) decide
whether a problem is recoverable (return INCONCLUSIVE) or a hard failure
(return ERROR) without string-matching messages.
"""


class AudioError(Exception):
    """Base class for all audio-processing errors."""


class UnsupportedFormatError(AudioError):
    """Raised when the incoming audio cannot be decoded (bad/unknown format)."""


class InsufficientAudioError(AudioError):
    """Raised when there is less audio than the minimum usable duration."""
