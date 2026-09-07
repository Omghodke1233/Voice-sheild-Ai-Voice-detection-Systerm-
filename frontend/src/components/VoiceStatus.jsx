// Voice authenticity panel (derived from risk.voice_suspicion).
import { FaMicrophoneAlt } from "react-icons/fa";
import { pct } from "./riskStyles";

export default function VoiceStatus({ risk }) {
  const v = risk?.voice_suspicion ?? null;
  const suspicious = v != null && v >= 0.5;
  const label = v == null ? "—" : suspicious ? "SUSPICIOUS" : "NORMAL";
  const color = v == null ? "text-slate-400" : suspicious ? "text-rose-400" : "text-emerald-400";

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
      <div className="flex items-center gap-2 text-slate-400 text-sm mb-3">
        <FaMicrophoneAlt /> Voice Authenticity
      </div>
      <div className={`text-2xl font-bold ${color}`}>{label}</div>
      <div className="mt-3 h-2 rounded bg-slate-800 overflow-hidden">
        <div
          className={`h-full ${suspicious ? "bg-rose-500" : "bg-emerald-500"}`}
          style={{ width: v != null ? `${v * 100}%` : "0%" }}
        />
      </div>
      <div className="mt-1 text-xs text-slate-500">
        Synthetic likelihood: {pct(v)}
      </div>
    </div>
  );
}
