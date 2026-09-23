import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { cn } from "../../lib/cn";
import type { InterviewApi } from "../../hooks/useInterview";
import type { useVoice } from "../../hooks/useVoice";
import { Button, Spinner } from "../common/Primitives";
import { Stamp } from "../common/Primitives";
import Breadcrumb from "../common/Breadcrumb";
import ChatThread from "./ChatThread";
import Composer from "./Composer";

interface Props {
  interview: InterviewApi;
  voice: ReturnType<typeof useVoice>;
}

function formatElapsed(ms: number): string {
  const total = Math.max(0, Math.floor(ms / 1000));
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function SessionTimer({ startedAt, large = false }: { startedAt: number; large?: boolean }) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const t = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(t);
  }, []);
  return (
    <span
      className={cn(
        "font-mono tabular-nums text-[#83DDDA]",
        large ? "text-xl sm:text-2xl" : "text-xs",
      )}
      title="Session elapsed time"
    >
      {formatElapsed(now - startedAt)}
    </span>
  );
}

const FOCUS_ROWS = ["Technical depth", "Clarity", "Trade-offs", "Examples"];

/** Session-info rail (image 04): STATE/TURNS/TIME/CLAIMS/FOLLOW-UPS, current
    focus, next question. Follow-ups derive from real Miki message counts —
    the backend exposes no counter. Wiring otherwise untouched. */
function SessionRail({ interview }: { interview: InterviewApi }) {
  const { detail, interviewState, claimsFound, messages, startedAt, sessionId } =
    interview;
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const t = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(t);
  }, []);
  const followUps = Math.max(
    0,
    messages.filter((m) => m.who === "miki").length - 1,
  );
  const rows: [string, string, boolean][] = [
    ["State", detail?.state ?? interviewState ?? "—", true],
    ["Turns", detail != null ? String(detail.turns) : "—", false],
    ["Time", startedAt != null ? formatElapsed(now - startedAt) : "—", false],
    [
      "Claims detected",
      detail != null ? String(detail.claims) : String(claimsFound),
      false,
    ],
    ["Follow ups", String(followUps), false],
  ];
  return (
    <aside
      aria-label="Session info"
      className="rounded-none border border-white/[0.14] bg-[#06090A] p-5"
    >
      <div className="flex items-center justify-between gap-3 border-b border-white/[0.14] pb-3">
        <h2 className="font-mono text-xs uppercase tracking-[0.18em] text-[#83DDDA]">
          Session info
        </h2>
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-[#8FA3A0]">
          {sessionId != null
            ? `SES-${String(sessionId).padStart(3, "0")}`
            : "SES-···"}
        </p>
      </div>
      <dl className="mt-4 space-y-2.5">
        {rows.map(([k, v, hot]) => (
          <div key={k} className="flex items-baseline justify-between gap-2">
            <dt className="font-mono text-[11px] uppercase tracking-[0.14em] text-[#8FA3A0]">
              {k}
            </dt>
            <dd
              className={cn(
                "font-mono text-xs tabular-nums",
                hot && v.toLowerCase() === "live"
                  ? "uppercase tracking-[0.14em] text-[#3AA99E]"
                  : "text-[#83DDDA]",
              )}
            >
              {v}
            </dd>
          </div>
        ))}
      </dl>
      <div className="mt-5 border-t border-white/[0.14] pt-4">
        <h3 className="font-mono text-[11px] uppercase tracking-[0.18em] text-[#8FA3A0]">
          Current focus
        </h3>
        <ul className="mt-3 space-y-2">
          {FOCUS_ROWS.map((f) => (
            <li
              key={f}
              className="flex items-baseline justify-between gap-2 font-mono text-[11px] uppercase tracking-[0.14em]"
            >
              <span className="text-[#8FA3A0]">{f}</span>
              <span className="text-[#3AA99E]">→ ON</span>
            </li>
          ))}
        </ul>
      </div>
      <div className="mt-5 border-t border-white/[0.14] pt-4">
        <h3 className="font-mono text-[11px] uppercase tracking-[0.18em] text-[#8FA3A0]">
          Next question
        </h3>
        <p className="mt-2 font-serif text-[15px] italic leading-relaxed text-[#8FA3A0]">
          {interview.status === "thinking" || interview.status === "starting"
            ? "Miki is choosing a follow-up…"
            : "Answer above — Miki's follow-up lands in the ledger."}
        </p>
      </div>
    </aside>
  );
}

