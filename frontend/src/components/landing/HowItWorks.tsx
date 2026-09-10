import { Link } from "react-router-dom";

const steps = [
  {
    n: "1",
    title: "Upload resume & JD",
    body: "Drop two files. Miki structures your claims and the role's required skills in seconds.",
    to: "/setup",
    cta: "Go to Setup",
  },
  {
    n: "2",
    title: "Defend claims in the voice arena",
    body: "Answer by voice or text while the state machine probes, follows up, and escalates difficulty.",
    to: "/interview",
    cta: "See the Arena",
  },
  {
    n: "3",
    title: "Receive your rubric scorecard",
    body: "Five hand-written dimensions, every score cited to your own words, plus what to study next.",
    to: "/report",
    cta: "See a Report",
  },
];

/** T9: 3-step visual timeline with route links. */
export default function HowItWorks() {
  return (
    <section
      aria-label="How it works"
      className="rounded-xl border border-white/[0.08] bg-zinc-900/60 p-5 shadow-xl sm:p-6"
    >
      <p className="text-xs font-medium uppercase tracking-wider text-neutral-400">
        How it works
      </p>
      <ol className="mt-4 space-y-4">
        {steps.map((s) => (
          <li key={s.n} className="flex gap-3">
            <span
              aria-hidden="true"
              className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border border-white/10 bg-white/[0.03] font-mono text-xs text-amber-300"
            >
              {s.n}
            </span>
            <div className="min-w-0">
              <p className="text-sm font-medium text-zinc-50">
                {s.title}{" "}
                <Link
                  to={s.to}
                  className="ml-1 text-xs font-normal text-cyan-300 hover:text-white focus-ring"
                >
                  {s.cta} →
                </Link>
              </p>
              <p className="mt-1 text-sm leading-relaxed text-neutral-300">
                {s.body}
              </p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
