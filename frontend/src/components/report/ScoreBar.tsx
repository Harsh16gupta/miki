import type { ReportDimension } from "../../types/api";

export default function ScoreBar({ score }: { score: number }) {
  // Rubric scale is 1-5; clamp defensively.
  const pct = Math.max(0, Math.min(100, ((score - 1) / 4) * 100));
  return (
    <div
      className="h-1.5 w-28 overflow-hidden rounded-full bg-white/10"
      role="img"
      aria-label={`Score ${score} out of 5`}
    >
      <div
        className="h-full rounded-full bg-zinc-100"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

export function EvidenceDrawer({ dim }: { dim: ReportDimension }) {
  const cites = [...dim.refs.claims, ...dim.refs.evidence, ...dim.refs.turns];
  if (cites.length === 0)
    return <p className="text-xs text-zinc-400">No cited evidence.</p>;
  return (
    <details className="group text-xs">
      <summary className="cursor-pointer text-cyan-300 hover:text-white focus-ring">
        {cites.length} cited {cites.length === 1 ? "passage" : "passages"}
      </summary>
      <ul className="mt-2 space-y-1.5 border-l border-white/10 pl-3 text-zinc-400">
        {cites.slice(0, 8).map((c) => (
          <li key={`${dim.dimension}-${c.id}`}>
            <span className="font-mono text-amber-300">#{c.id}</span> — {c.text}
          </li>
        ))}
      </ul>
    </details>
  );
}
