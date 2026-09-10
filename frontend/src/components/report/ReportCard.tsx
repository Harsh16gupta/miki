import { useState } from "react";
import { useNavigate } from "react-router-dom";
import type { InterviewApi } from "../../hooks/useInterview";
import type { SessionDetail } from "../../types/api";
import { buildReportMarkdown } from "../../lib/reportMarkdown";
import GlassCard from "../layout/GlassCard";
import { Button, PillBadge, Spinner } from "../common/Primitives";
import ScoreBar, { EvidenceDrawer } from "./ScoreBar";

function BulletList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-xl border border-white/[0.08] bg-black/30 p-4">
      <h4 className="mb-2 text-xs font-medium uppercase tracking-wider text-amber-300">
        {title.toUpperCase()}
      </h4>
      {items.length === 0 ? (
        <p className="text-sm text-zinc-400">Nothing recorded.</p>
      ) : (
        <ul className="list-disc space-y-1.5 pl-5 text-sm leading-relaxed text-zinc-300">
          {items.map((s, i) => (
            <li key={i}>{s}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

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
  const s = totalS % 60;
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

export default function ReportCard({
  interview,
  meta,
}: {
  interview: InterviewApi;
  meta?: SessionDetail | null;
}) {
  const { report, status } = interview;
  const navigate = useNavigate();
  const [copied, setCopied] = useState(false);

  if (status === "scoring") {
    return (
      <GlassCard className="px-6 py-6 sm:px-8">
        <Spinner label="Scoring your session…" />
      </GlassCard>
    );
  }

  if (!report) return null;

  const overall =
    report.dimensions.length > 0
      ? report.dimensions.reduce((a, d) => a + d.score, 0) / report.dimensions.length
      : 0;

  const copyMarkdown = async () => {
    try {
      await navigator.clipboard.writeText(buildReportMarkdown(report));
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      interview.toast("Copy failed — clipboard unavailable.");
    }
  };

  const downloadJson = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `miki-report-session-${report.session_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const practiceAgain = () => {
    interview.reset();
    navigate("/setup");
  };

  return (
    <GlassCard className="px-6 py-6 sm:px-8">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-medium tracking-tight text-white sm:text-xl">
          <span className="mr-2 font-mono text-xs text-amber-300">03</span> Report
        </h2>
        <div className="flex flex-wrap gap-1.5">
          <PillBadge tone="gold">rubric {report.rubric_version}</PillBadge>
          <PillBadge>{report.claims_examined} claims examined</PillBadge>
        </div>
      </div>

      {/* T22: executive summary header */}
      <div className="mt-4 grid gap-3 sm:grid-cols-4">
        <div className="rounded-xl border border-white/[0.08] bg-black/30 p-4">
          <p className="text-xs font-medium uppercase tracking-wider text-neutral-400">
            Overall readiness
          </p>
          <p className="mt-1 text-2xl font-semibold tabular-nums text-white">
            {overall.toFixed(1)}
            <span className="text-sm font-normal text-zinc-500"> / 5</span>
          </p>
        </div>
        <div className="rounded-xl border border-white/[0.08] bg-black/30 p-4">
          <p className="text-xs font-medium uppercase tracking-wider text-neutral-400">
            Session date
          </p>
          <p className="mt-1 text-sm text-zinc-200">
            {meta ? formatDate(meta.started_at) : "—"}
          </p>
        </div>
        <div className="rounded-xl border border-white/[0.08] bg-black/30 p-4">
          <p className="text-xs font-medium uppercase tracking-wider text-neutral-400">
            Duration
          </p>
          <p className="mt-1 font-mono text-sm tabular-nums text-zinc-200">
            {meta ? formatDuration(meta.duration_s) : "—"}
          </p>
        </div>
        <div className="rounded-xl border border-white/[0.08] bg-black/30 p-4">
          <p className="text-xs font-medium uppercase tracking-wider text-neutral-400">
            Rubric
          </p>
          <p className="mt-1 font-mono text-sm text-zinc-200">
            {report.rubric_version}
          </p>
        </div>
      </div>

      <div className="mt-4 overflow-hidden rounded-xl border border-white/[0.08]">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-white/[0.08] bg-white/[0.04] text-[11px] tracking-[0.14em] text-zinc-400">
              <th className="px-4 py-2.5 font-medium">DIMENSION</th>
              <th className="px-4 py-2.5 font-medium">SCORE</th>
              <th className="hidden px-4 py-2.5 font-medium sm:table-cell">
                EVIDENCE
              </th>
            </tr>
          </thead>
          <tbody>
            {report.dimensions.map((d) => (
              <tr
                key={d.dimension}
                className="border-b border-white/5 last:border-0"
              >
                <td className="px-4 py-3 font-medium text-white">
                  {d.dimension}
                </td>
                <td className="px-4 py-3">
                  <span className="flex items-center gap-2">
                    <span className="font-mono text-xs tabular-nums text-zinc-50">{d.score.toFixed(1)}</span>
                    <ScoreBar score={d.score} />
                  </span>
                </td>
                <td className="hidden px-4 py-3 sm:table-cell">
                  <EvidenceDrawer dim={d} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* evidence for small screens */}
      <div className="mt-3 space-y-3 sm:hidden">
        {report.dimensions.map((d) => (
          <div
            key={d.dimension}
            className="rounded-xl border border-white/[0.08] bg-black/30 p-3"
          >
            <p className="mb-1.5 text-xs font-medium text-white">
              {d.dimension}
            </p>
            <EvidenceDrawer dim={d} />
          </div>
        ))}
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <BulletList title="Strengths" items={report.strengths} />
        <BulletList title="Weaknesses" items={report.weaknesses} />
        <BulletList
          title="Hard to defend"
          items={report.hard_to_defend_claims}
        />
        <BulletList title="Study next" items={report.study_topics} />
      </div>

      {/* T26: action bar — client-side export suite */}
      <div className="mt-5 flex flex-wrap items-center gap-2 border-t border-white/[0.08] pt-4">
        <Button variant="primary" onClick={practiceAgain}>
          Practice Again
        </Button>
        <Button variant="secondary" onClick={() => void copyMarkdown()}>
          {copied ? "Copied ✓" : "Copy Markdown Summary"}
        </Button>
        <Button variant="secondary" onClick={downloadJson}>
          Export JSON
        </Button>
        <Button variant="ghost" onClick={() => window.print()}>
          Print / PDF
        </Button>
      </div>
    </GlassCard>
  );
}
