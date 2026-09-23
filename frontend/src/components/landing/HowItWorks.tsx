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

/** 3-step checklist rows with square number chips. */
export default function HowItWorks() {
  return (
    <section
      aria-label="How it works"
      className="rounded-none border border-white/[0.08] bg-[#0E1223] p-5 sm:p-6"
    >
      <p className="font-mono text-xs uppercase tracking-[0.18em] text-[#8FA3A0]">
        How it works
      </p>
      <ol className="mt-5 space-y-5">
        {steps.map((s) => (
          <li key={s.n} className="flex gap-4">
            <span
              aria-hidden="true"
              className="flex h-7 w-7 shrink-0 items-center justify-center border border-white/[0.2] font-mono text-xs text-[#83DDDA]"
            >
              {s.n}
            </span>
            <div className="min-w-0">
              <p className="font-serif text-lg font-medium text-[#83DDDA]">
                {s.title}{" "}
                <Link
                  to={s.to}
                  className="ml-1 rounded-none font-mono text-[11px] font-normal uppercase tracking-[0.14em] text-[#3AA99E] transition-colors duration-150 ease-out hover:text-[#83DDDA] focus-ring"
                >
                  {s.cta} →
                </Link>
              </p>
              <p className="mt-1 font-serif text-[15px] leading-relaxed text-[#8FA3A0]">
                {s.body}
              </p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
