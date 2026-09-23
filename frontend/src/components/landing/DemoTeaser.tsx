import { Link } from "react-router-dom";
import { Badge } from "../common/Primitives";

const BAR_HEIGHTS = [
  8, 14, 22, 12, 26, 18, 30, 16, 24, 10, 28, 20, 12, 26, 18, 8, 22, 14, 28,
  18, 10, 24, 16, 30,
];

/** Mock preview of a live probe in transcript-ledger language — static illustration, not live audio. */
export default function DemoTeaser() {
  return (
    <section
      aria-label="Interview preview"
      className="rounded-none border border-white/[0.08] bg-[#0E1223] p-5 sm:p-6"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-[#8FA3A0]">
          Sample probe · illustration
        </p>
        <div className="flex flex-wrap items-center gap-1.5">
          <Badge tone="cyan" dot>
            PROBING_CLAIM
          </Badge>
          <Badge tone="amber">2 claims</Badge>
          <span className="font-mono text-xs tabular-nums text-[#8FA3A0]">
            12:47
          </span>
        </div>
      </div>

      <div className="mt-4 border-t border-white/[0.08] pt-4">
        <div className="flex gap-4">
          <span
            aria-hidden="true"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-[#3AA99E] font-serif text-sm font-semibold text-[#3AA99E]"
          >
            M
          </span>
          <div className="min-w-0">
            <p className="flex flex-wrap items-baseline gap-x-3">
              <span className="font-serif text-base font-semibold text-[#83DDDA]">
                Miki
              </span>
              <span className="font-mono text-[11px] tabular-nums text-[#8FA3A0]">
                00:00:12
              </span>
            </p>
            <p className="mt-1 font-serif text-[15px] leading-relaxed text-[#83DDDA]">
              You said checkout latency dropped 40%. Walk me through how you
              measured that — what was the baseline, and what else changed in
              the same deploy?
            </p>
          </div>
        </div>
      </div>

      <div
        aria-hidden="true"
        className="mt-4 flex h-12 items-center gap-1 overflow-hidden rounded-none border border-white/[0.08] bg-black/30 px-4"
      >
        {BAR_HEIGHTS.map((h, i) => (
          <span
            key={i}
            className={`demo-bar w-full rounded-full ${i === 15 ? "bg-[#E4621F]" : "bg-[#83DDDA]/70"}`}
            style={{ height: h, animationDelay: `${(i % 8) * 0.12}s` }}
          />
        ))}
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <p className="font-serif text-[15px] text-[#8FA3A0]">
          Your live session looks like this — voice or text, cited to your words.
        </p>
        <Link
          to="/setup"
          className="rounded-none bg-[#E4621F] px-5 py-2.5 font-mono text-xs font-medium uppercase tracking-[0.14em] text-black transition-colors duration-150 ease-out hover:bg-[#f07433] focus-ring"
        >
          Try it live →
        </Link>
      </div>
    </section>
  );
}
