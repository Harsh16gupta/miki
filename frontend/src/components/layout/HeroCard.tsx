import GlassCard from "./GlassCard";

export default function HeroCard({ onBegin }: { onBegin: () => void }) {
  return (
    <GlassCard className="overflow-hidden px-7 py-8 sm:px-10">
      <div className="flex items-start justify-between gap-6">
        <div className="max-w-xl">
          <p className="mb-3 inline-flex items-center gap-2 rounded-full border border-[#d6c7a5]/30 bg-[#d6c7a5]/5 px-3 py-1 text-[11px] tracking-[0.18em] text-[#d6c7a5]">
            VOICE-FIRST · EVIDENCE-GROUNDED
          </p>
          <h1 className="text-3xl font-bold leading-tight text-white sm:text-4xl">
            Glass
            <br />
            Interview
          </h1>
          <p className="mt-2 text-lg text-[#a8a29e]">trainer.</p>
          <p className="mt-4 max-w-md text-sm leading-relaxed text-[#a8a29e]">
            Upload your resume and a job description. Miki probes your claims,
            follows up like a real interviewer, then scores you with cited
            evidence — not vibes.
          </p>
          <div className="mt-6 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={onBegin}
              className="rounded-full bg-[#f5f3ee] px-5 py-2.5 text-sm font-semibold text-[#0b1120] transition hover:bg-white"
            >
              Start setup
            </button>
            <span className="gold-pill rounded-full px-3 py-1 text-[11px]">
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
