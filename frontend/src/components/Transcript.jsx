// Live streaming transcript.
import { useEffect, useRef } from "react";
import { FaRegCommentDots } from "react-icons/fa";

export default function Transcript({ transcript }) {
  const endRef = useRef(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcript]);

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4 flex flex-col h-64">
      <div className="flex items-center gap-2 text-slate-400 text-sm mb-3">
        <FaRegCommentDots /> Live Transcript
      </div>
      <div className="flex-1 overflow-y-auto space-y-2 pr-1">
        {transcript.length === 0 && (
          <div className="text-slate-600 text-sm italic">Waiting for speech…</div>
        )}
        {transcript.map((line, i) => (
          <div key={i} className="text-sm text-slate-200 bg-slate-800/50 rounded px-3 py-2">
            {line.text}
          </div>
        ))}
        <div ref={endRef} />
      </div>
    </div>
  );
}
