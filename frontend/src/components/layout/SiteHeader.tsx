import { useEffect, useState } from "react";
import { apiUrl } from "../../lib/config";

export default function SiteHeader({ onReset }: { onReset: () => void }) {
  const [ready, setReady] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(apiUrl("/health"))
      .then((r) => {
        if (!cancelled) setReady(r.ok);
      })
      .catch(() => {
        if (!cancelled) setReady(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <header className="glass glass-sheen flex items-center justify-between px-5 py-3">
      <div className="glass-inner flex w-full items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl border border-[#d6c7a5]/40 bg-[#d6c7a5]/10 text-sm font-bold tracking-widest text-[#e5c878]">
            M
          </div>
          <div>
            <p className="text-sm font-semibold tracking-[0.2em] text-[#f5f3ee]">
              MIKI
            </p>
            <p className="text-[11px] tracking-wide text-[#a8a29e]">
              Interview Trainer
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span
            className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] text-[#a8a29e]"
            title="Backend health"
          >
            <span
              className={
                ready == null
                  ? "h-1.5 w-1.5 rounded-full bg-white/30"
                  : ready
                    ? "live-dot h-1.5 w-1.5 rounded-full bg-[#22d3ee]"
                    : "h-1.5 w-1.5 rounded-full bg-red-400"
              }
            />
            {ready == null ? "checking" : ready ? "ready" : "offline"}
          </span>
          <a
            href="/docs"
            target="_blank"
            rel="noreferrer"
            className="hidden rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] text-[#a8a29e] transition hover:border-white/25 hover:text-white sm:inline"
          >
            API docs
          </a>
          <button
            type="button"
            onClick={onReset}
            className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] text-[#a8a29e] transition hover:border-white/25 hover:text-white"
          >
            Reset
          </button>
        </div>
      </div>
    </header>
  );
}
