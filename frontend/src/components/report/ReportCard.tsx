import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import type { InterviewApi } from "../../hooks/useInterview";
import type { EvaluationReport, SessionDetail } from "../../types/api";
import { buildReportMarkdown } from "../../lib/reportMarkdown";
import { Button, Spinner } from "../common/Primitives";
import Breadcrumb from "../common/Breadcrumb";
import ScoreBar from "./ScoreBar";

/* Backend scores 1–5; the reference sheet shows /100. Display decision
   (per SCREEN-SPECS.md): score/5*100, backend values untouched. */
const to100 = (score5: number): number =>
  Math.round((Math.max(0, Math.min(5, score5)) / 5) * 100);

function formatStamp(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso.toUpperCase();
  const date = d
    .toLocaleDateString("en-US", {
      month: "short",
      day: "2-digit",
      year: "numeric",
    })
    .toUpperCase();
  const time = d.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
  return `${date} ${time}`;
}

function Quadrant({
  n,
  title,
  count,
  children,
}: {
  n: string;
  title: string;
  count: number;
  children: React.ReactNode;
}) {
  return (
    <article className="rounded-none border border-white/[0.08] bg-[#0E1223] p-4">
      <div className="flex items-center justify-between border-b border-white/[0.08] pb-2.5 font-mono text-xs uppercase tracking-[0.18em] text-[#8FA3A0]">
        <span>
          [{n}] <span className="ml-2">{title}</span>
        </span>
        <span>({count})</span>
      </div>
      {children}
    </article>
  );
}

function QuadrantList({
  items,
  tone,
  empty,
}: {
  items: string[];
  tone: "teal" | "accent";
  empty: string;
}) {
  if (items.length === 0)
    return (
      <p className="mt-3 font-serif text-[15px] italic text-[#8FA3A0]">{empty}</p>
    );
  return (
    <ul className="mt-1 divide-y divide-white/[0.06]">
      {items.map((s, i) => (
        <li key={i} className="flex items-start gap-3 py-2.5">
          <span
            aria-hidden="true"
            className={`flex h-6 w-6 shrink-0 items-center justify-center border font-mono text-xs ${
              tone === "teal"
                ? "border-[#3AA99E] text-[#3AA99E]"
                : "border-[#E4621F] text-[#E4621F]"
            }`}
          >
            {i + 1}
          </span>
          <span className="font-mono text-xs leading-relaxed text-[#83DDDA]">
            {s}
          </span>
        </li>
      ))}
    </ul>
  );
}

interface CitedRow {
  key: string;
  code: string;
  text: string;
  dim: string;
}

