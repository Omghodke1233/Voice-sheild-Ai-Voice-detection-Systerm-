"""Integration: AnalysisService runs the 3 modules through risk fusion."""

import numpy as np

from app.ai.speaker_verification.enrollment import get_store
from app.services.analysis_service import AnalysisService

CONTRACT_LEN = 32_000


def _audio(seed):
    rng = np.random.default_rng(seed)
    return rng.standard_normal(CONTRACT_LEN).astype(np.float32) * 0.3


def test_service_returns_all_sections():
    svc = AnalysisService()
    out = svc.analyze_chunk(_audio(1), claimed_speaker_id=None,
                            injected_transcript="hello")
    assert set(out.keys()) == {"voice", "speaker", "nlp", "risk"}
    assert out["speaker"] is None  # no claimed speaker provided
    assert "overall_risk" in out["risk"]


def test_service_full_attack_scenario():
    # Enroll a speaker, then verify DIFFERENT audio against it (mismatch),
    # with an attack transcript. Expect HIGH or CRITICAL.
    store = get_store()
    store.enroll("victim_boss", _audio(100))

    svc = AnalysisService()
    attack_text = ("This is an emergency. Transfer the money immediately and "
                   "read me the OTP. Don't tell anyone.")
    out = svc.analyze_chunk(_audio(555), claimed_speaker_id="victim_boss",
                            injected_transcript=attack_text)

    assert out["speaker"]["status"] in {"MISMATCH", "INCONCLUSIVE"}
    assert out["nlp"]["social_engineering_probability"] >= 0.75
    assert out["risk"]["risk_level"] in {"HIGH", "CRITICAL"}
    store.clear()


def test_service_survives_module_returning_error(monkeypatch):
    svc = AnalysisService()

    class Boom:
        def analyze(self, samples):
            raise RuntimeError("boom")

    svc.voice = Boom()
    out = svc.analyze_chunk(_audio(2), injected_transcript="hi there")
    # Voice errored but the call still produced a risk assessment.
    assert out["voice"]["status"] == "ERROR"
    assert "overall_risk" in out["risk"]
