import { Link } from "react-router-dom";
import type { ReactNode } from "react";
import { Stamp } from "../common/Primitives";

/** Centered auth shell: stamp header, serif title, form-panel treatment. */
export default function AuthLayout({
  title,
  subtitle,
  children,
  stamp,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
  stamp?: string;
}) {
  return (
    <div className="relative mx-auto w-full max-w-md py-8">
      <div className="panel-hard p-6 sm:p-8">
        <div className="flex items-center justify-between gap-3">
          <Link
            to="/"
            className="rounded-none font-serif text-3xl font-semibold tracking-tight text-[#83DDDA] focus-ring"
            aria-label="Back to home"
          >
            Miki
          </Link>
          <Stamp tone="teal">{stamp ?? "Account"}</Stamp>
        </div>
        <h1 className="mt-6 font-serif text-3xl font-semibold tracking-tight text-[#83DDDA]">
          {title}
        </h1>
        <p className="mt-2 font-serif text-[15px] leading-relaxed text-[#8FA3A0]">
          {subtitle}
        </p>
        <div className="mt-6">{children}</div>
        <Link
          to="/"
          className="mt-6 inline-block rounded-none font-mono text-[11px] uppercase tracking-[0.14em] text-[#8FA3A0] transition-colors duration-150 ease-out hover:text-[#83DDDA] focus-ring"
        >
          ← Back to home
        </Link>
      </div>
    </div>
  );
}
