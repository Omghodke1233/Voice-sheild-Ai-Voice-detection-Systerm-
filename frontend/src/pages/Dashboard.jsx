// VoiceShield real-time dashboard (Phase 6).
// Runs in mock mode by default (canned scenarios, no backend). A live mode
// toggle drives a real call over REST + WebSocket against the backend.
import { useState } from "react";
import { FaShieldAlt } from "react-icons/fa";
import { useCall } from "../hooks/useCall";
import { SCENARIOS } from "../services/mockScenarios";
import { api } from "../services/api";
import CallStatus from "../components/CallStatus";
import RiskMeter from "../components/RiskMeter";
import VoiceStatus from "../components/VoiceStatus";
import SpeakerStatus from "../components/SpeakerStatus";
import Transcript from "../components/Transcript";
import RiskEvents from "../components/RiskEvents";

const DEMO_SPEAKER = { id: "speaker_001", name: "Rahul" };
const LIVE_TRANSCRIPT =
  "This is an emergency, please transfer the money now and don't tell anyone.";

export default function Dashboard() {
  const { state, startMock, startLive, startMic, reset } = useCall();
  const [mode, setMode] = useState("mock"); // "mock" | "live"
  const [customText, setCustomText] = useState(LIVE_TRANSCRIPT);

  const runMock = (key) => {
    setMode("mock");
    startMock(key);
  };

  const runLive = async () => {
    setMode("live");
    // Ensure the demo speaker exists, then start a live analyzed call.
    try {
      await api.enrollSpeaker(DEMO_SPEAKER.id, DEMO_SPEAKER.name, "rahul-seed");
    } catch {
      /* enrollment is best-effort for the demo */
    }
    startLive(DEMO_SPEAKER.id, customText.trim() || LIVE_TRANSCRIPT);
  };

  const runMic = async () => {
    setMode("mic");
    try {
      await api.enrollSpeaker(DEMO_SPEAKER.id, DEMO_SPEAKER.name, "rahul-seed");
    } catch {
      /* best-effort */
    }
    startMic(DEMO_SPEAKER.id);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Header */}
      <header className="border-b border-slate-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FaShieldAlt className="text-cyan-400 text-2xl" />
          <div>
            <h1 className="text-xl font-bold text-cyan-400 leading-tight">VoiceShield</h1>
            <p className="text-xs text-slate-500">Real-Time Conversational Deepfake Firewall</p>
          </div>
        </div>
        <CallStatus status={state.callStatus} />
      </header>

      {/* Controls */}
      <div className="px-6 py-4 flex flex-wrap items-center gap-2 border-b border-slate-800/60">
        <span className="text-xs uppercase tracking-wide text-slate-500 mr-2">Demo scenarios:</span>
        {Object.entries(SCENARIOS).map(([key, s]) => (
          <button
            key={key}
            onClick={() => runMock(key)}
            className="px-3 py-1.5 rounded-lg text-sm bg-slate-800 hover:bg-slate-700 border border-slate-700 transition"
          >
            {s.label}
          </button>
        ))}
        <button
          onClick={runLive}
          className="px-3 py-1.5 rounded-lg text-sm bg-cyan-600 hover:bg-cyan-500 border border-cyan-500 transition"
        >
          Live (backend)
        </button>
        <button
          onClick={runMic}
          className="px-3 py-1.5 rounded-lg text-sm bg-violet-600 hover:bg-violet-500 border border-violet-500 transition"
        >
          🎤 Live Mic
        </button>
        <button
          onClick={reset}
          className="px-3 py-1.5 rounded-lg text-sm bg-slate-800 hover:bg-slate-700 border border-slate-700 transition"
        >
          Reset
        </button>
        <span className="ml-auto text-xs text-slate-600">
          mode: <span className="text-slate-400">{mode}</span>
        </span>
      </div>

      {/* Custom transcript -> live backend analysis */}
      <div className="px-6 py-3 flex flex-wrap items-center gap-2 border-b border-slate-800/60">
        <span className="text-xs uppercase tracking-wide text-slate-500 mr-2">
          Analyze text:
        </span>
        <input
          type="text"
          value={customText}
          onChange={(e) => setCustomText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && runLive()}
          placeholder="Type a sentence and press Enter…"
          className="flex-1 min-w-[240px] px-3 py-1.5 rounded-lg text-sm bg-slate-900 border border-slate-700 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-cyan-500"
        />
        <button
          onClick={runLive}
          className="px-4 py-1.5 rounded-lg text-sm bg-cyan-600 hover:bg-cyan-500 border border-cyan-500 transition"
        >
          Analyze
        </button>
      </div>

      {/* Main grid */}
      <main className="p-6 grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-1">
          <RiskMeter risk={state.risk} />
        </div>
        <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <VoiceStatus risk={state.risk} />
          <SpeakerStatus speaker={state.speaker} claimedName={DEMO_SPEAKER.name} />
          <Transcript transcript={state.transcript} />
          <RiskEvents events={state.events} />
        </div>
      </main>

      <footer className="px-6 py-3 text-center text-xs text-slate-600 border-t border-slate-800">
        Risk reflects normalized evidence of a possible impersonation attack — not proof of fraud.
      </footer>
    </div>
  );
}
