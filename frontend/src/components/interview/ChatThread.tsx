import { useEffect, useRef, useState } from "react";
import type { ChatMessage } from "../../types/api";
import { cn } from "../../lib/cn";

function formatStamp(ms: number): string {
  const total = Math.max(0, Math.floor(ms / 1000));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

/** Session-relative arrival time, captured once when the row mounts
    (messages carry no timestamps from the backend). */
function MsgTime({ startedAt }: { startedAt: number | null }) {
  const [at] = useState(() => Date.now());
  if (startedAt == null) return null;
  return <>{formatStamp(at - startedAt)}</>;
}

/** Transcript ledger: avatar ring (M teal / H sage) + serif name + mono
    timestamp + serif message, hairline separators. Arrival times are captured
    presentationally relative to session start (messages carry no timestamps). */
export default function ChatThread({
  messages,
  startedAt,
}: {
  messages: ChatMessage[];
  startedAt: number | null;
}) {
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = boxRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages.length]);

  if (messages.length === 0) {
    return (
      <div className="px-4 py-10 text-center font-serif text-[15px] text-[#8FA3A0]">
        Miki&apos;s opening question lands here — answer by voice or text.
      </div>
    );
  }

  return (
    <div
      ref={boxRef}
      aria-live="polite"
      className="chat-scroll max-h-[30rem] min-h-[12rem] overflow-y-auto"
    >
      {messages.map((m) => {
        const miki = m.who === "miki";
        return (
          <div
            key={m.id}
            className="msg-in flex gap-4 border-b border-white/[0.08] px-5 py-4 last:border-b-0"
          >
            <span
              aria-hidden="true"
              className={cn(
                "flex h-9 w-9 shrink-0 items-center justify-center rounded-full border font-serif text-sm font-semibold",
                miki
                  ? "border-[#3AA99E] text-[#3AA99E]"
                  : "border-[#83DDDA] text-[#83DDDA]",
              )}
            >
              {miki ? "M" : "H"}
            </span>
            <div className="min-w-0 flex-1">
              <p className="flex flex-wrap items-baseline gap-x-3">
                <span className="font-serif text-base font-semibold text-[#83DDDA]">
                  {miki ? "Miki" : "You"}
                </span>
                <span className="font-mono text-[11px] tabular-nums text-[#8FA3A0]">
                  <MsgTime startedAt={startedAt} />
                </span>
                {!miki && m.voice && (
                  <span className="font-mono text-[11px] uppercase tracking-[0.14em] text-[#3AA99E]">
                    · voice
                  </span>
                )}
              </p>
              <p className="mt-1 whitespace-pre-wrap font-serif text-[15px] leading-relaxed text-[#83DDDA]">
                {m.text}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
