"""
Manual Phase 2 verification.

Generates a synthetic stereo 44.1 kHz WAV in memory, runs it through the
audio pipeline, and prints the resulting chunk report so you can eyeball that
the contract (16 kHz, mono, float32, 2s chunks) is satisfied.

Run:  ./.venv/Scripts/python.exe scripts/audio_demo.py
"""

import io
import wave

import numpy as np

from app.audio.contract import get_contract
from app.audio.processor import process_wav_bytes


def make_stereo_wav(seconds: float, rate: int) -> bytes:
    n = int(seconds * rate)
    t = np.linspace(0, seconds, n, endpoint=False)
    left = (np.sin(2 * np.pi * 220 * t) * 12000).astype(np.int16)
    right = (np.sin(2 * np.pi * 330 * t) * 12000).astype(np.int16)
    interleaved = np.empty(left.size + right.size, dtype=np.int16)
    interleaved[0::2] = left
    interleaved[1::2] = right

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(interleaved.tobytes())
    return buf.getvalue()


def main() -> None:
    contract = get_contract()
    wav_bytes = make_stereo_wav(seconds=4.0, rate=44_100)
    print(f"Input: 4.0s stereo @ 44100 Hz  ({len(wav_bytes)} bytes)")

    chunks = process_wav_bytes(wav_bytes, contract)

    print(f"Contract: {contract.sample_rate} Hz, mono, "
          f"{contract.chunk_seconds}s chunk, {contract.overlap_seconds}s overlap")
    print(f"Produced {len(chunks)} chunk(s):")
    for c in chunks:
        peak = float(np.max(np.abs(c.samples)))
        print(
            f"  #{c.index}  start={c.start_sample:>6}  "
            f"len={len(c.samples)}  dur={c.duration_seconds:.2f}s  "
            f"rate={c.sample_rate}  peak={peak:.3f}"
        )

    # Sanity assertions mirroring the success criteria.
    assert all(c.sample_rate == 16_000 for c in chunks)
    assert all(c.samples.ndim == 1 for c in chunks)
    assert all(len(c.samples) == contract.chunk_samples for c in chunks)
    print("\nOK: sample_rate=16000, channels=1, chunks uniform length.")


if __name__ == "__main__":
    main()
