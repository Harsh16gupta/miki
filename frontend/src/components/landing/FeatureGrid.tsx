const pillars = [
  {
    n: "01",
    title: "Evidence-grounded probing",
    body: "Follow-ups target claims extracted from your resume — methodology, measurement, actual contribution. Vague answers get pushed, not nodded along.",
  },
  {
    n: "02",
    title: "Voice & text realism",
    body: "Talk through the browser mic with silence-based turn-taking, or type when you prefer. Same interview engine underneath either way.",
  },
  {
    n: "03",
    title: "Citations over vibes",
    body: "Every rubric score links to the exact turns, claims, and evidence behind it. Disagree with a score? Inspect what produced it.",
  },
  {
    n: "04",
    title: "Local-first privacy",
    body: "Your files live in your own backend database. No account needed for guest mode, no tracking, nothing shipped to third parties.",
  },
];

/** 2×2 quadrant cards in the report-ledger language. */
export default function FeatureGrid() {
  return (
    <section aria-label="Why Miki" className="grid gap-4 sm:grid-cols-2">
      {pillars.map((p) => (
        <article
          key={p.n}
          className="rounded-none border border-white/[0.08] bg-[#0E1223] p-5"
        >
          <div className="flex items-center justify-between border-b border-white/[0.08] pb-3 font-mono text-xs uppercase tracking-[0.18em] text-[#8FA3A0]">
            <span>[{p.n}]</span>
          </div>
          <h2 className="mt-4 font-serif text-xl font-medium text-[#83DDDA]">
            {p.title}
          </h2>
          <p className="mt-2 font-serif text-[15px] leading-relaxed text-[#8FA3A0]">
            {p.body}
          </p>
        </article>
      ))}
    </section>
  );
}
