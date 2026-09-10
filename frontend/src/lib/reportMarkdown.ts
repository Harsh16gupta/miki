import type { EvaluationReport } from "../types/api";

/** T26: Markdown summary builder for clipboard export. */
export function buildReportMarkdown(rep: EvaluationReport): string {
  const overall =
    rep.dimensions.length > 0
      ? rep.dimensions.reduce((a, d) => a + d.score, 0) / rep.dimensions.length
      : 0;
  const lines: string[] = [
    `# Miki Interview Report — session ${rep.session_id}`,
    ``,
    `Overall readiness: ${overall.toFixed(1)} / 5 · rubric ${rep.rubric_version} · policy ${rep.policy_version}`,
    ``,
    `## Dimension scores`,
  ];
  for (const d of rep.dimensions) {
    lines.push(`- ${d.dimension}: ${d.score.toFixed(1)} / 5`);
  }
  const section = (title: string, items: string[]) => {
    lines.push(``, `## ${title}`);
    if (items.length === 0) lines.push(`- (none recorded)`);
    for (const s of items) lines.push(`- ${s}`);
  };
  section("Strengths", rep.strengths);
  section("Areas for improvement", rep.weaknesses);
  section("Vulnerable claims", rep.hard_to_defend_claims);
  section("Recommended study topics", rep.study_topics);
  return lines.join("\n");
}
