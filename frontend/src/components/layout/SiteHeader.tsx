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
    <header className="sticky top-0 z-40 flex h-14 items-center justify-between border-b border-white/[0.08] bg-[#09090b]/90 px-5 backdrop-blur-md">
      <div className="flex w-full items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white text-sm font-bold tracking-widest text-zinc-950">
            M
          </div>
          <div>
            <p className="text-sm font-semibold tracking-tight text-zinc-50">
              Miki
            </p>
            <p className="text-[11px] tracking-wide text-zinc-400">
              Evidence-Grounded Trainer
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span
            className="inline-flex items-center gap-1.5 rounded-full border border-white/[0.08] bg-white/[0.06] px-2.5 py-0.5 text-xs font-medium text-zinc-300"
            title="Backend health"
          >
            <span
              className={
                ready == null
                  ? "h-1.5 w-1.5 rounded-full bg-white/30"
                  : ready
                    ? "live-dot h-1.5 w-1.5 rounded-full bg-cyan-500"
                    : "h-1.5 w-1.5 rounded-full bg-red-400"
              }
            />
            {ready == null ? "checking" : ready ? "ready" : "offline"}
          </span>
          <a
            href="/docs"
            target="_blank"
            rel="noreferrer"
            className="hidden rounded-lg px-3 py-1.5 text-sm text-neutral-400 transition-colors hover:bg-white/[0.05] hover:text-white sm:inline"
          >
            API docs
          </a>
          <button
            type="button"
            onClick={onReset}
            className="rounded-lg border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-neutral-200 transition-colors hover:bg-white/[0.08] hover:text-white"
          >
            New Session
          </button>
        </div>
      </div>
    </header>
  );
}
