import { Badge } from "../common/Primitives";

function ChipList({ items, tone }: { items: string[]; tone: "amber" | "cyan" | "default" }) {
  if (items.length === 0) return null;
  return (
    <ul className="mt-2 flex flex-wrap gap-1.5">
      {items.slice(0, 12).map((s, i) => (
        <li key={i}>
          <Badge tone={tone}>{s}</Badge>
        </li>
      ))}
      {items.length > 12 && <Badge tone="default">+{items.length - 12} more</Badge>}
    </ul>
  );
}

/** Collapsible inspection panel over parsed claims + required skills (mono chips). */
export default function ClaimsPreview({
  candClaimsList,
  candSkills,
  roleSkillsList,
}: {
  candClaimsList: string[];
  candSkills: string[];
  roleSkillsList: string[];
}) {
  const empty =
    candClaimsList.length === 0 &&
    candSkills.length === 0 &&
    roleSkillsList.length === 0;
  if (empty) return null;
  return (
    <details className="group rounded-none border border-white/[0.08] bg-[#0E1223] p-4">
      <summary className="cursor-pointer font-mono text-xs uppercase tracking-[0.18em] text-[#83DDDA] focus-ring">
        Inspect extracted claims & skills
        <span className="ml-2 tabular-nums text-[#8FA3A0]">
          {candClaimsList.length} claims · {roleSkillsList.length} required skills
        </span>
      </summary>
      <div className="mt-3 space-y-3">
        {candClaimsList.length > 0 && (
          <div>
            <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-[#8FA3A0]">
              Resume claims
            </p>
            <ChipList items={candClaimsList} tone="amber" />
          </div>
        )}
        {candSkills.length > 0 && (
          <div>
            <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-[#8FA3A0]">
              Candidate skills
            </p>
            <ChipList items={candSkills} tone="default" />
          </div>
        )}
        {roleSkillsList.length > 0 && (
          <div>
            <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-[#8FA3A0]">
              Required skills
            </p>
            <ChipList items={roleSkillsList} tone="cyan" />
          </div>
        )}
      </div>
    </details>
  );
}
