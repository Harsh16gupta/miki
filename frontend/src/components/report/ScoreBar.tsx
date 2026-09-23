import type { ReportDimension } from "../../types/api";

/** Dimension bar: sage fill on dark track. Backend scores 1–5, displayed /100. */
export default function ScoreBar({ score }: { score: number }) {
  // Rubric scale is 1-5; clamp defensively.
  const pct = Math.max(0, Math.min(100, (score / 5) * 100));
  return (
    <div
      className="h-2 w-full min-w-24 overflow-hidden rounded-none bg-white/[0.06]"
      role="img"
      aria-label={`Score ${Math.round(pct)} out of 100`}
    >
      <div className="h-full rounded-none bg-[#83DDDA]" style={{ width: `${pct}%` }} />
    </div>
  );
}

export function EvidenceDrawer({ dim }: { dim: ReportDimension }) {
  const cites = [...dim.refs.claims, ...dim.refs.evidence, ...dim.refs.turns];
  if (cites.length === 0)
    return (
      <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-[#8FA3A0]">
        No cited evidence.
      </p>
    );
  return (
    <details className="group font-mono text-xs">
      <summary className="cursor-pointer uppercase tracking-[0.14em] text-[#3AA99E] transition-colors duration-150 ease-out hover:text-[#83DDDA] focus-ring">
        {cites.length} cited {cites.length === 1 ? "passage" : "passages"}
      </summary>
      <ul className="mt-2 space-y-1.5 border-l border-white/10 pl-3 normal-case tracking-normal text-[#8FA3A0]">
        {cites.slice(0, 8).map((c) => (
          <li key={`${dim.dimension}-${c.id}`}>
            <span className="text-[#E4621F]">#{c.id}</span> — {c.text}
          </li>
        ))}
      </ul>
    </details>
  );
}
