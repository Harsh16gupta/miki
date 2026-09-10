import { useEffect, useRef } from "react";
import { readLevels } from "../../lib/audioAnalyser";
import { cn } from "../../lib/cn";

const BARS = 32;

/** T19: live frequency-bar visualizer driven by an AnalyserNode. */
export default function Waveform({
  getAnalyser,
  active,
  tone = "cyan",
  label,
}: {
  getAnalyser: () => AnalyserNode | null;
  active: boolean;
  tone?: "cyan" | "emerald";
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
      const levels = isActive ? readLevels(get(), BARS) : new Array(BARS).fill(0);
      const gap = w / BARS;
      const barW = Math.max(1, gap * 0.55);
      const color = tone === "cyan" ? "34,211,238" : "16,185,129";
      for (let i = 0; i < BARS; i++) {
        const v = levels[i];
        const barH = Math.max(2 * dpr, v * h * 0.92);
        const x = i * gap + (gap - barW) / 2;
        const y = (h - barH) / 2;
        ctx.fillStyle = `rgba(${color},${0.25 + v * 0.65})`;
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
      className={cn(
        "overflow-hidden rounded-xl border border-white/[0.08] bg-black/30",
        !active && "opacity-60",
      )}
    >
      <canvas ref={canvasRef} className="h-14 w-full" />
    </div>
  );
}
