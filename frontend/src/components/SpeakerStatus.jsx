// Speaker verification panel.
import { FaUserShield } from "react-icons/fa";
import { pct } from "./riskStyles";

const STATUS_COLOR = {
  MATCH: "text-emerald-400",
  MISMATCH: "text-rose-400",
  INCONCLUSIVE: "text-amber-400",
  ERROR: "text-slate-400",
};

export default function SpeakerStatus({ speaker, claimedName }) {
  const status = speaker?.status || "—";
  const color = STATUS_COLOR[status] || "text-slate-400";

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
      <div className="flex items-center gap-2 text-slate-400 text-sm mb-3">
        <FaUserShield /> Speaker Verification
      </div>
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <div className="text-slate-500">Claimed Speaker</div>
          <div className="text-slate-200 font-medium">{claimedName || "—"}</div>
        </div>
        <div>
          <div className="text-slate-500">Status</div>
          <div className={`font-bold ${color}`}>{status}</div>
        </div>
        <div className="col-span-2">
          <div className="text-slate-500">Voice Similarity</div>
          <div className="text-slate-200 font-mono">{pct(speaker?.similarity)}</div>
          <div className="mt-2 h-2 rounded bg-slate-800 overflow-hidden">
            <div
              className="h-full bg-cyan-500"
              style={{ width: speaker?.similarity != null ? `${speaker.similarity * 100}%` : "0%" }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
