"""
Phase 8 latency benchmark.

Measures real per-stage and total latency of the analysis pipeline over many
synthetic 2-second chunks. Reports min/mean/median/p95/max in milliseconds.
Does NOT fabricate accuracy — this measures wall-clock latency only.

Run:  PYTHONPATH=. ./.venv/Scripts/python.exe scripts/latency_bench.py
"""

from __future__ import annotations

import statistics
import time

import numpy as np

from app.services.analysis_service import AnalysisService

CHUNK_SAMPLES = 32_000  # 2s @ 16kHz
N_RUNS = 50


def summarize(name: str, values: list[float]) -> None:
    values_sorted = sorted(values)
    p95 = values_sorted[int(len(values_sorted) * 0.95) - 1]
    print(
        f"{name:<22} "
        f"min={min(values):7.2f}  mean={statistics.mean(values):7.2f}  "
        f"median={statistics.median(values):7.2f}  p95={p95:7.2f}  "
        f"max={max(values):7.2f}   (ms)"
    )


def main() -> None:
    service = AnalysisService()
    rng = np.random.default_rng(42)

    transcripts = [
        None,
        "Hi, confirming our meeting tomorrow.",
        "This is an emergency, transfer the money now and tell no one.",
    ]

    totals: list[float] = []
    voice_times: list[float] = []
    speaker_times: list[float] = []
    nlp_times: list[float] = []

    print(f"Running {N_RUNS} analysis cycles on 2s chunks...\n")

    for i in range(N_RUNS):
        samples = (rng.standard_normal(CHUNK_SAMPLES) * 6000).astype(np.int16)
        samples = samples.astype(np.float32) / 32768.0
        transcript = transcripts[i % len(transcripts)]

        start = time.perf_counter()
        result = service.analyze_chunk(
            samples, claimed_speaker_id="speaker_001",
            injected_transcript=transcript,
        )
        total_ms = (time.perf_counter() - start) * 1000
        totals.append(total_ms)

        # Per-module self-reported processing times.
        if result.get("voice"):
            voice_times.append(result["voice"].get("processing_time_ms", 0))
        if result.get("speaker"):
            speaker_times.append(result["speaker"].get("processing_time_ms", 0))
        if result.get("nlp"):
            nlp_times.append(result["nlp"].get("processing_time_ms", 0))

    print("Per-module (self-reported):")
    summarize("  voice_detector", voice_times)
    summarize("  speaker_verify", speaker_times)
    summarize("  nlp_analysis", nlp_times)
    print("\nEnd-to-end analyze_chunk:")
    summarize("  TOTAL", totals)

    mean_total = statistics.mean(totals)
    target_ms = 3000
    print(
        f"\nTarget: analysis < {target_ms} ms per chunk.  "
        f"Result: mean {mean_total:.1f} ms -> "
        f"{'PASS' if mean_total < target_ms else 'REVIEW'}"
    )
    print(
        "Note: mock modules; real ML models will add inference time. "
        "This measures pipeline overhead, not model accuracy."
    )


if __name__ == "__main__":
    main()
