/** Blueprint grid over canvas + frame lines with corner `+` registration marks. */
export default function AmbientBackground() {
  return (
    <div
      aria-hidden="true"
      className="blueprint-grid pointer-events-none fixed inset-0 bg-[#06090A]"
    >
      {/* frame lines */}
      <div className="absolute inset-y-0 left-4 w-px bg-white/[0.08] sm:left-6" />
      <div className="absolute inset-y-0 right-4 w-px bg-white/[0.08] sm:right-6" />
      {/* corner registration marks */}
      <span className="absolute left-4 top-3 -translate-x-1/2 font-mono text-sm text-[#83DDDA]/60 sm:left-6">
        +
      </span>
      <span className="absolute right-4 top-3 translate-x-1/2 font-mono text-sm text-[#83DDDA]/60 sm:right-6">
        +
      </span>
      <span className="absolute bottom-3 left-4 -translate-x-1/2 font-mono text-sm text-[#83DDDA]/60 sm:left-6">
        +
      </span>
      <span className="absolute bottom-3 right-4 translate-x-1/2 font-mono text-sm text-[#83DDDA]/60 sm:right-6">
        +
      </span>
    </div>
  );
}
