import type { ReactNode } from "react";
import { cn } from "../../lib/cn";

export function PillBadge({
  children,
  tone = "ghost",
  className,
}: {
  children: ReactNode;
  tone?: "ghost" | "gold" | "cyan";
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px]",
        tone === "ghost" && "border-white/10 bg-white/5 text-[#a8a29e]",
        tone === "gold" && "gold-pill",
        tone === "cyan" &&
          "border-[#22d3ee]/40 bg-[#22d3ee]/10 text-[#7dd3fc]",
        className,
      )}
    >
      {children}
    </span>
  );
}

export function Spinner({ label = "Loading…" }: { label?: string }) {
  return (
    <span className="inline-flex items-center gap-2 text-sm text-[#a8a29e]" role="status">
      <span className="live-dot inline-block h-2 w-2 animate-pulse rounded-full bg-[#22d3ee]" />
      {label}
    </span>
  );
}

export function Toast({
  message,
  onDismiss,
}: {
  message: string;
  onDismiss: () => void;
}) {
  return (
    <div
      role="alert"
      className="glass glass-sheen fixed bottom-5 left-1/2 z-50 w-[min(92vw,28rem)] -translate-x-1/2 px-4 py-3"
    >
      <div className="glass-inner flex items-start justify-between gap-3">
        <p className="text-sm text-red-200">{message}</p>
        <button
          type="button"
          onClick={onDismiss}
          className="rounded-full border border-white/15 px-2.5 py-0.5 text-xs text-white/70 hover:text-white"
        >
          Dismiss
        </button>
      </div>
    </div>
  );
}
