// Large central impersonation-risk indicator.
import { riskStyle } from "./riskStyles";

const ARC_COLOR = {
  LOW: "#10b981", MEDIUM: "#f59e0b", HIGH: "#f97316", CRITICAL: "#f43f5e",
};

export default function RiskMeter({ risk }) {
  const level = risk?.risk_level || "—";
  const score = risk?.overall_risk ?? null;
  const s = riskStyle(risk?.risk_level);
  const deg = score != null ? Math.round(score * 360) : 0;
  const arc = ARC_COLOR[risk?.risk_level] || "#475569";

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900 p-6 flex flex-col items-center">
      <div className="text-xs uppercase tracking-widest text-slate-500 mb-4">
        Impersonation Risk
      </div>

      <div
        className="relative h-44 w-44 rounded-full flex items-center justify-center"
        style={{
          background:
            score != null
              ? `conic-gradient(${arc} ${deg}deg, rgb(30 41 59) ${deg}deg)`
              : "rgb(30 41 59)",
        }}
      >
        <div className={`absolute inset-2 rounded-full bg-slate-950 ring-4 ${s.ring}`} />
        <div className="relative text-center">
          <div className={`text-5xl font-bold ${s.text}`}>
            {score != null ? Math.round(score * 100) : "—"}
            {score != null && <span className="text-2xl">%</span>}
          </div>
          <div className={`mt-1 text-sm font-semibold tracking-wide ${s.text}`}>
            {level}
          </div>
        </div>
      </div>

      {risk?.recommended_action && (
        <div className={`mt-5 text-center text-sm rounded-lg border ${s.border} px-4 py-3 ${s.text}`}>
          {risk.recommended_action}
        </div>
      )}
    </div>
  );
}
