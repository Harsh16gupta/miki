import type { InterviewApi } from "../../hooks/useInterview";
import GlassCard from "../layout/GlassCard";
import { PillBadge, Spinner } from "../common/Primitives";
import ScoreBar, { EvidenceDrawer } from "./ScoreBar";

function BulletList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
      <h4 className="mb-2 text-xs font-semibold tracking-[0.16em] text-[#d6c7a5]">
        {title.toUpperCase()}
      </h4>
      {items.length === 0 ? (
        <p className="text-sm text-[#a8a29e]">Nothing recorded.</p>
      ) : (
        <ul className="list-disc space-y-1.5 pl-5 text-sm text-[#f5f3ee]/90">
          {items.map((s, i) => (
            <li key={i}>{s}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function ReportCard({ interview }: { interview: InterviewApi }) {
  const { report, status } = interview;

  if (status === "scoring") {
    return (
      <GlassCard className="px-6 py-6 sm:px-8">
        <Spinner label="Scoring your session…" />
      </GlassCard>
    );
  }

  if (!report) return null;

  return (
    <GlassCard className="px-6 py-6 sm:px-8">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-base font-semibold text-white">
          <span className="mr-2 text-[#d6c7a5]">03</span> Report
        </h2>
        <div className="flex flex-wrap gap-1.5">
          <PillBadge tone="gold">rubric {report.rubric_version}</PillBadge>
          <PillBadge>{report.claims_examined} claims examined</PillBadge>
        </div>
      </div>

      <div className="mt-4 overflow-hidden rounded-2xl border border-white/10">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-white/10 bg-white/[0.04] text-[11px] tracking-[0.14em] text-[#a8a29e]">
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
                    <span className="text-[#e5c878]">{d.score.toFixed(1)}</span>
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
            className="rounded-2xl border border-white/10 bg-black/20 p-3"
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
    </GlassCard>
  );
}
