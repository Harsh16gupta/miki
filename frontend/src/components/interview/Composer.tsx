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

  const showWave = recording || speaking;

  return (
    <div>
      {showWave && (
        <div className="mb-2">
          <Waveform
            getAnalyser={getAnalyser}
            active={recording || speaking}
            tone={recording ? "cyan" : "emerald"}
            label={
              recording
                ? "Microphone input level"
                : "Miki voice playback level"
            }
          />
        </div>
      )}
      <div className="flex gap-2">
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
          rows={2}
          placeholder="Type your answer… (Enter to send)"
          disabled={busy && !recording}
          className="chat-scroll min-h-[3.2rem] flex-1 resize-y rounded-xl border border-white/[0.06] bg-[rgba(24,24,27,0.6)] px-3.5 py-2.5 text-sm text-zinc-50 placeholder:text-zinc-500 focus:border-white/25 focus:outline-none"
        />
        <div className="flex flex-col gap-2">
          <button
            type="button"
            onClick={send}
            disabled={!draft.trim() || busy}
            aria-label="Send answer"
            className="flex h-10 w-10 items-center justify-center rounded-lg bg-white text-zinc-950 shadow-sm transition-colors hover:bg-neutral-200 disabled:opacity-50"
          >
            <Send size={16} />
          </button>
          <button
            type="button"
            onClick={onToggleVoice}
            disabled={!canVoice}
            aria-label={recording ? "Stop recording" : "Start voice recording"}
            title={voiceStatus}
            className={cn(
              "flex h-10 w-10 items-center justify-center rounded-lg border transition-colors focus-ring",
              recording
                ? "voice-live border-cyan-500/20 bg-cyan-500/10 text-cyan-400"
                : "border-white/10 bg-white/[0.03] text-neutral-400 hover:bg-white/[0.08] hover:text-white",
              !canVoice && "cursor-not-allowed opacity-40",
            )}
          >
            {recording ? <Square size={15} /> : <Mic size={16} />}
          </button>
        </div>
      </div>
      <p className="mt-2 text-[11px] text-zinc-500" role="status">
        {recording ? "● " : ""}
        {voiceStatus}
      </p>
    </div>
  );
}