/** Flatten real claim/evidence/turn refs (evidence first) across dimensions. */
function citedRows(report: EvaluationReport): CitedRow[] {
  const rows: CitedRow[] = [];
  for (const d of report.dimensions) {
    const push = (
      kind: "EV" | "CL" | "T",
      refs: { id: number; text: string }[],
    ) => {
      for (const r of refs) {
        rows.push({
          key: `${kind}-${r.id}-${d.dimension}`,
          code: `${kind}-${String(r.id).padStart(3, "0")}`,
          text: r.text,
          dim: d.dimension,
        });
      }
    };
    push("EV", d.refs.evidence);
    push("CL", d.refs.claims);
    push("T", d.refs.turns);
  }
  return rows;
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
      <div className="rounded-none border border-white/[0.08] bg-[#0E1223] p-6">
        <Spinner label="Scoring your session…" />
      </div>
    );
  }

  if (!report) {
    return (
      <div className="rounded-none border border-white/[0.08] bg-[#0E1223] p-5 sm:p-6">
        <div className="border border-white/[0.08] bg-black/30 px-4 py-8 text-center font-serif text-[15px] text-[#8FA3A0]">
          No report yet — finish an interview first.{" "}
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

  const overall5 =
    report.dimensions.length > 0
      ? report.dimensions.reduce((a, d) => a + d.score, 0) /
        report.dimensions.length
      : 0;
  const overall100 = to100(overall5);
  const sorted = [...report.dimensions].sort((a, b) => b.score - a.score);
  const top = sorted[0];
  const bottom = sorted[sorted.length - 1];
  const sessionTag = `SESSION-${String(report.session_id).padStart(3, "0")}`;

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

  const cites = citedRows(report);
  const shown = cites.slice(0, 12);

  return (
    <div className="space-y-6 pt-4">
      {/* header */}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <Breadcrumb
          trail={[{ label: "Evaluation report" }, { label: sessionTag }]}
        />
        {meta && (
          <p className="font-mono text-xs uppercase tracking-[0.18em] text-[#8FA3A0]">
            {formatStamp(meta.started_at)}
          </p>
        )}
      </div>

      <div className="grid items-start gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        {/* left: score hero + dimensions + evidence ledger */}
        <div>
          <h1 className="font-serif text-5xl font-semibold leading-[1.05] tracking-tight text-[#83DDDA] sm:text-6xl">
            Overall Score:{" "}
            <span className="tabular-nums">
              <span className="text-[#E4621F]">{overall100}</span>/100
            </span>
          </h1>
          {top && bottom && top !== bottom && (
            <p className="mt-4 max-w-xl font-serif text-lg leading-relaxed text-[#83DDDA]">
              Strongest in{" "}
              <em className="italic text-[#E4621F]">
                {top.dimension.toLowerCase()}
              </em>{" "}
              ({to100(top.score)}/100) — tighten{" "}
              <em className="italic text-[#E4621F]">
                {bottom.dimension.toLowerCase()}
              </em>{" "}
              ({to100(bottom.score)}/100) next.
            </p>
          )}

          <div className="mt-6 border-t border-dashed border-white/[0.2]" />

          <div className="mt-4 flex items-center justify-between font-mono text-xs uppercase tracking-[0.18em] text-[#8FA3A0]">
            <span>Dimension</span>
            <span>Score</span>
          </div>
          <ul className="mt-2 divide-y divide-white/[0.06] border-y border-white/[0.08]">
            {report.dimensions.map((d) => (
              <li
                key={d.dimension}
                className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)_auto] items-center gap-4 py-3"
              >
                <span className="font-serif text-lg text-[#83DDDA]">
                  {d.dimension}
                </span>
                <ScoreBar score={d.score} />
                <span className="font-mono text-sm tabular-nums text-[#83DDDA]">
                  {to100(d.score)} / 100
                </span>
              </li>
            ))}
          </ul>

          <div className="mt-8 flex items-center justify-between font-mono text-xs uppercase tracking-[0.18em] text-[#8FA3A0]">
            <span>Evidence citations</span>
            <span>From session</span>
          </div>
          {shown.length === 0 ? (
            <p className="mt-3 font-serif text-[15px] italic text-[#8FA3A0]">
              No cited passages recorded for this session.
            </p>
          ) : (
            <>
              <ol className="mt-2 divide-y divide-white/[0.06] border-y border-white/[0.08]">
                {shown.map((c, i) => (
                  <li
                    key={c.key}
                    className="flex items-baseline gap-3 py-2.5 font-mono text-xs"
                  >
                    <span
                      aria-hidden="true"
                      className="flex h-6 w-6 shrink-0 items-center justify-center border border-white/[0.2] text-[11px] text-[#83DDDA]"
                    >
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <span className="shrink-0 text-[#8FA3A0]">{c.code}</span>
                    <span className="min-w-0 flex-1 truncate text-[#83DDDA]">
                      {c.text}
                    </span>
                    <span className="hidden shrink-0 uppercase tracking-[0.14em] text-[#8FA3A0] sm:inline">
                      {c.dim}
                    </span>
                  </li>
                ))}
              </ol>
              {cites.length > shown.length && (
                <p className="mt-2 font-mono text-[11px] uppercase tracking-[0.14em] text-[#8FA3A0]">
                  +{cites.length - shown.length} more in the JSON export
                </p>
              )}
            </>
          )}
        </div>

        {/* right: quadrants + export */}
        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
            <Quadrant
              n="01"
              title="Strengths"
              count={report.strengths.length}
            >
              <QuadrantList
                items={report.strengths}
                tone="teal"
                empty="Nothing recorded."
              />
            </Quadrant>
            <Quadrant
              n="02"
              title="Improvements"
              count={report.weaknesses.length}
            >
              <QuadrantList
                items={report.weaknesses}
                tone="accent"
                empty="Nothing recorded."
              />
            </Quadrant>
            <Quadrant
              n="03"
              title="Vulnerable claims"
              count={report.hard_to_defend_claims.length}
            >
              <QuadrantList
                items={report.hard_to_defend_claims}
                tone="accent"
                empty="No shaky claims detected."
              />
            </Quadrant>
            <Quadrant
              n="04"
              title="Study topics"
              count={report.study_topics.length}
            >
              <QuadrantList
                items={report.study_topics}
                tone="teal"
                empty="Nothing assigned."
              />
            </Quadrant>
          </div>
          <Button
            variant="primary"
            onClick={downloadJson}
            className="w-full py-3.5 text-sm"
          >
            Export report →
          </Button>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" onClick={() => void copyMarkdown()}>
              {copied ? "Copied ✓" : "Copy Markdown"}
            </Button>
            <Button variant="secondary" onClick={practiceAgain}>
              Practice Again
            </Button>
            <Button variant="ghost" onClick={() => window.print()}>
              Print / PDF
            </Button>
          </div>
          <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-[#8FA3A0]">
            Rubric {report.rubric_version} · {report.claims_examined} claims
            examined
          </p>
        </div>
      </div>
    </div>
  );
}
