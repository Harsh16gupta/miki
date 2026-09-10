import { useEffect, useRef, useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { cn } from "../../lib/cn";
import { apiUrl } from "../../lib/config";
import { useAuth } from "../../app/useAuth";

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

/** Sign In link for guests, avatar menu for signed-in users. */
function AuthAction() {
  const { user, status } = useAuth();
  if (status === "loading") return null;
  if (!user) {
    return (
      <Link
        to="/login"
        className="hidden rounded-lg border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-neutral-200 transition-colors hover:bg-white/[0.08] hover:text-white focus-ring sm:inline"
      >
        Sign In
      </Link>
    );
  }
  return <UserMenu />;
}

/** T36: avatar menu with profile details, history link, logout. */
function UserMenu() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    const onPointer = (e: PointerEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("pointerdown", onPointer);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("pointerdown", onPointer);
    };
  }, [open ]);

  if (!user) return null;
  const initial = (user.full_name || user.email || "?").trim().charAt(0).toUpperCase();

  const handleLogout = () => {
    logout();
    setOpen(false);
    navigate("/", { replace: true });
  };

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-haspopup="menu"
        aria-label="Account menu"
        className="flex h-8 w-8 items-center justify-center rounded-lg bg-white text-sm font-bold text-zinc-950 transition-colors hover:bg-neutral-200 focus-ring"
      >
        {initial}
      </button>
      {open && (
        <div
          role="menu"
          className="absolute right-0 top-10 z-50 w-56 rounded-xl border border-white/[0.08] bg-[#18181b] p-2 shadow-xl"
        >
          <div className="px-3 py-2">
            <p className="truncate text-sm font-medium text-zinc-50">
              {user.full_name}
            </p>
            <p className="truncate font-mono text-xs text-zinc-500">{user.email}</p>
          </div>
          <div className="my-1 border-t border-white/[0.08]" />
          <Link
            to="/history"
            role="menuitem"
            onClick={() => setOpen(false)}
            className="block rounded-lg px-3 py-1.5 text-sm text-neutral-300 transition-colors hover:bg-white/[0.05] hover:text-white focus-ring"
          >
            Past sessions
          </Link>
          <button
            type="button"
            role="menuitem"
            onClick={handleLogout}
            className="block w-full rounded-lg px-3 py-1.5 text-left text-sm text-red-400 transition-colors hover:bg-red-500/[0.08] focus-ring"
          >
            Log out
          </button>
        </div>
      )}
    </div>
  );
}

export default function Navbar({ onReset }: { onReset: () => void }) {
  const navigate = useNavigate();
  const handleReset = () => {
    onReset();
    navigate("/setup");
  };
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
        <AuthAction />
        <button
          type="button"
          onClick={handleReset}
          className="rounded-lg px-3 py-1.5 text-sm text-neutral-400 transition-colors hover:bg-white/[0.05] hover:text-white focus-ring"
        >
          New Session
        </button>
      </div>
    </header>
  );
}
