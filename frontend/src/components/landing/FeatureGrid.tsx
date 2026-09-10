import { Badge } from "../common/Primitives";

const pillars = [
  {
    title: "Evidence-grounded probing",
    body: "Follow-ups target claims extracted from your resume — methodology, measurement, actual contribution. Vague answers get pushed, not nodded along.",
  },
  {
    title: "Voice & text realism",
    body: "Talk through the browser mic with silence-based turn-taking, or type when you prefer. Same interview engine underneath either way.",
  },
  {
    title: "Citations over vibes",
    body: "Every rubric score links to the exact turns, claims, and evidence behind it. Disagree with a score? Inspect what produced it.",
  },
  {
    title: "Local-first privacy",
    body: "Your files live in your own backend database. No account needed for guest mode, no tracking, nothing shipped to third parties.",
  },
];

/** T8: 4-pillar feature grid. */
export default function FeatureGrid() {
  return (
    <section aria-label="Features" className="grid gap-3 sm:grid-cols-2">
      {pillars.map((p) => (
        <div
          key={p.title}
          className="rounded-xl border border-white/[0.08] bg-zinc-900/60 p-5 shadow-xl"
        >
          <Badge tone="amber">{p.title}</Badge>
          <p className="mt-3 text-sm leading-relaxed text-neutral-300">{p.body}</p>
        </div>
      ))}
    </section>
  );
}
