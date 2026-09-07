// Header status pill showing the current call state.
const STATUS_STYLE = {
  IDLE: "bg-slate-700 text-slate-300",
  CONNECTING: "bg-sky-500/20 text-sky-300 animate-pulse",
  ACTIVE: "bg-emerald-500/20 text-emerald-300",
  ANALYZING: "bg-amber-500/20 text-amber-300 animate-pulse",
  ENDED: "bg-slate-700 text-slate-400",
  ERROR: "bg-rose-500/20 text-rose-300",
};

export default function CallStatus({ status }) {
  const style = STATUS_STYLE[status] || STATUS_STYLE.IDLE;
  return (
    <span className={`px-3 py-1 rounded-full text-xs font-semibold tracking-wide ${style}`}>
      ● {status}
    </span>
  );
}
