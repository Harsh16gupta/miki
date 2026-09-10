import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { cn } from "../../lib/cn";
import type { InterviewApi } from "../../hooks/useInterview";
import type { useVoice } from "../../hooks/useVoice";
import { Badge, Button, Spinner } from "../common/Primitives";
import ChatThread from "./ChatThread";
import Composer from "./Composer";

interface Props {
  interview: InterviewApi;
  voice: ReturnType<typeof useVoice>;
}

function formatElapsed(ms: number): string {
  const total = Math.max(0, Math.floor(ms / 1000));
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function SessionTimer({ startedAt }: { startedAt: number }) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const t = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(t);
  }, []);
  return (
    <span
      className="font-mono text-xs tabular-nums text-zinc-400"
      title="Session elapsed time"
    >
      {formatElapsed(now - startedAt)}
    </span>
  );
}

/** T21: live telemetry — real states, turn/claim counters, versions. */
function TelemetryDrawer({ interview }: { interview: InterviewApi }) {
  const { detail, interviewState, policyVersion, claimsFound, startedAt } = interview;
  const rows: [string, string][] = [
    ["State", detail?.state ?? interviewState ?? "—"],
    ["Turns", detail != null ? String(detail.turns) : "—"],
    ["Claims extracted", detail != null ? String(detail.claims) : String(claimsFound)],
    ["Policy", detail?.policy_version ?? policyVersion ?? "—"],
    ["Engine", detail?.engine_version ?? "—"],
    [
      "Started",
      startedAt != null
        ? new Date(startedAt).toLocaleTimeString()
        : (detail?.started_at ?? "—"),
    ],
  ];
  return (
    <aside
      aria-label="Session telemetry"
      className="rounded-xl border border-white/[0.08] bg-black/30 p-4"
    >
      <p className="text-xs font-medium uppercase tracking-wider text-neutral-400">
        Live telemetry
      </p>
      <dl className="mt-2 space-y-1.5 text-sm">
        {rows.map(([k, v]) => (
          <div key={k} className="flex items-center justify-between gap-2">
            <dt className="text-xs text-zinc-500">{k}</dt>
            <dd className="font-mono text-xs tabular-nums text-zinc-200">{v}</dd>
          </div>
        ))}
      </dl>
    </aside>
  );
}

export default function InterviewCard({ interview, voice }: Props) {
  const navigate = useNavigate();
  const [drawerOpen, setDrawerOpen] = useState(true);
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
      <div className="rounded-xl border border-white/[0.08] bg-zinc-900/60 p-5 shadow-xl sm:p-6">
        <div className="rounded-xl border border-white/[0.08] bg-black/30 px-4 py-8 text-center text-sm text-zinc-400">
          Complete setup to unlock the arena.{" "}
          <Link to="/setup" className="text-cyan-300 hover:text-white">
            Go to setup
          </Link>
        </div>
      </div>
    );
  }

  if (interview.stage === "report") {
    return (
      <div className="rounded-xl border border-white/[0.08] bg-zinc-900/60 p-5 shadow-xl sm:p-6">
        <div className="rounded-xl border border-white/[0.08] bg-black/30 px-4 py-8 text-center text-sm text-zinc-400">
          Session complete.{" "}
          <Link to="/report" className="text-cyan-300 hover:text-white">
            View your report
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-white/[0.08] bg-zinc-900/60 p-5 shadow-xl sm:p-6">
      {/* T16: session header */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-1.5">
          {interview.sessionId != null && (
            <Badge>session #{interview.sessionId}</Badge>
          )}
          {interview.interviewState && (
            <Badge tone="cyan" dot>
              {interview.interviewState}
            </Badge>
          )}
          {interview.claimsFound > 0 && (
            <Badge tone="amber">{interview.claimsFound} claims</Badge>
          )}
          {interview.policyVersion && (
            <Badge>policy {interview.policyVersion}</Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          {interview.startedAt != null && (
            <SessionTimer startedAt={interview.startedAt} />
          )}
          <button
            type="button"
            onClick={() => setDrawerOpen((o) => !o)}
            aria-expanded={drawerOpen}
            className="rounded-lg px-3 py-1.5 text-sm text-neutral-400 transition-colors hover:bg-white/[0.05] hover:text-white focus-ring"
          >
            {drawerOpen ? "Hide context" : "Show context"}
          </button>
          <Button variant="danger" onClick={() => void handleEnd()}>
            End Session
          </Button>
        </div>
      </div>

      {/* T17: dual-pane workbench */}
      <div
        className={cn(
          "mt-4 grid gap-4",
          drawerOpen && active ? "md:grid-cols-[minmax(0,1fr)_240px]" : "grid-cols-1",
        )}
      >
        <div className="min-w-0 space-y-4">
          <ChatThread messages={interview.messages} />
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
        {drawerOpen && <TelemetryDrawer interview={interview} />}
      </div>
    </div>
  );
}
