// Shared risk-level -> color/label mapping so every component agrees.
export const RISK_STYLES = {
  LOW: { text: "text-emerald-400", bg: "bg-emerald-500", ring: "ring-emerald-500/40", border: "border-emerald-500/40" },
  MEDIUM: { text: "text-amber-400", bg: "bg-amber-500", ring: "ring-amber-500/40", border: "border-amber-500/40" },
  HIGH: { text: "text-orange-400", bg: "bg-orange-500", ring: "ring-orange-500/40", border: "border-orange-500/40" },
  CRITICAL: { text: "text-rose-400", bg: "bg-rose-500", ring: "ring-rose-500/40", border: "border-rose-500/40" },
};

export const riskStyle = (level) => RISK_STYLES[level] || {
  text: "text-slate-400", bg: "bg-slate-600", ring: "ring-slate-600/40", border: "border-slate-700",
};

export const pct = (v) => (v == null ? "—" : `${Math.round(v * 100)}%`);
