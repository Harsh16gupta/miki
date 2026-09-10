import { useEffect, useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { cn } from "../../lib/cn";
import { apiUrl } from "../../lib/config";

const stages = [
  { to: "/setup", label: "Setup" },
  { to: "/interview", label: "Interview" },
  { to: "/report", label: "Report" },
];

function HealthPill() {
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
      {ready == null ? "checking" : ready ? "live" : "offline"}
    </span>
  );
}

export default function Navbar({ onReset }: { onReset: () => void }) {
  return (
    <header className="sticky top-0 z-40 flex h-14 items-center justify-between gap-3 border-b border-white/[0.08] bg-[#09090b]/90 px-4 backdrop-blur-md sm:px-5">
      <Link
        to="/"
        className="flex shrink-0 items-center gap-2.5 rounded-lg focus-ring"
        aria-label="Miki home"
      >
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-white text-sm font-bold text-zinc-950">
          M
        </span>
        <span className="hidden flex-col leading-none sm:flex">
          <span className="text-sm font-semibold tracking-tight text-zinc-50">
            Miki
          </span>
          <span className="text-[11px] text-zinc-500">Evidence-Grounded Trainer</span>
        </span>
      </Link>

      <nav aria-label="Interview stages" className="flex items-center gap-1">
        {stages.map((s, i) => (
          <span key={s.to} className="flex items-center gap-1">
            {i > 0 && (
              <span aria-hidden="true" className="text-zinc-700">
                →
              </span>
            )}
            <NavLink
              to={s.to}
              className={({ isActive }) =>
                cn(
                  "rounded-lg px-2.5 py-1.5 text-sm transition-colors focus-ring sm:px-3",
                  isActive
                    ? "bg-white/[0.08] text-white"
                    : "text-neutral-400 hover:bg-white/[0.05] hover:text-white",
                )
              }
            >
              <span className="mr-1.5 font-mono text-[11px] text-zinc-500">
                {i + 1}
              </span>
              {s.label}
            </NavLink>
          </span>
        ))}
      </nav>

      <div className="flex shrink-0 items-center gap-2">
        <HealthPill />
        <Link
          to="/login"
          className="hidden rounded-lg border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-neutral-200 transition-colors hover:bg-white/[0.08] hover:text-white focus-ring sm:inline"
        >
          Sign In
        </Link>
        <button
          type="button"
          onClick={onReset}
          className="rounded-lg px-3 py-1.5 text-sm text-neutral-400 transition-colors hover:bg-white/[0.05] hover:text-white focus-ring"
        >
          New Session
        </button>
      </div>
    </header>
  );
}
