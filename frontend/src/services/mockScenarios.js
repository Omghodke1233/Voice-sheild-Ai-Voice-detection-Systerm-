// Mock WebSocket scenarios for the hackathon demo (Phase 6).
// Each scenario is a timed sequence of server->client messages matching the
// backend contract exactly (risk_update, transcript_update, risk_event,
// speaker_update, call_status). This lets the dashboard run and demo with NO
// backend or AI models present.

const t = () => new Date().toISOString();

// Scenario 1 — Genuine call: real voice, correct speaker, normal talk -> LOW
export const genuineCall = [
  { delay: 300, msg: { type: "call_status", status: "ACTIVE" } },
  { delay: 600, msg: { type: "speaker_update", status: "MATCH", similarity: 0.88 } },
  { delay: 500, msg: { type: "transcript_update", text: "Hi, just calling to confirm our meeting tomorrow at 10.", timestamp: t() } },
  {
    delay: 700,
    msg: {
      type: "risk_update", voice_suspicion: 0.08, speaker_risk: 0.05,
      social_engineering: 0.04, conversation_anomaly: 0.06,
      overall_risk: 0.07, risk_level: "LOW",
      recommended_action: "Conversation appears normal.",
    },
  },
  { delay: 900, msg: { type: "transcript_update", text: "Great, see you then. Thanks!", timestamp: t() } },
];

// Scenario 2 — Cloned voice: synthetic voice + speaker mismatch -> HIGH
export const clonedVoice = [
  { delay: 300, msg: { type: "call_status", status: "ACTIVE" } },
  { delay: 500, msg: { type: "voice_hint" } }, // no-op marker, ignored
  { delay: 500, msg: { type: "speaker_update", status: "MISMATCH", similarity: 0.29 } },
  { delay: 500, msg: { type: "transcript_update", text: "Hey, it's me. I'm using a different phone today.", timestamp: t() } },
  {
    delay: 700,
    msg: {
      type: "risk_update", voice_suspicion: 0.79, speaker_risk: 0.74,
      social_engineering: 0.12, conversation_anomaly: 0.30,
      overall_risk: 0.58, risk_level: "HIGH",
      recommended_action: "Perform secondary verification before taking action.",
    },
  },
];

// Scenario 3 — Full social engineering attack -> CRITICAL
export const fullAttack = [
  { delay: 300, msg: { type: "call_status", status: "ACTIVE" } },
  { delay: 400, msg: { type: "speaker_update", status: "MISMATCH", similarity: 0.22 } },
  { delay: 400, msg: { type: "transcript_update", text: "This is an emergency — I need you to act now.", timestamp: t() } },
  { delay: 300, msg: { type: "risk_event", category: "EMERGENCY_CLAIM", confidence: 0.94, timestamp: t(), description: "Caller claims an urgent emergency." } },
  { delay: 400, msg: { type: "transcript_update", text: "Transfer the money to this account immediately.", timestamp: t() } },
  { delay: 300, msg: { type: "risk_event", category: "FINANCIAL_REQUEST", confidence: 0.96, timestamp: t(), description: "Caller requested a financial transaction." } },
  { delay: 300, msg: { type: "risk_event", category: "URGENCY", confidence: 0.9, timestamp: t(), description: "Caller is pressuring for immediate action." } },
  { delay: 400, msg: { type: "transcript_update", text: "Don't tell anyone about this call.", timestamp: t() } },
  { delay: 300, msg: { type: "risk_event", category: "ISOLATION_TACTIC", confidence: 0.88, timestamp: t(), description: "Caller asked to keep the call secret." } },
  {
    delay: 500,
    msg: {
      type: "risk_update", voice_suspicion: 0.82, speaker_risk: 0.78,
      social_engineering: 0.91, conversation_anomaly: 0.68,
      overall_risk: 0.81, risk_level: "CRITICAL",
      recommended_action:
        "Potential impersonation attack. Do not authorize sensitive actions. Verify through a second channel.",
    },
  },
];

export const SCENARIOS = {
  genuine: { label: "Genuine Call", data: genuineCall },
  cloned: { label: "Cloned Voice", data: clonedVoice },
  attack: { label: "Full Attack", data: fullAttack },
};

// Plays a scenario by invoking onMessage over time. Returns a cancel fn.
export function playScenario(key, onMessage) {
  const scenario = SCENARIOS[key];
  if (!scenario) return () => {};
  const timers = [];
  let elapsed = 0;
  for (const step of scenario.data) {
    elapsed += step.delay;
    const id = setTimeout(() => {
      if (step.msg && step.msg.type && step.msg.type !== "voice_hint") {
        onMessage(step.msg);
      }
    }, elapsed);
    timers.push(id);
  }
  return () => timers.forEach(clearTimeout);
}
