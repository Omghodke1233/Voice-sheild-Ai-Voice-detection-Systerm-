// Thin WebSocket wrapper for a live call. Emits parsed JSON messages to a
// callback and exposes send/close. Used in "live" mode; mock mode uses
// mockScenarios.js instead.
const WS_BASE = import.meta.env.VITE_WS_BASE || "ws://localhost:8000";

export function connectCall(callId, { onMessage, onOpen, onClose, onError }) {
  const ws = new WebSocket(`${WS_BASE}/ws/calls/${callId}`);

  ws.onopen = () => onOpen && onOpen();
  ws.onclose = () => onClose && onClose();
  ws.onerror = (e) => onError && onError(e);
  ws.onmessage = (evt) => {
    try {
      onMessage(JSON.parse(evt.data));
    } catch {
      // Ignore non-JSON frames.
    }
  };

  return {
    // Send a control/analyze message (mock injection or 'end').
    sendAnalyze: (transcript) =>
      ws.readyState === WebSocket.OPEN &&
      ws.send(JSON.stringify({ action: "analyze", transcript })),
    // Send raw Int16 PCM audio as a binary frame (live mic, Phase 7).
    sendBytes: (int16) =>
      ws.readyState === WebSocket.OPEN && ws.send(int16.buffer),
    isOpen: () => ws.readyState === WebSocket.OPEN,
    end: () =>
      ws.readyState === WebSocket.OPEN &&
      ws.send(JSON.stringify({ action: "end" })),
    close: () => ws.close(),
    raw: ws,
  };
}
