"""Recommended actions per risk level.

The wording deliberately avoids claims of certainty (project rule): the score
is normalized evidence of a POSSIBLE impersonation attack, not proof.
"""

from __future__ import annotations

_ACTIONS: dict[str, str] = {
    "LOW": "Conversation appears normal.",
    "MEDIUM": "Verify caller identity before continuing.",
    "HIGH": "Perform secondary verification before taking action.",
    "CRITICAL": (
        "Potential impersonation attack. Do not authorize sensitive actions. "
        "Verify through a second channel."
    ),
}


def action_for_level(risk_level: str) -> str:
    return _ACTIONS.get(risk_level, _ACTIONS["MEDIUM"])
