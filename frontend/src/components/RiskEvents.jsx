// Detected social-engineering events + a simple time-ordered timeline.
import { FaExclamationTriangle } from "react-icons/fa";
import { pct } from "./riskStyles";

const LABELS = {
  FINANCIAL_REQUEST: "Financial Request",
  EMERGENCY_CLAIM: "Emergency Claim",
  URGENCY: "Urgency",
  CREDENTIAL_REQUEST: "Credential Request",
  OTP_REQUEST: "OTP Request",
  ISOLATION_TACTIC: "Isolation Tactic",
  SECRET_REQUEST: "Secret Request",
  PAYMENT_REQUEST: "Payment Request",
  IDENTITY_CLAIM: "Identity Claim",
};

const fmtTime = (ts) => {
  try {
    return new Date(ts).toLocaleTimeString();
  } catch {
    return "";
  }
};

export default function RiskEvents({ events }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4 flex flex-col h-64">
      <div className="flex items-center gap-2 text-slate-400 text-sm mb-3">
        <FaExclamationTriangle /> Conversation Analysis
      </div>
      <div className="flex-1 overflow-y-auto space-y-2 pr-1">
        {events.length === 0 && (
          <div className="text-slate-600 text-sm italic">No suspicious events detected.</div>
        )}
        {events.map((e, i) => (
          <div key={i} className="flex items-start gap-2 text-sm border-l-2 border-rose-500/60 bg-rose-500/5 rounded px-3 py-2">
            <span className="text-rose-400 mt-0.5">⚠️</span>
            <div className="flex-1">
              <div className="text-slate-200 font-medium">
                {LABELS[e.category] || e.category}
              </div>
              {e.description && (
                <div className="text-slate-400 text-xs">{e.description}</div>
              )}
              <div className="text-slate-600 text-xs mt-0.5">
                {fmtTime(e.timestamp)} · confidence {pct(e.confidence)}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
