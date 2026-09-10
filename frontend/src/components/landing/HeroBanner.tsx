import { Link } from "react-router-dom";
import { Badge } from "../common/Primitives";

/** T6: hero banner — tight-tracked headline, value badge, dual CTA. */
export default function HeroBanner() {
  return (
    <section className="rounded-xl border border-white/[0.08] bg-zinc-900/60 p-5 shadow-xl sm:p-10">
      <Badge tone="cyan">VOICE-FIRST · EVIDENCE-GROUNDED</Badge>
      <h1 className="mt-4 max-w-2xl text-2xl font-semibold tracking-tight text-white sm:text-4xl">
        Defend your resume claims in a live voice interview.
      </h1>
      <p className="mt-3 max-w-xl text-sm leading-relaxed text-neutral-300 sm:text-base">
        Miki uploads your resume and the job description, probes your claims
        like a real interviewer, and scores you against a hand-written rubric —
        every score cited to something you actually said.
      </p>
      <div className="mt-6 flex flex-wrap items-center gap-3">
        <Link
          to="/setup"
          className="rounded-lg bg-white px-4 py-2 text-sm font-medium text-zinc-950 shadow-sm transition-colors hover:bg-neutral-200 focus-ring"
        >
          Start Practice Session
        </Link>
        <Link
          to="/interview"
          className="rounded-lg border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-neutral-200 transition-colors hover:bg-white/[0.08] hover:text-white focus-ring"
        >
          How it works
        </Link>
      </div>
      <p className="mt-4 font-mono text-xs tabular-nums text-zinc-500">
        ~40 min per session · guest mode, no account needed
      </p>
    </section>
  );
}
