/** Shared AudioContext + AnalyserNode helpers for the T19 visualizer. */

export interface AnalyserHandle {
  ctx: AudioContext;
  analyser: AnalyserNode;
  dispose: () => void;
}

let sharedCtx: AudioContext | null = null;

function getSharedCtx(): AudioContext | null {
  try {
    if (!sharedCtx || sharedCtx.state === "closed") {
      const AC =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext?: typeof AudioContext })
          .webkitAudioContext;
      if (!AC) return null;
      sharedCtx = new AC();
    }
    if (sharedCtx.state === "suspended") {
      void sharedCtx.resume().catch(() => {});
    }
    return sharedCtx;
  } catch {
    return null;
  }
}

/** Tap the live mic stream. Detach when recording stops. */
export function attachMicAnalyser(stream: MediaStream): AnalyserHandle | null {
  const ctx = getSharedCtx();
  if (!ctx) return null;
  try {
    const source = ctx.createMediaStreamSource(stream);
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 64;
    analyser.smoothingTimeConstant = 0.6;
    source.connect(analyser);
    return {
      ctx,
      analyser,
      dispose: () => {
        try {
          source.disconnect(analyser);
        } catch {
          // already torn down with the stream
        }
      },
    };
  } catch {
    return null;
  }
}

/** Tap a TTS playback element. Detach on audio end. */
export function attachElementAnalyser(
  audio: HTMLAudioElement,
): AnalyserHandle | null {
  const ctx = getSharedCtx();
  if (!ctx) return null;
  try {
    const source = ctx.createMediaElementSource(audio);
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 64;
    analyser.smoothingTimeConstant = 0.6;
    source.connect(analyser);
    analyser.connect(ctx.destination);
    return {
      ctx,
      analyser,
      dispose: () => {
        try {
          source.disconnect(analyser);
          analyser.disconnect();
        } catch {
          // element already garbage-collected
        }
      },
    };
  } catch {
    return null;
  }
}

/** Normalized 0..1 levels across `bars` buckets (flat zeros when idle). */
export function readLevels(
  analyser: AnalyserNode | null,
  bars: number,
): number[] {
  const out = new Array<number>(bars).fill(0);
  if (!analyser) return out;
  try {
    const data = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(data);
    for (let i = 0; i < bars; i++) {
      const idx = Math.min(
        data.length - 1,
        Math.floor((i / bars) * data.length),
      );
      out[i] = data[idx] / 255;
    }
  } catch {
    // analyser detached mid-read; fall back to silence
  }
  return out;
}
