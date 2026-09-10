import GlassCard from "./GlassCard";

export default function HeroCard({ onBegin }: { onBegin: () => void }) {
  return (
    <GlassCard className="overflow-hidden px-7 py-8 sm:px-10">
      <div className="flex items-start justify-between gap-6">
        <div className="max-w-xl">
          <p className="mb-3 inline-flex items-center gap-1.5 rounded-full border border-amber-500/20 bg-amber-500/10 px-2.5 py-0.5 text-xs font-medium tracking-[0.18em] text-amber-300">
            VOICE-FIRST · EVIDENCE-GROUNDED
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
            <button
              type="button"
              onClick={onBegin}
              className="rounded-lg bg-white px-4 py-2 text-sm font-medium text-zinc-950 shadow-sm transition-colors hover:bg-neutral-200"
            >
              Start setup
            </button>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-white/[0.08] bg-white/[0.06] px-2.5 py-0.5 text-xs font-medium text-neutral-300">
              single session · ~40 min
            </span>
          </div>
        </div>
        {/* carousel-dot motif from the reference mockup */}
        <div aria-hidden="true" className="hidden flex-col items-center gap-1.5 pt-2 sm:flex">
          <span className="h-1.5 w-1.5 rounded-full bg-white/25" />
          <span className="h-1.5 w-1.5 rounded-full bg-white" />
          <span className="h-1.5 w-1.5 rounded-full bg-white/25" />
        </div>
      </div>
    </GlassCard>
  );
}
