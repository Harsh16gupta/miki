import { useEffect, useRef } from "react";
import type { ChatMessage } from "../../types/api";
import { cn } from "../../lib/cn";

export default function ChatThread({ messages }: { messages: ChatMessage[] }) {
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = boxRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages.length]);

  if (messages.length === 0) {
    return (
      <div className="rounded-xl border border-white/[0.08] bg-black/30 px-4 py-8 text-center text-sm text-zinc-400">
        Start the interview above — Miki&apos;s opening question lands here.
      </div>
    );
  }

  return (
    <div
      ref={boxRef}
      aria-live="polite"
      className="chat-scroll min-h-[12rem] max-h-[26rem] space-y-2.5 overflow-y-auto pr-1"
    >
      {messages.map((m) => (
        <div
          key={m.id}
          className={cn(
            "msg-in max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed",
            m.who === "miki"
              ? "border border-white/[0.08] bg-white/[0.06] text-zinc-50"
              : "ml-auto border border-white/10 bg-white/[0.03] text-right text-zinc-50",
          )}
        >
          <p
            className={
              m.who === "miki"
                ? "mb-1 text-[10px] font-medium tracking-[0.16em] text-amber-300"
                : "mb-1 text-[10px] tracking-[0.16em] text-zinc-500"
            }
          >
            {m.who === "miki" ? "MIKI" : m.voice ? "YOU · VOICE" : "YOU"}
          </p>
          <p className="whitespace-pre-wrap">{m.text}</p>
        </div>
      ))}
    </div>
  );
}
