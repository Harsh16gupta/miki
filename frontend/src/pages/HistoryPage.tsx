import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Spinner } from "../components/common/Primitives";
import Breadcrumb from "../components/common/Breadcrumb";
import { apiFetch, ApiError } from "../lib/api";
import type { HistoryEntry, HistoryResponse } from "../types/api";

function formatDate(iso: string): string {
  try {
    return new Date(iso)
      .toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      })
      .toUpperCase();
  } catch {
    return iso;
  }
}

function formatDuration(totalS: number | null): string {
  if (totalS == null) return "—";
  const m = Math.floor(totalS / 60);
  return m > 0 ? `${m}m ${totalS % 60}s` : `${totalS}s`;
}

/** Backend scores 1–5; history chips display /100 like the report. */
const to100 = (score5: number): number =>
  Math.round((Math.max(0, Math.min(5, score5)) / 5) * 100);

function EntryCard({ entry }: { entry: HistoryEntry }) {
  return (
    <div className="rounded-none border border-white/[0.08] bg-[#0E1223] p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-[#83DDDA]">
          Session-{String(entry.session_id).padStart(3, "0")}
          <span className="ml-3 tabular-nums text-[#8FA3A0]">
            {formatDate(entry.started_at)} · {formatDuration(entry.duration_s)}
          </span>
        </p>
        <div className="flex items-center gap-1.5">
          <Badge tone={entry.status === "completed" ? "success" : "default"}>
            {entry.status}
          </Badge>
          {entry.overall_score != null && (
            <Badge tone="amber">{to100(entry.overall_score)} / 100</Badge>
          )}
        </div>
      </div>
      {entry.dimensions.length > 0 && (
        <ul className="mt-2.5 flex flex-wrap gap-1.5 border-t border-white/[0.06] pt-2.5">
          {entry.dimensions.map((d) => (
            <li key={d.dimension}>
              <Badge>
                {d.dimension} · {to100(d.score)}
              </Badge>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/** Past interview history for the signed-in user (ledger rows). */
export default function HistoryPage() {
  const [entries, setEntries] = useState<HistoryEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiFetch<HistoryResponse>("/sessions/history?limit=50")
      .then((body) => {
        if (!cancelled) setEntries(body.sessions);
      })
      .catch((e) => {
        if (!cancelled) {
          setError(
            e instanceof ApiError
              ? `History failed: ${e.detail}`
              : "History failed to load.",
          );
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="space-y-6 pt-4">
      <div>
        <Breadcrumb trail={[{ label: "Account" }, { label: "History" }]} />
        <h1 className="mt-6 font-serif text-5xl font-semibold tracking-tight text-[#83DDDA]">
          Past sessions
        </h1>
      </div>
      {entries == null && !error && (
        <div className="flex justify-center py-12">
          <Spinner label="Loading history…" />
        </div>
      )}
      {error && (
        <p role="alert" className="rounded-none border border-red-500/30 bg-red-500/[0.08] px-4 py-3 font-mono text-xs text-[#f87171]">
          {error}
        </p>
      )}
      {entries != null && entries.length === 0 && (
        <div className="rounded-none border border-white/[0.08] bg-[#0E1223] p-5 text-center sm:p-6">
          <p className="font-serif text-[15px] text-[#8FA3A0]">No sessions yet.</p>
          <Link
            to="/setup"
            className="mt-3 inline-block rounded-none bg-[#E4621F] px-5 py-2.5 font-mono text-xs font-medium uppercase tracking-[0.14em] text-black transition-all duration-150 ease-out hover:brightness-110 focus-ring"
          >
            Start your first session →
          </Link>
        </div>
      )}
      {entries != null && entries.length > 0 && (
        <div className="space-y-3">
          {entries.map((e) => (
            <EntryCard key={e.session_id} entry={e} />
          ))}
        </div>
      )}
    </div>
  );
}
