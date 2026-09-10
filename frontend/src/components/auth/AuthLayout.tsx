import { Link } from "react-router-dom";
import type { ReactNode } from "react";

/** T32: centered auth shell — subtle grid backdrop, brand, back-to-home. */
export default function AuthLayout({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <div className="relative mx-auto w-full max-w-md py-8">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 opacity-40 [background-image:linear-gradient(rgba(255,255,255,0.04)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.04)_1px,transparent_1px)] [background-size:24px_24px] [mask-image:radial-gradient(ellipse_at_center,black_30%,transparent_75%)]"
      />
      <div className="relative rounded-xl border border-white/[0.08] bg-zinc-900/60 p-5 shadow-xl sm:p-8">
        <Link
          to="/"
          className="flex items-center gap-2.5 rounded-lg focus-ring"
          aria-label="Back to home"
        >
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-white text-sm font-bold text-zinc-950">
            M
          </span>
          <span className="text-sm font-semibold tracking-tight text-zinc-50">
            Miki
          </span>
        </Link>
        <h1 className="mt-5 text-lg font-medium tracking-tight text-white sm:text-xl">
          {title}
        </h1>
        <p className="mt-1 text-sm leading-relaxed text-neutral-300">{subtitle}</p>
        <div className="mt-5">{children}</div>
        <Link
          to="/"
          className="mt-5 inline-block rounded-lg text-sm text-neutral-400 transition-colors hover:text-white focus-ring"
        >
          ← Back to Home
        </Link>
      </div>
    </div>
  );
}
