import { useCallback, useEffect, useRef, useState } from "react";
import {
  connectVoiceSocket,
  pickAudioMimeType,
  speakBrowserFallback,
  type VoiceEvent,
} from "../lib/voiceSocket";
import {
  attachElementAnalyser,
  attachMicAnalyser,
  type AnalyserHandle,
} from "../lib/audioAnalyser";
import type { InterviewApi } from "./useInterview";

/**
 * Click Start/Stop voice toggle. Pure frontend wiring over the existing
 * WS protocol (binary frames + {type:end_of_turn}); no backend change.
 * Hold-to-talk later reuses start()/stop() with different events.
 */
export function useVoice(interview: InterviewApi) {
  const [recording, setRecording] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState<string>("Voice idle");
  const wsRef = useRef<WebSocket | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  // Sentence-chunked TTS arrives as several `audio` frames; queue them so a
  // new chunk never cuts off the one still playing.
  const audioQueueRef = useRef<Array<{ dataB64: string; fallbackText: string }>>([]);
  // One-shot audio transport: chunks accumulate here during recording and go
  // out as a SINGLE Blob on Stop (valid container) with its MIME signaled.
  // Streaming raw timeslice chunks produced corrupt files server-side.
  const audioChunksRef = useRef<Blob[]>([]);
  const audioMimeRef = useRef<string>("audio/webm");
  const analyserRef = useRef<AnalyserHandle | null>(null);
  const lastQuestionRef = useRef("");
  const sessionRef = useRef<number | null>(null);

  useEffect(() => {
    sessionRef.current = interview.sessionId;
  }, [interview.sessionId]);

  // Keep last Miki question for TTS fallback + error narration.
  useEffect(() => {
    const last = [...interview.messages].reverse().find((m) => m.who === "miki");
    if (last) lastQuestionRef.current = last.text;
  }, [interview.messages]);

  const detachAnalyser = useCallback(() => {
    analyserRef.current?.dispose();
    analyserRef.current = null;
  }, []);

  const getAnalyser = useCallback((): AnalyserNode | null => {
    return analyserRef.current?.analyser ?? null;
  }, []);

  const cleanup = useCallback((closeSocket: boolean) => {
    audioQueueRef.current = [];
    try {
      audioRef.current?.pause();
    } catch {
      // ignore pause races
    }
    audioRef.current = null;
    detachAnalyser();
    const rec = recorderRef.current;
    if (rec && rec.state !== "inactive") {
      try {
        rec.stop();
      } catch {
        // ignore stop races
      }
    }
    recorderRef.current = null;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    if (closeSocket) {
      try {
        wsRef.current?.close();
      } catch {
        // ignore
      }
      wsRef.current = null;
    }
    setRecording(false);
  }, [detachAnalyser]);

  useEffect(() => () => cleanup(true), [cleanup]);

  // Named function expression: `play` recurses for queue draining without
  // capturing the in-progress `playAudioB64` binding (oxlint-clean).
  const playAudioB64 = useCallback(function play(
    dataB64: string,
    fallbackText: string,
  ): void {
    // If something is already playing, queue behind it (chunked TTS).
    if (audioRef.current && !audioRef.current.paused && !audioRef.current.ended) {
      audioQueueRef.current.push({ dataB64, fallbackText });
      return;
    }
    const playNext = (): void => {
      const next = audioQueueRef.current.shift();
      if (!next) return;
      play(next.dataB64, next.fallbackText);
    };
    try {
      detachAnalyser();
      setSpeaking(false);
      audioRef.current?.pause();
      const audio = new Audio(`data:audio/mp3;base64,${dataB64}`);
      audioRef.current = audio;
      const handle = attachElementAnalyser(audio);
      if (handle) {
        analyserRef.current = handle;
        setSpeaking(true);
      }
      const stopSpeaking = () => {
        setSpeaking(false);
        if (analyserRef.current === handle) detachAnalyser();
      };
      audio.onended = () => {
        stopSpeaking();
        if (audioQueueRef.current.length > 0) {
          playNext();
        } else {
          setVoiceStatus("Ready — click Speak to answer");
        }
      };
      audio.onerror = () => {
        stopSpeaking();
        playNext();
      };
      audio.play().catch(() => {
        stopSpeaking();
        speakBrowserFallback(fallbackText);
        playNext();
      });
    } catch {
      speakBrowserFallback(fallbackText);
      playNext();
    }
  }, [detachAnalyser]);

  const handleEvent = useCallback(
    (ev: VoiceEvent) => {
      switch (ev.kind) {
        case "ready":
          setVoiceStatus("Connected — click Speak to answer");
          break;
        case "answer":
          // Stop recording so the mic never captures Miki's reply.
          cleanup(false);
          setVoiceStatus("Miki is thinking…");
          interview.pushCandidateVoice(ev.transcript);
          break;
        case "question":
          lastQuestionRef.current = ev.text;
          interview.pushMikiVoice(ev.text);
          setVoiceStatus("Miki is speaking…");
          if (ev.finished && sessionRef.current != null) {
            cleanup(true);
            void interview.loadReport(sessionRef.current);
          }
          break;
        case "audio":
          setVoiceStatus("Miki is speaking…");
          playAudioB64(ev.dataB64, lastQuestionRef.current);
          break;
        case "done":
          cleanup(true);
          if (sessionRef.current != null)
            void interview.loadReport(sessionRef.current);
          break;
        case "error":
          cleanup(false);
          interview.toast(`Voice error: ${ev.detail}`);
          setVoiceStatus("Voice error — see toast");
          if (lastQuestionRef.current)
            speakBrowserFallback(lastQuestionRef.current);
          break;
      }
    },
    [cleanup, interview, playAudioB64],
  );

  const ensureSocket = useCallback(async (): Promise<WebSocket | null> => {
    const sid = sessionRef.current;
    if (sid == null) {
      interview.toast("Start the interview before using voice");
      return null;
    }
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN)
      return wsRef.current;
    try {
      wsRef.current?.close();
    } catch {
      // ignore
    }
    wsRef.current = null;
    try {
      const ws = await connectVoiceSocket(sid, handleEvent, () => {
        wsRef.current = null;
      });
      wsRef.current = ws;
      return ws;
    } catch {
      interview.toast("Voice socket failed. Is the backend reachable?");
      setVoiceStatus("Socket error");
      return null;
    }
  }, [handleEvent, interview]);

  const start = useCallback(async () => {
    if (recording || interview.sessionId == null) return;
    setVoiceStatus("Connecting…");
    const ws = await ensureSocket();
    if (!ws) return;
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      interview.toast("Microphone blocked. Allow mic access and retry.");
      setVoiceStatus("Mic blocked");
      return;
    }
    streamRef.current = stream;
    detachAnalyser();
    const micHandle = attachMicAnalyser(stream);
    if (micHandle) analyserRef.current = micHandle;
    let recorder: MediaRecorder;
    try {
      const mime = pickAudioMimeType();
      recorder = mime
        ? new MediaRecorder(stream, { mimeType: mime })
        : new MediaRecorder(stream);
    } catch {
      interview.toast("This browser cannot record audio");
      detachAnalyser();
      stream.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
      return;
    }
    recorderRef.current = recorder;
    audioChunksRef.current = [];
    audioMimeRef.current = recorder.mimeType || "audio/webm";
    recorder.ondataavailable = (e: BlobEvent) => {
      if (e.data.size > 0) audioChunksRef.current.push(e.data);
    };
    recorder.start(250);
    setRecording(true);
    setVoiceStatus("Recording… speak, then click Stop (or go silent)");
  }, [detachAnalyser, ensureSocket, interview, recording]);

  // Minimum speech payload: anything smaller is a mic blip, not an answer.
  // Rejected locally with a friendly toast — no server round trip.
  const MIN_SPEECH_BYTES = 2000;

  const stop = useCallback(
    (sendEnd = true) => {
      const ws = wsRef.current;
      const sendBlob = () => {
        const chunks = audioChunksRef.current;
        audioChunksRef.current = [];
        const open = ws && ws.readyState === WebSocket.OPEN;
        if (!sendEnd || !open) {
          cleanup(false);
          setVoiceStatus("Ready — click Speak to answer");
          return;
        }
        const total = chunks.reduce((n, c) => n + c.size, 0);
        if (total < MIN_SPEECH_BYTES) {
          cleanup(false);
          interview.toast("Didn't catch that — tap Speak and try again.");
          setVoiceStatus("Ready — click Speak to answer");
          return;
        }
        try {
          const mime = audioMimeRef.current;
          ws.send(JSON.stringify({ type: "audio_format", mime }));
          ws.send(new Blob(chunks, { type: mime }));
          ws.send(JSON.stringify({ type: "end_of_turn" }));
          setVoiceStatus("Sending…");
        } catch {
          setVoiceStatus("Send failed");
        }
        cleanup(false);
      };
      const rec = recorderRef.current;
      if (rec && rec.state !== "inactive") {
        // Final ondataavailable fires before onstop per spec — send after it.
        rec.onstop = () => sendBlob();
        try {
          rec.stop();
        } catch {
          sendBlob();
        }
      } else {
        sendBlob();
      }
    },
    [cleanup, interview],
  );

  const toggle = useCallback(() => {
    if (recording) stop(true);
    else void start();
  }, [recording, start, stop]);

  return { recording, speaking, voiceStatus, toggle, stopVoice: stop, getAnalyser };
}
