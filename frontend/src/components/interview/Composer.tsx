import { useState } from "react";
import { Mic, Send, Square } from "lucide-react";
import { cn } from "../../lib/cn";
import Waveform from "./Waveform";

interface Props {
  busy: boolean;
  recording: boolean;
  speaking: boolean;
  getAnalyser: () => AnalyserNode | null;
  voiceStatus: string;
  canVoice: boolean;
  onSend: (text: string) => void;
  onToggleVoice: () => void;
}

/** Composer bar (image 04): underline input + orange mic + waveform + hold-space hint.
    Text send stays available (Enter / send button) — backend wiring unchanged. */
export default function Composer({
  busy,
  recording,
  speaking,
  getAnalyser,
  voiceStatus,
  canVoice,
  onSend,
  onToggleVoice,
}: Props) {
  const [draft, setDraft] = useState("");

  const send = () => {
    const t = draft.trim();
    if (!t || busy) return;
    setDraft("");
    onSend(t);
  };

  return (
    <div className="border border-white/[0.14] bg-[#06090A] px-4 py-3 sm:px-5">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-3">
        <label htmlFor="composer-input" className="sr-only">
          Press and speak or type a message
        </label>
        <textarea
          id="composer-input"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
          rows={1}
          placeholder="Press and speak or type a message…"
          disabled={busy && !recording}
          className="input-underline min-w-[12rem] flex-1 italic"
        />
        <button
          type="button"
          onClick={send}
          disabled={!draft.trim() || busy}
          aria-label="Send answer"
          title="Send (Enter)"
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-none border border-[#83DDDA]/60 text-[#83DDDA] transition-colors duration-150 ease-out hover:bg-[#83DDDA]/10 disabled:cursor-not-allowed disabled:opacity-40 focus-ring"
        >
          <Send size={15} />
        </button>
        <button
          type="button"
          onClick={onToggleVoice}
          disabled={!canVoice}
          aria-label={recording ? "Stop recording" : "Start voice recording"}
          title={voiceStatus}
          className={cn(
            "flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[#E4621F] text-black transition-all duration-150 ease-out hover:brightness-110 focus-ring",
            recording && "voice-live",
            !canVoice && "cursor-not-allowed opacity-40",
          )}
        >
          {recording ? <Square size={16} /> : <Mic size={17} />}
        </button>
        <div className="w-36 shrink-0 sm:w-48" aria-hidden="true">
          <Waveform
            getAnalyser={getAnalyser}
            active={recording || speaking}
            tone={recording ? "teal" : "sage"}
            label={
              recording
                ? "Microphone input level"
                : "Miki voice playback level"
            }
          />
        </div>
        <p className="shrink-0 font-mono text-[11px] uppercase leading-relaxed tracking-[0.14em] text-[#8FA3A0]">
          Hold space
          <br />
          to talk
        </p>
      </div>
      <p className="mt-1.5 font-mono text-[11px] tabular-nums text-[#8FA3A0]" role="status">
        {recording ? "● " : ""}
        {voiceStatus}
      </p>
    </div>
  );
}
