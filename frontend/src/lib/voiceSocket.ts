import type { VoiceServerFrame } from "../types/api";
import { wsUrl } from "./config";

export type VoiceEvent =
  | { kind: "ready"; silenceThreshold: number }
  | { kind: "answer"; transcript: string }
  | { kind: "question"; text: string; finished: boolean }
  | { kind: "audio"; dataB64: string }
  | { kind: "done" }
  | { kind: "error"; detail: string };

function toEvent(frame: VoiceServerFrame): VoiceEvent | null {
  switch (frame.type) {
    case "ready":
      return { kind: "ready", silenceThreshold: frame.silence_threshold_seconds };
    case "answer":
      return { kind: "answer", transcript: frame.transcript };
    case "question":
      return { kind: "question", text: frame.text, finished: frame.finished };
    case "audio":
      return { kind: "audio", dataB64: frame.data_b64 };
    case "done":
      return { kind: "done" };
    case "error":
      return { kind: "error", detail: frame.detail };
    default:
      return null;
  }
}

/** Pick a MediaRecorder mimeType that actually works in this browser. */
export function pickAudioMimeType(): string | undefined {
  if (typeof MediaRecorder === "undefined") return undefined;
  const candidates = ["audio/webm", "audio/mp4", "audio/ogg"];
  for (const t of candidates) {
    try {
      if (MediaRecorder.isTypeSupported(t)) return t;
    } catch {
      continue;
    }
  }
  return undefined; // let the browser choose its default
}

export function speakBrowserFallback(text: string): void {
  if (!("speechSynthesis" in window) || !text) return;
  try {
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.rate = 1.0;
    window.speechSynthesis.speak(u);
  } catch {
    // no-op: fallback is best-effort only
  }
}

export interface VoiceSocket {
  sendAudio(chunk: Blob): void;
  sendEndOfTurn(): void;
  close(): void;
  readonly open: boolean;
}

export function connectVoiceSocket(
  sessionId: number,
  onEvent: (ev: VoiceEvent) => void,
  onClose?: () => void,
): Promise<WebSocket> {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl(`/session/${sessionId}/voice`));
    const fail = (e: Event) => {
      ws.removeEventListener("open", ok);
      reject(e instanceof Error ? e : new Error("Voice socket failed to open"));
    };
    const ok = () => {
      ws.removeEventListener("error", fail);
      resolve(ws);
    };
    ws.addEventListener("error", fail, { once: true });
    ws.addEventListener("open", ok, { once: true });
    ws.addEventListener("message", (ev: MessageEvent) => {
      if (typeof ev.data !== "string") return;
      try {
        const frame = JSON.parse(ev.data) as VoiceServerFrame;
        const mapped = toEvent(frame);
        if (mapped) onEvent(mapped);
      } catch {
        // ignore malformed control frames; binary frames are server->client only
      }
    });
    ws.addEventListener("close", () => onClose?.());
  });
}