export default function InterviewCard({ interview, voice }: Props) {
  const navigate = useNavigate();
  const [railOpen, setRailOpen] = useState(true);
  const active = interview.stage !== "setup";
  const busy = interview.status === "thinking" || interview.status === "starting";

  // Poll session detail while the arena is live (best-effort telemetry).
  useEffect(() => {
    if (!active || interview.sessionId == null) return;
    if (interview.status !== "live" && interview.status !== "thinking") return;
    void interview.refreshDetail();
    const t = window.setInterval(() => void interview.refreshDetail(), 8000);
    return () => window.clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active, interview.sessionId, interview.status]);

  const handleEnd = async () => {
    const ok = await interview.abort();
    if (ok) navigate("/setup");
  };

  if (!active) {
    return (
      <div className="rounded-none border border-white/[0.08] bg-[#0E1223] p-5 sm:p-6">
        <div className="border border-white/[0.08] bg-black/30 px-4 py-8 text-center font-serif text-[15px] text-[#8FA3A0]">
          Complete setup to unlock the arena.{" "}
          <Link
            to="/setup"
            className="rounded-none font-mono text-xs uppercase tracking-[0.14em] text-[#3AA99E] transition-colors duration-150 ease-out hover:text-[#83DDDA] focus-ring"
          >
            Go to setup →
          </Link>
        </div>
      </div>
    );
  }

  if (interview.stage === "report") {
    return (
      <div className="rounded-none border border-white/[0.08] bg-[#0E1223] p-5 sm:p-6">
        <div className="border border-white/[0.08] bg-black/30 px-4 py-8 text-center font-serif text-[15px] text-[#8FA3A0]">
          Session complete.{" "}
          <Link
            to="/report"
            className="rounded-none font-mono text-xs uppercase tracking-[0.14em] text-[#3AA99E] transition-colors duration-150 ease-out hover:text-[#83DDDA] focus-ring"
          >
            View your report →
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 pt-4">
      {/* session header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Breadcrumb trail={[{ label: "Session" }, { label: "Live" }]} />
        <div className="flex items-center gap-5">
          <Stamp tone="teal">Live</Stamp>
          <p className="flex items-baseline gap-3">
            <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-[#8FA3A0]">
              Time elapsed
            </span>
            {interview.startedAt != null ? (
              <SessionTimer startedAt={interview.startedAt} large />
            ) : (
              <span className="font-mono text-xl tabular-nums text-[#83DDDA]">
                --:--:--
              </span>
            )}
          </p>
        </div>
      </div>

      <div
        className={cn(
          "grid items-start gap-4",
          railOpen ? "lg:grid-cols-[minmax(0,1fr)_300px]" : "grid-cols-1",
        )}
      >
        <div className="min-w-0 space-y-4">
          <div className="rounded-none border border-white/[0.14] bg-[#06090A]">
            <ChatThread
              messages={interview.messages}
              startedAt={interview.startedAt}
            />
          </div>
          {busy && <Spinner label="Miki is thinking…" />}
          <Composer
            busy={busy}
            recording={voice.recording}
            speaking={voice.speaking}
            getAnalyser={voice.getAnalyser}
            voiceStatus={voice.voiceStatus}
            canVoice={interview.sessionId != null}
            onSend={(t) => void interview.answer(t)}
            onToggleVoice={voice.toggle}
          />
        </div>
        {railOpen && <SessionRail interview={interview} />}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => setRailOpen((o) => !o)}
          aria-expanded={railOpen}
          className="rounded-none px-2 py-1 font-mono text-[11px] uppercase tracking-[0.14em] text-[#8FA3A0] transition-colors duration-150 ease-out hover:text-[#83DDDA] focus-ring"
        >
          {railOpen ? "Hide session info" : "Show session info"}
        </button>
        <Button variant="danger" onClick={() => void handleEnd()}>
          End session
        </Button>
      </div>
    </div>
  );
}
