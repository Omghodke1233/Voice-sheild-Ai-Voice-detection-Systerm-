"""
Manual Phase 3+4 verification.

Runs the three demo scenarios from the brief through the full AnalysisService
(3 AI modules -> risk fusion) and prints the resulting assessment.

Run:  PYTHONPATH=. ./.venv/Scripts/python.exe scripts/risk_demo.py
"""

import numpy as np

from app.ai.speaker_verification.enrollment import get_store
from app.services.analysis_service import AnalysisService


def audio(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.standard_normal(32_000).astype(np.float32) * 0.3


def show(title: str, out: dict) -> None:
    r = out["risk"]
    print(f"\n=== {title} ===")
    if out["voice"]:
        print(f"  voice     : {out['voice']['status']:12} "
              f"synthetic_prob={out['voice'].get('synthetic_probability')}")
    if out["speaker"]:
        print(f"  speaker   : {out['speaker']['status']:12} "
              f"similarity={out['speaker'].get('similarity')}")
    if out["nlp"]:
        ev = ", ".join(e["type"] for e in out["nlp"].get("events", []))
        print(f"  nlp       : SE_prob={out['nlp']['social_engineering_probability']} "
              f"events=[{ev}]")
    print(f"  --> overall_risk={r['overall_risk']}  LEVEL={r['risk_level']}")
    print(f"      action: {r['recommended_action']}")


def main() -> None:
    store = get_store()
    svc = AnalysisService()

    # Enroll a reference speaker. The "genuine" scenario re-uses this exact
    # audio (match); attack scenarios use different audio (mismatch).
    genuine_audio = audio(100)
    store.enroll("boss", genuine_audio)

    # Scenario 1 — genuine call.
    show("Scenario 1: Genuine call", svc.analyze_chunk(
        genuine_audio.copy(), claimed_speaker_id="boss",
        injected_transcript="Hi, are we still on for the review tomorrow?"))

    # Scenario 2 — cloned voice, speaker mismatch, normal conversation.
    show("Scenario 2: Cloned voice", svc.analyze_chunk(
        audio(777), claimed_speaker_id="boss",
        injected_transcript="Just checking in about the project status."))

    # Scenario 3 — full social-engineering attack.
    show("Scenario 3: Full attack", svc.analyze_chunk(
        audio(888), claimed_speaker_id="boss",
        injected_transcript=(
            "This is an emergency, I need you to transfer money immediately. "
            "Don't tell anyone and read me the OTP right now.")))

    store.clear()


if __name__ == "__main__":
    main()
