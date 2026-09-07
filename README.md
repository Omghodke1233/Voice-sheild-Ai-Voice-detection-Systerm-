# VoiceShield — Real-Time Conversational Deepfake Firewall

> A familiar voice is no longer treated as proof of identity.

VoiceShield is a security layer for the voice channel. It combines voice
authenticity analysis, speaker verification, and conversational threat
detection to identify potential voice-impersonation attacks in real time and
trigger appropriate verification actions.

**Core flow:** DETECT → VERIFY → UNDERSTAND → ASSESS RISK → WARN → PREVENT

---

## Status

**Phase 1 — Foundation** is complete. The backend boots, the database
connects, the health endpoint works, and the frontend renders and reports
backend connectivity.

**Phase 2 — Audio Pipeline** is complete. Incoming audio is decoded, downmixed
to mono, resampled to 16 kHz, normalized to float32 `[-1, 1]`, and split into
overlapping 2-second chunks — the internal contract every AI module consumes.

**Phase 3 — AI Modules** is complete (mock-first, behind stable interfaces):
voice deepfake detection, speaker verification, and ASR + conversational
analysis. Each returns the documented JSON contract, handles failure
(ERROR/INCONCLUSIVE), and reports processing time.

**Phase 4 — Risk Engine** is complete. Weighted fusion
(0.35 voice / 0.30 speaker / 0.25 social-engineering / 0.10 conversation
anomaly) with automatic renormalization when a module is missing or
inconclusive, banding into LOW/MEDIUM/HIGH/CRITICAL, and a recommended action.

**Phase 5 — Backend + WebSocket** is complete. REST endpoints for speakers and
calls, plus `WS /ws/calls/{call_id}` streaming risk_update / transcript_update /
risk_event / speaker_update / call_status messages.

**Phase 6 — Frontend** is complete. A real-time React dashboard (RiskMeter,
VoiceStatus, SpeakerStatus, Transcript, RiskEvents) runs mock-first with three
demo scenarios, plus a live backend mode.

**Phase 7 — Integration** is complete. Live microphone capture downsamples to
the 16 kHz PCM contract in the browser and streams binary frames through the
real voice + speaker pipeline over WebSocket.

**Phase 8 — Final Testing** is complete. 69 tests pass, including the three
demo scenarios, failure/disconnect handling, missing-speaker resilience, and a
12-consecutive-call soak test. Measured pipeline latency (mock modules)
averages under 1 ms per 2-second chunk — within the 3 s target; real ML models
will add inference time.

### Demo scenarios
- **Genuine Call** -> LOW · **Cloned Voice** -> HIGH · **Full Attack** -> CRITICAL
- **Live (backend)** — real REST + WebSocket call · **🎤 Live Mic** — real audio
  through voice + speaker analysis

### Honest limitations
- AI modules are deterministic mocks behind real interfaces; no accuracy is
  claimed. Real anti-spoofing, speaker-embedding, and Whisper ASR models are
  the documented next upgrade.
- The risk score is normalized evidence of a *possible* impersonation attack,
  not proof of fraud.
- Live-mic ASR is not yet wired: voice + speaker analysis run on real audio;
  NLP/social-engineering events come from the injected-transcript path.

---

## Architecture (target)

```
AI modules  ->  Standardized contracts  ->  Risk engine
            ->  Backend service  ->  WebSocket  ->  Frontend
```

Three parallel AI modules (deepfake detection, speaker verification, ASR+NLP)
feed a risk-fusion engine, which produces an overall risk score
(LOW / MEDIUM / HIGH / CRITICAL) streamed to a React dashboard.

---

## Technology stack

| Layer     | Tech                                             |
| --------- | ------------------------------------------------ |
| Frontend  | React, Vite, JavaScript, Tailwind CSS, WebSocket |
| Backend   | Python, FastAPI, WebSocket, SQLAlchemy, Pydantic |
| AI/ML     | PyTorch, Transformers, Whisper, Librosa (Phase 3)|
| Database  | SQLite (local dev) / PostgreSQL (prod, Docker)   |
| Packaging | Docker, Docker Compose                           |

### Python version note

Detected Python on this machine is **3.14**. FastAPI and the Phase 1 stack run
fine on it. However, ML wheels (PyTorch, faster-whisper, librosa) frequently
lag new Python releases. For Phase 3 we recommend a dedicated **Python 3.11 or
3.12** virtual environment for the backend. The Docker image already pins
`python:3.12-slim`.

---

## Prerequisites

- Python 3.11–3.12 recommended (3.14 works for Phase 1). On Windows use the
  `py` launcher.
- Node.js 18+ (detected: v24) and npm.
- PostgreSQL only if you opt out of the default SQLite (Docker provides it).

---

## Setup & running

### 1. Environment file

```bash
cp .env.example .env
```

The defaults use SQLite, so no database install is required to start.

### 2. Backend

```bash
cd backend
py -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash
# .venv\Scripts\activate        # Windows PowerShell/CMD
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Verify:

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok","app":"VoiceShield","version":"0.1.0"}`

Interactive API docs: http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — the page should show the backend status as
online.

### 4. PostgreSQL via Docker (optional)

```bash
docker compose up db
```

Then set `DATABASE_URL` in `.env` to the PostgreSQL URL shown in
`.env.example`.

---

## Testing

```bash
cd backend
pytest
```

Phase 1 ships a health-endpoint smoke test. Each module adds its own tests in
later phases.

---

## Project structure

```
VoiceShield/
├── backend/          FastAPI app, AI modules, risk engine, tests
│   └── app/
│       ├── api/          REST routers (Phase 5)
│       ├── websocket/    WS endpoints (Phase 5)
│       ├── services/     call & analysis orchestration
│       ├── audio/         preprocessing pipeline (contract, chunking)
│       ├── ai/           voice_detector | speaker_verification | nlp
│       ├── risk/         fusion engine
│       ├── database/     engine + session
│       ├── models/       ORM models
│       ├── schemas/      Pydantic schemas
│       └── main.py       app entry point + /health
├── frontend/         React + Vite + Tailwind dashboard
├── models/           trained model artifacts (gitignored)
├── data/             sample & test audio (gitignored)
├── docs/             documentation
├── docker-compose.yml
└── .env.example
```

---

## API & WebSocket documentation

Placeholders — populated in Phase 5. REST endpoints under `/api/v1/...` and a
WebSocket at `/ws/calls/{call_id}`.

---

## Demo scenarios

Planned (Phase 8): genuine call (LOW), cloned voice (HIGH), and full social-
engineering attack (CRITICAL). See `docs/` as phases progress.

---

## Privacy considerations

- Minimal raw-audio retention (disabled by default).
- Speaker table stores an embedding *reference*, not raw voice.
- Secrets via environment variables only; `.env` is gitignored.
- Structured logs exclude raw audio, secrets, and unnecessary PII.

This is privacy-by-design intent, **not** a claim of legal compliance.

---

## Limitations

- Risk score is normalized evidence of a *possible* impersonation attack — not
  proof of fraud, not legal evidence, not a probability that someone is a
  criminal.
- No accuracy numbers are claimed until real models are trained and evaluated.

---

## Future scope

Indian languages & accents, telecom/banking integration, edge inference,
continuous speaker verification, SIEM integration, and privacy-preserving
learning. See the project brief for the full list.
