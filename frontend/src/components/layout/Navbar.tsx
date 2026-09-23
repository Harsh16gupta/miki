import { useEffect, useRef, useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { cn } from "../../lib/cn";
import { apiUrl } from "../../lib/config";
import { useAuth } from "../../app/useAuth";

/* Mono nav mapped to existing routes (SCREEN-SPECS.md: 02-landing). */
const stages = [
  { to: "/setup", label: "Practice" },
  { to: "/interview", label: "Review" },
  { to: "/report", label: "Improve" },
  { to: "/", label: "About" },
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
      className="inline-flex items-center gap-1.5 rounded-none border border-white/[0.08] bg-white/[0.04] px-2.5 py-0.5 font-mono text-[11px] uppercase tracking-[0.14em] text-[#8FA3A0]"
      title="Backend health"
    >
      <span
        className={
          ready == null
            ? "h-1.5 w-1.5 rounded-full bg-white/30"
            : ready
              ? "live-dot h-1.5 w-1.5 rounded-full bg-[#3AA99E]"
              : "h-1.5 w-1.5 rounded-full bg-[#f87171]"
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
        className="hidden px-2 py-1 font-mono text-xs uppercase tracking-[0.14em] text-[#8FA3A0] transition-colors duration-150 ease-out hover:text-[#83DDDA] focus-ring sm:inline"
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
        className="flex h-8 w-8 items-center justify-center rounded-none border border-[#83DDDA]/60 font-serif text-sm font-bold text-[#83DDDA] transition-colors duration-150 ease-out hover:bg-[#83DDDA]/10 focus-ring"
      >
        {initial}
      </button>
      {open && (
        <div
          role="menu"
          className="absolute right-0 top-10 z-50 w-56 rounded-none border border-white/[0.08] bg-[#0E1223] p-2"
        >
          <div className="px-3 py-2">
            <p className="truncate font-serif text-sm font-medium text-[#83DDDA]">
              {user.full_name}
            </p>
            <p className="truncate font-mono text-xs text-[#8FA3A0]">{user.email}</p>
          </div>
          <div className="my-1 border-t border-white/[0.08]" />
          <Link
            to="/history"
            role="menuitem"
            onClick={() => setOpen(false)}
            className="block rounded-none px-3 py-1.5 font-mono text-xs uppercase tracking-[0.14em] text-[#8FA3A0] transition-colors duration-150 ease-out hover:bg-white/[0.05] hover:text-[#83DDDA] focus-ring"
          >
            Past sessions
          </Link>
          <button
            type="button"
            role="menuitem"
            onClick={handleLogout}
            className="block w-full rounded-none px-3 py-1.5 text-left font-mono text-xs uppercase tracking-[0.14em] text-[#f87171] transition-colors duration-150 ease-out hover:bg-red-500/[0.08] focus-ring"
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
    <header className="sticky top-0 z-40 border-b border-white/[0.08] bg-[#06090A]/90 backdrop-blur-md">
      <div className="flex min-h-14 flex-wrap items-center justify-between gap-x-6 gap-y-2 py-3">
        <Link
          to="/"
          className="flex shrink-0 items-center gap-4 rounded-none focus-ring"
          aria-label="Miki home"
        >
          <span className="font-serif text-4xl font-semibold tracking-tight text-[#83DDDA]">
            Miki
          </span>
          <span aria-hidden="true" className="h-10 w-px bg-white/[0.14]" />
          <span className="hidden flex-col leading-relaxed font-mono text-[11px] uppercase tracking-[0.18em] text-[#8FA3A0] min-[420px]:flex">
            <span>AI voice interview trainer</span>
            <span>for software engineers</span>
          </span>
        </Link>

        <div className="flex shrink-0 items-center gap-4">
          <nav aria-label="Primary" className="flex items-center gap-4 sm:gap-6">
            {stages.map((s) => (
              <NavLink
                key={s.to}
                to={s.to}
                className={({ isActive }) =>
                  cn(
                    "rounded-none font-mono text-xs uppercase tracking-[0.18em] transition-colors duration-150 ease-out focus-ring",
                    isActive
                      ? "text-[#83DDDA]"
                      : "text-[#8FA3A0] hover:text-[#83DDDA]",
                  )
                }
              >
                {s.label}
              </NavLink>
            ))}
          </nav>
          <div className="flex shrink-0 items-center gap-2">
            <HealthPill />
            <AuthAction />
            <button
              type="button"
              onClick={handleReset}
              className="rounded-none px-2 py-1 font-mono text-xs uppercase tracking-[0.14em] text-[#8FA3A0] transition-colors duration-150 ease-out hover:text-[#83DDDA] focus-ring"
            >
              New Session
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
