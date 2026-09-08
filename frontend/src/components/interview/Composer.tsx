import { useState } from "react";
import { Mic, Send, Square } from "lucide-react";
import { cn } from "../../lib/cn";

interface Props {
  busy: boolean;
  recording: boolean;
  voiceStatus: string;
  canVoice: boolean;
  onSend: (text: string) => void;
  onToggleVoice: () => void;
}

export default function Composer({
  busy,
  recording,
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
    <div>
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
          className="chat-scroll min-h-[3.2rem] flex-1 resize-y rounded-2xl border border-white/12 bg-black/30 px-3.5 py-2.5 text-sm text-white placeholder:text-[#a8a29e]/70 focus:border-[#22d3ee]/50 focus:outline-none"
        />
        <div className="flex flex-col gap-2">
          <button
            type="button"
            onClick={send}
            disabled={!draft.trim() || busy}
            aria-label="Send answer"
            className="flex h-10 w-10 items-center justify-center rounded-full bg-[#f5f3ee] text-[#0b1120] transition enabled:hover:bg-white disabled:opacity-40"
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
              "flex h-10 w-10 items-center justify-center rounded-full border transition",
              recording
                ? "voice-live border-[#22d3ee]/60 bg-[#22d3ee]/15 text-[#7dd3fc]"
                : "border-white/15 bg-white/5 text-[#a8a29e] hover:border-white/30 hover:text-white",
              !canVoice && "cursor-not-allowed opacity-40",
            )}
          >
            {recording ? <Square size={15} /> : <Mic size={16} />}
          </button>
        </div>
      </div>
      <p className="mt-2 text-[11px] text-[#a8a29e]" role="status">
        {recording ? "● " : ""}
        {voiceStatus}
      </p>
    </div>
  );
}
