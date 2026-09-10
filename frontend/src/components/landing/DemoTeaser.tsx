import { Link } from "react-router-dom";
import { Badge } from "../common/Primitives";

const BAR_HEIGHTS = [
  8, 14, 22, 12, 26, 18, 30, 16, 24, 10, 28, 20, 12, 26, 18, 8, 22, 14, 28,
  18, 10, 24, 16, 30,
];

/** T7: mock preview of a live probe — static illustration, not live audio. */
export default function DemoTeaser() {
  return (
    <section
      aria-label="Interview preview"
      className="rounded-xl border border-white/[0.08] bg-zinc-900/60 p-5 shadow-xl sm:p-6"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs font-medium uppercase tracking-wider text-neutral-400">
          Sample probe · illustration
        </p>
        <div className="flex flex-wrap gap-1.5">
          <Badge tone="cyan" dot>
            PROBING_CLAIM
          </Badge>
          <Badge tone="amber">2 claims</Badge>
          <span className="font-mono text-xs tabular-nums text-zinc-500">
            12:47
          </span>
        </div>
      </div>

      <div className="mt-4 max-w-[85%] rounded-2xl border border-white/[0.08] bg-white/[0.06] px-3.5 py-2.5">
        <p className="mb-1 text-[10px] font-medium tracking-[0.16em] text-amber-300">
          MIKI
        </p>
        <p className="text-sm leading-relaxed text-zinc-50">
          You said checkout latency dropped 40%. Walk me through how you
          measured that — what was the baseline, and what else changed in the
          same deploy?
        </p>
      </div>

      <div
        aria-hidden="true"
        className="mt-4 flex h-12 items-center gap-1 overflow-hidden rounded-xl border border-white/[0.08] bg-black/30 px-4"
      >
        {BAR_HEIGHTS.map((h, i) => (
          <span
            key={i}
            className="demo-bar w-full rounded-full bg-cyan-500/70"
            style={{ height: h, animationDelay: `${(i % 8) * 0.12}s` }}
          />
        ))}
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-zinc-500">
          Your live session looks like this — voice or text, cited to your words.
        </p>
        <Link
          to="/setup"
          className="rounded-lg bg-white px-4 py-2 text-sm font-medium text-zinc-950 shadow-sm transition-colors hover:bg-neutral-200 focus-ring"
        >
          Try it live
        </Link>
      </div>
    </section>
  );
}
