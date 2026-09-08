/** Ambient obsidian canvas: deep gradient + drifting orbs + grain. Decorative. */
export default function AmbientBackground() {
  return (
    <div aria-hidden="true" className="pointer-events-none fixed inset-0 overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(120%_90%_at_50%_0%,#101a30_0%,#060a14_55%,#04060c_100%)]" />
      {/* bronze orb, lower-left like the reference */}
      <div
        className="orb absolute -left-24 bottom-[-8rem] h-[26rem] w-[26rem] rounded-full opacity-60 blur-[70px] animate-[orb-drift_20s_ease-in-out_infinite]"
        style={{
          background:
            "radial-gradient(circle at 35% 30%, #6b5d4f 0%, #3a322b 38%, #141318 70%)",
        }}
      />
      {/* slate orb, top-center behind card */}
      <div
        className="orb absolute left-1/2 top-[-10rem] h-[22rem] w-[34rem] -translate-x-1/2 rounded-full opacity-50 blur-[80px] animate-[orb-drift_26s_ease-in-out_infinite]"
        style={{
          background:
            "radial-gradient(ellipse at 50% 40%, #3b4a68 0%, #1a2338 45%, transparent 75%)",
        }}
      />
      {/* indigo rim glow, right edge like the mockup */}
      <div
        className="orb absolute -right-28 top-1/3 h-[24rem] w-[24rem] rounded-full opacity-50 blur-[70px] animate-[orb-drift_23s_ease-in-out_infinite]"
        style={{
          background:
            "radial-gradient(circle at 40% 40%, #4a5a8a 0%, #232b4a 45%, transparent 72%)",
        }}
      />
      {/* cyan kiss of light, top-right */}
      <div
        className="absolute right-[12%] top-[6%] h-40 w-40 rounded-full opacity-25 blur-[60px]"
        style={{
          background: "radial-gradient(circle, #38bdf8 0%, transparent 70%)",
        }}
      />
      {/* film grain */}
      <svg className="absolute inset-0 h-full w-full opacity-[0.05]">
        <filter id="grain">
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" />
        </filter>
        <rect width="100%" height="100%" filter="url(#grain)" />
      </svg>
    </div>
  );
}
