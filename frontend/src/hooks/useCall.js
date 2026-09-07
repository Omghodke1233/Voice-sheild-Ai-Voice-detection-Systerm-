// useCall — central state for a live/mock call. Consumes the WebSocket event
// contract and exposes a single `state` object the dashboard renders from.
import { useCallback, useRef, useState } from "react";
import { playScenario } from "../services/mockScenarios";
import { api } from "../services/api";
import { connectCall } from "../services/websocket";
import { startMicCapture } from "../services/micCapture";

const EMPTY = {
  callStatus: "IDLE", // IDLE | CONNECTING | ACTIVE | ANALYZING | ENDED | ERROR
  risk: null, // { overall_risk, risk_level, voice_suspicion, ... }
  speaker: null, // { status, similarity }
  transcript: [], // [{ text, timestamp }]
  events: [], // [{ category, confidence, timestamp, description }]
};

export function useCall() {
  const [state, setState] = useState(EMPTY);
  const cancelRef = useRef(null);
  const wsRef = useRef(null);
  const stopMicRef = useRef(null);

  const handleMessage = useCallback((msg) => {
    setState((prev) => {
      switch (msg.type) {
        case "call_status":
          return { ...prev, callStatus: msg.status };
        case "risk_update":
          return { ...prev, risk: msg };
        case "speaker_update":
          return { ...prev, speaker: { status: msg.status, similarity: msg.similarity } };
        case "transcript_update":
          return { ...prev, transcript: [...prev.transcript, { text: msg.text, timestamp: msg.timestamp }] };
        case "risk_event":
          return { ...prev, events: [...prev.events, msg] };
        default:
          return prev;
      }
    });
  }, []);

  const reset = useCallback(() => {
    if (cancelRef.current) cancelRef.current();
    if (stopMicRef.current) stopMicRef.current();
    if (wsRef.current) wsRef.current.close();
    cancelRef.current = null;
    stopMicRef.current = null;
    wsRef.current = null;
    setState(EMPTY);
  }, []);

  // Mock mode: play a canned scenario with no backend.
  const startMock = useCallback(
    (scenarioKey) => {
      reset();
      setState({ ...EMPTY, callStatus: "CONNECTING" });
      cancelRef.current = playScenario(scenarioKey, handleMessage);
    },
    [handleMessage, reset]
  );

  // Live mode: start a real call over REST + WebSocket, then inject a
  // transcript so the mock AI produces a real fused risk result.
  const startLive = useCallback(
    async (claimedSpeakerId, transcript) => {
      reset();
      setState({ ...EMPTY, callStatus: "CONNECTING" });
      try {
        const { call_id } = await api.startCall(claimedSpeakerId || null);
        const conn = connectCall(call_id, {
          onMessage: handleMessage,
          onOpen: () => transcript && conn.sendAnalyze(transcript),
          onError: () => setState((p) => ({ ...p, callStatus: "ERROR" })),
        });
        wsRef.current = conn;
      } catch (e) {
        setState((p) => ({ ...p, callStatus: "ERROR" }));
      }
    },
    [handleMessage, reset]
  );

  // Live mic mode: real microphone -> 16kHz PCM -> WebSocket -> real pipeline.
  const startMic = useCallback(
    async (claimedSpeakerId) => {
      reset();
      setState({ ...EMPTY, callStatus: "CONNECTING" });
      try {
        const { call_id } = await api.startCall(claimedSpeakerId || null);
        const conn = connectCall(call_id, {
          onMessage: handleMessage,
          onError: () => setState((p) => ({ ...p, callStatus: "ERROR" })),
          onClose: () => {
            if (stopMicRef.current) stopMicRef.current();
          },
        });
        wsRef.current = conn;

        stopMicRef.current = await startMicCapture({
          chunkSeconds: 2,
          onFrame: (int16) => conn.isOpen() && conn.sendBytes(int16),
          onError: () => setState((p) => ({ ...p, callStatus: "ERROR" })),
        });
      } catch {
        setState((p) => ({ ...p, callStatus: "ERROR" }));
      }
    },
    [handleMessage, reset]
  );

  return { state, startMock, startLive, startMic, reset };
}
