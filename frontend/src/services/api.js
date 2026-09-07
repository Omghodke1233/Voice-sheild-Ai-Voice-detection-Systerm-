// REST client for the VoiceShield backend.
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

async function req(path, options) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const api = {
  base: API_BASE,
  health: () => req("/health"),
  enrollSpeaker: (speaker_id, name, enrollment_seed) =>
    req("/api/v1/speakers/enroll", {
      method: "POST",
      body: JSON.stringify({ speaker_id, name, enrollment_seed }),
    }),
  startCall: (claimed_speaker_id) =>
    req("/api/v1/calls/start", {
      method: "POST",
      body: JSON.stringify({ claimed_speaker_id }),
    }),
  endCall: (call_id) =>
    req(`/api/v1/calls/${call_id}/end`, { method: "POST" }),
  getEvents: (call_id) => req(`/api/v1/calls/${call_id}/events`),
};
