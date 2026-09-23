import { useEffect, useRef } from "react";
import { readLevels } from "../../lib/audioAnalyser";
import { cn } from "../../lib/cn";

const BARS = 32;
/* One accent bar among the sage — matches the composer in image 04. */
const ACCENT_BAR = 21;

const TONES = {
  sage: "131,221,218",
  teal: "58,169,158",
} as const;

/** Live frequency-bar visualizer driven by an AnalyserNode. Flat when idle. */
export default function Waveform({
  getAnalyser,
  active,
  tone = "sage",
  label,
}: {
  getAnalyser: () => AnalyserNode | null;
  active: boolean;
  tone?: keyof typeof TONES;
  label: string;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const stateRef = useRef({ getAnalyser, active });

  useEffect(() => {
    stateRef.current = { getAnalyser, active };
  });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    let raf = 0;
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    const draw = () => {
      raf = requestAnimationFrame(draw);
      const { getAnalyser: get, active: isActive } = stateRef.current;
      const w = canvas.clientWidth * dpr;
      const h = canvas.clientHeight * dpr;
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w;
        canvas.height = h;
      }
      ctx.clearRect(0, 0, w, h);
      const levels = isActive ? readLevels(get(), BARS) : new Array(BARS).fill(0.06);
      const gap = w / BARS;
      const barW = Math.max(1, gap * 0.5);
      for (let i = 0; i < BARS; i++) {
        const v = levels[i];
        const barH = Math.max(2 * dpr, v * h * 0.92);
        const x = i * gap + (gap - barW) / 2;
        const y = (h - barH) / 2;
        const color = i === ACCENT_BAR ? "228,98,31" : TONES[tone];
        ctx.fillStyle = `rgba(${color},${0.3 + v * 0.6})`;
        if (typeof ctx.roundRect === "function") {
          ctx.beginPath();
          ctx.roundRect(x, y, barW, barH, barW / 2);
          ctx.fill();
        } else {
          ctx.fillRect(x, y, barW, barH);
        }
      }
    };
    draw();
    return () => cancelAnimationFrame(raf);
  }, [tone]);

  return (
    <div
      role="img"
      aria-label={label}
      className={cn(!active && "opacity-70")}
    >
      <canvas ref={canvasRef} className="h-10 w-full" />
    </div>
  );
}
