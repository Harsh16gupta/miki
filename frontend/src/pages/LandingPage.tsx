import { Link } from "react-router-dom";
import { Card } from "../components/common/Primitives";

/** Minimal landing (Wave 3 builds the full showcase per Tasks 6–10). */
export default function LandingPage() {
  return (
    <div className="space-y-4">
      <Card className="px-7 py-8 sm:px-10">
        <p className="mb-3 inline-flex items-center gap-1.5 rounded-full border border-cyan-500/20 bg-cyan-500/10 px-2.5 py-0.5 text-xs font-medium tracking-widest text-cyan-400">
          EVIDENCE-GROUNDED TRAINER
        </p>
        <h1 className="text-2xl font-semibold tracking-tight text-white sm:text-3xl">
          Interview trainer
          <br />
          that cites evidence.
        </h1>
        <p className="mt-4 max-w-md text-sm leading-relaxed text-neutral-300">
          Upload your resume and a job description. Miki probes your claims,
          follows up like a real interviewer, then scores you with cited
          evidence — not vibes.
        </p>
        <div className="mt-6 flex flex-wrap items-center gap-3">
          <Link
            to="/setup"
            className="rounded-lg bg-white px-4 py-2 text-sm font-medium text-zinc-950 shadow-sm transition-colors hover:bg-neutral-200 focus-ring"
          >
            Start Practice Session
          </Link>
          <Link
            to="/login"
            className="rounded-lg border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-neutral-200 transition-colors hover:bg-white/[0.08] hover:text-white focus-ring"
          >
            Sign In
          </Link>
        </div>
      </Card>
    </div>
  );
}
