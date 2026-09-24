import { useEffect, useRef } from "react";
import { readLevels } from "../../lib/audioAnalyser";
import { cn } from "../../lib/cn";

const BARS = 32;
/* One accent bar among the base bars — matches the composer in image 04. */
const ACCENT_BAR = 21;

/* Dark fallbacks (identical to previous constants); light values come from
   `light-theme.css` vars so the dark file stays untouched. */
const FALLBACK = {
  sage: "131,221,218",
  teal: "58,169,158",
  accent: "228,98,31",
} as const;

type Tone = "sage" | "teal";

/** Live frequency-bar visualizer driven by an AnalyserNode. Flat when idle. */
export default function Waveform({
  getAnalyser,
  active,
  tone = "sage",
  label,
}: {
  getAnalyser: () => AnalyserNode | null;
  active: boolean;
  tone?: Tone;
  label: string;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const stateRef = useRef({ getAnalyser, active });
  const colorsRef = useRef<{ sage: string; teal: string; accent: string }>({
    ...FALLBACK,
  });

  useEffect(() => {
    stateRef.current = { getAnalyser, active };
  });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Bar colors follow the theme via CSS vars (dark fallbacks = old values).
    const refresh = () => {
      const cs = getComputedStyle(canvas);
      colorsRef.current = {
        sage: cs.getPropertyValue("--wave-sage").trim() || FALLBACK.sage,
        teal: cs.getPropertyValue("--wave-teal").trim() || FALLBACK.teal,
        accent:
          cs.getPropertyValue("--wave-accent").trim() || FALLBACK.accent,
      };
    };

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    refresh();
    const observer = new MutationObserver(refresh);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class"],
    });

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
      const palette = colorsRef.current;
      for (let i = 0; i < BARS; i++) {
        const v = levels[i];
        const barH = Math.max(2 * dpr, v * h * 0.92);
        const x = i * gap + (gap - barW) / 2;
        const y = (h - barH) / 2;
        const color = i === ACCENT_BAR ? palette.accent : palette[tone];
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
    return () => {
      cancelAnimationFrame(raf);
      observer.disconnect();
    };
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
