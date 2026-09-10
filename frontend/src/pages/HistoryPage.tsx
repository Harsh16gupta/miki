import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Spinner } from "../components/common/Primitives";
import { apiFetch, ApiError } from "../lib/api";
import type { HistoryEntry, HistoryResponse } from "../types/api";

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}

function formatDuration(totalS: number | null): string {
  if (totalS == null) return "—";
  const m = Math.floor(totalS / 60);
  return m > 0 ? `${m}m ${totalS % 60}s` : `${totalS}s`;
}

function EntryCard({ entry }: { entry: HistoryEntry }) {
  return (
    <div className="rounded-xl border border-white/[0.08] bg-black/30 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-medium text-zinc-50">
          Session #{entry.session_id}
          <span className="ml-2 font-mono text-xs tabular-nums text-zinc-500">
            {formatDate(entry.started_at)} · {formatDuration(entry.duration_s)}
          </span>
        </p>
        <div className="flex items-center gap-1.5">
          <Badge tone={entry.status === "completed" ? "success" : "default"}>
            {entry.status}
          </Badge>
          {entry.overall_score != null && (
            <Badge tone="amber">{entry.overall_score.toFixed(1)} / 5</Badge>
          )}
        </div>
      </div>
      {entry.dimensions.length > 0 && (
        <ul className="mt-2 flex flex-wrap gap-1.5">
          {entry.dimensions.map((d) => (
            <li key={d.dimension}>
              <Badge>
                {d.dimension} · {d.score.toFixed(1)}
              </Badge>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/** T36: past interview history for the signed-in user. */
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
    <div className="space-y-4">
      <div>
        <p className="text-xs font-medium uppercase tracking-wider text-neutral-400">
          Account · History
        </p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight text-white sm:text-3xl">
          Past sessions
        </h1>
      </div>
      {entries == null && !error && (
        <div className="flex justify-center py-12">
          <Spinner label="Loading history…" />
        </div>
      )}
      {error && (
        <p role="alert" className="rounded-xl border border-red-500/30 bg-red-500/[0.08] px-4 py-3 text-sm text-red-400">
          {error}
        </p>
      )}
      {entries != null && entries.length === 0 && (
        <div className="rounded-xl border border-white/[0.08] bg-zinc-900/60 p-5 text-center shadow-xl sm:p-6">
          <p className="text-sm text-zinc-400">No sessions yet.</p>
          <Link
            to="/setup"
            className="mt-3 inline-block rounded-lg bg-white px-4 py-2 text-sm font-medium text-zinc-950 shadow-sm transition-colors hover:bg-neutral-200 focus-ring"
          >
            Start your first session
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
