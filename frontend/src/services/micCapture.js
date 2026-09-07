// Microphone capture -> 16 kHz mono Int16 PCM frames (Phase 7).
//
// Browsers capture audio at the hardware rate (usually 44.1 or 48 kHz) as
// Float32. The backend audio contract is 16 kHz mono 16-bit PCM, so we
// downsample and convert client-side before sending binary WebSocket frames.
//
// Uses a ScriptProcessorNode: deprecated but universally supported and by far
// the simplest reliable option for an MVP (AudioWorklet needs a separate module
// file and more setup). Swap to AudioWorklet later if needed.

const TARGET_RATE = 16000;

// Downsample a Float32 buffer from srcRate to 16 kHz by simple averaging.
function downsampleTo16k(input, srcRate) {
  if (srcRate === TARGET_RATE) return input;
  const ratio = srcRate / TARGET_RATE;
  const outLength = Math.floor(input.length / ratio);
  const out = new Float32Array(outLength);
  let pos = 0;
  for (let i = 0; i < outLength; i++) {
    const start = Math.floor(i * ratio);
    const end = Math.floor((i + 1) * ratio);
    let sum = 0;
    let count = 0;
    for (let j = start; j < end && j < input.length; j++) {
      sum += input[j];
      count++;
    }
    out[pos++] = count > 0 ? sum / count : 0;
  }
  return out;
}

// Convert Float32 [-1,1] to Int16 PCM.
function floatToInt16(float32) {
  const out = new Int16Array(float32.length);
  for (let i = 0; i < float32.length; i++) {
    const s = Math.max(-1, Math.min(1, float32[i]));
    out[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return out;
}

// Starts mic capture. Calls onFrame(Int16Array) with ~batches of 16k samples.
// Returns a stop() function that releases the mic and audio graph.
export async function startMicCapture({ onFrame, onError, chunkSeconds = 2 }) {
  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (e) {
    onError && onError(e);
    return () => {};
  }

  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  const ctx = new AudioCtx();
  const source = ctx.createMediaStreamSource(stream);
  const processor = ctx.createScriptProcessor(4096, 1, 1);

  // Accumulate downsampled samples until we have chunkSeconds worth, then emit.
  const frameSize = TARGET_RATE * chunkSeconds;
  let buffer = new Float32Array(0);

  processor.onaudioprocess = (e) => {
    const input = e.inputBuffer.getChannelData(0);
    const down = downsampleTo16k(input, ctx.sampleRate);

    const merged = new Float32Array(buffer.length + down.length);
    merged.set(buffer);
    merged.set(down, buffer.length);
    buffer = merged;

    while (buffer.length >= frameSize) {
      const frame = buffer.slice(0, frameSize);
      buffer = buffer.slice(frameSize);
      onFrame(floatToInt16(frame));
    }
  };

  source.connect(processor);
  processor.connect(ctx.destination);

  return function stop() {
    try {
      processor.disconnect();
      source.disconnect();
      stream.getTracks().forEach((t) => t.stop());
      ctx.close();
    } catch {
      /* best-effort cleanup */
    }
  };
}
