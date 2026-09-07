"""
Social-engineering signal detection.

Explainable, rule-based keyword/phrase matching over a transcript. Per project
rules we do NOT dress this up as advanced AI — it is transparent pattern
matching that a transformer classifier can later augment or replace.

Signals detected (per brief):
    financial_request, emergency_claim, urgency, credential_request,
    otp_request, isolation_tactic, secret_request, payment_request,
    identity_claim
"""

from __future__ import annotations

import re

# Each signal maps to a list of lowercase phrase patterns.
SIGNAL_PATTERNS: dict[str, list[str]] = {
    "financial_request": [
        "send money", "transfer", "wire", "bank account", "pay ", "payment",
        "deposit", "funds", "gift card",
    ],
    "payment_request": [
        "make a payment", "pay now", "settle the", "clear the dues",
        "upi", "credit card number",
    ],
    "emergency_claim": [
        "emergency", "accident", "hospital", "in trouble", "arrested",
        "urgent help", "life or death",
    ],
    "urgency": [
        "immediately", "right now", "as soon as possible", "asap",
        "hurry", "no time", "before it's too late", "quickly",
    ],
    "credential_request": [
        "password", "pin", "login", "username", "credentials",
        "security question",
    ],
    "otp_request": [
        "otp", "one time password", "verification code", "code i sent",
        "read me the code", "sms code",
    ],
    "isolation_tactic": [
        "don't tell anyone", "keep this between us", "don't call anyone",
        "stay on the line", "don't hang up", "don't talk to",
    ],
    "secret_request": [
        "secret", "confidential", "private matter", "just between us",
    ],
    "identity_claim": [
        "this is your", "i am the", "it's me", "your ceo", "your manager",
        "from the bank", "calling from", "officer",
    ],
}


def detect_signals(transcript: str) -> dict[str, bool]:
    """Return a bool per known signal indicating presence in the transcript."""
    text = (transcript or "").lower()
    results: dict[str, bool] = {}
    for signal, patterns in SIGNAL_PATTERNS.items():
        results[signal] = any(_matches(text, p) for p in patterns)
    return results


def _matches(text: str, pattern: str) -> bool:
    """Substring match, but word-boundary aware for short alpha tokens.

    Short tokens like "pin" or "otp" use word boundaries to avoid false hits
    inside words (e.g. "pin" in "shipping"). Multi-word phrases use plain
    substring matching.
    """
    if " " not in pattern and pattern.isalpha() and len(pattern) <= 4:
        return re.search(rf"\b{re.escape(pattern)}\b", text) is not None
    return pattern in text
