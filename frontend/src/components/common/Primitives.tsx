import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";
import { cn } from "../../lib/cn";

/* ---- Button (DESIGN.md §5) ----
   primary: solid accent, black text, mono uppercase + arrow (one per viewport).
   secondary: 1px sage outline. ghost: quiet. danger: errors only.
   Prop signature unchanged so callers don't break. */
type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

const buttonStyles: Record<ButtonVariant, string> = {
  primary:
    "bg-[#E4621F] text-black hover:brightness-110 font-mono font-medium uppercase tracking-[0.14em] px-5 py-2.5 rounded-sm text-xs transition-colors duration-150 ease-out disabled:opacity-50 disabled:pointer-events-none",
  secondary:
    "border border-[#83DDDA]/60 bg-transparent text-[#83DDDA] hover:bg-[#83DDDA]/10 hover:border-[#83DDDA] font-mono uppercase tracking-[0.14em] px-5 py-2.5 rounded-sm text-xs transition-colors duration-150 ease-out disabled:opacity-50 disabled:pointer-events-none",
  ghost:
    "text-[#8FA3A0] hover:text-[#83DDDA] hover:bg-white/[0.05] font-mono uppercase tracking-[0.14em] px-3 py-1.5 rounded-sm text-xs transition-colors duration-150 ease-out disabled:opacity-50 disabled:pointer-events-none",
  danger:
    "border border-red-500/30 bg-red-500/[0.08] text-[#f87171] hover:bg-red-500/[0.14] font-mono uppercase tracking-[0.14em] px-5 py-2.5 rounded-sm text-xs transition-colors duration-150 ease-out disabled:opacity-50 disabled:pointer-events-none",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

export function Button({ variant = "primary", className, ...rest }: ButtonProps) {
  return (
    <button
      type="button"
      className={cn(buttonStyles[variant], "focus-ring", className)}
      {...rest}
    />
  );
}

/* ---- Card (DESIGN.md §5): sharp single-level container, no nested cards ---- */
export function Card({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={cn(
        "rounded-none border border-white/[0.08] bg-[#0E1223] p-5 shadow-none sm:p-6",
        className,
      )}
    >
      {children}
    </section>
  );
}

/* ---- Badge (DESIGN.md §5): sharp mono chip; tone mapping keeps callers working ----
   default → hairline/sage · success → teal · amber → accent (gold retired) · cyan → teal */
type BadgeTone = "default" | "success" | "amber" | "cyan";

const badgeStyles: Record<BadgeTone, string> = {
  default:
    "bg-white/[0.04] text-[#8FA3A0] border border-white/[0.14]",
  success:
    "bg-[#3AA99E]/10 text-[#3AA99E] border border-[#3AA99E]/40",
  amber:
    "bg-[#E4621F]/10 text-[#E4621F] border border-[#E4621F]/40",
  cyan: "bg-[#3AA99E]/10 text-[#3AA99E] border border-[#3AA99E]/40",
};

const dotStyles: Record<BadgeTone, string> = {
  default: "bg-[#8FA3A0]",
  success: "bg-[#3AA99E]",
  amber: "bg-[#E4621F]",
  cyan: "bg-[#3AA99E]",
};

export function Badge({
  children,
  tone = "default",
  dot = false,
  className,
}: {
  children: ReactNode;
  tone?: BadgeTone;
  dot?: boolean;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-none border text-[11px] font-mono font-medium uppercase tracking-[0.14em]",
        badgeStyles[tone],
        className,
      )}
    >
      {dot && <span className={cn("h-1.5 w-1.5 rounded-full", dotStyles[tone])} />}
      {children}
    </span>
  );
}

/* ---- Stamp: rotated 2px-bordered badge for EVIDENCE-GROUNDED / VOICE-FIRST / LIVE / SETUP ---- */
export function Stamp({
  children,
  tone = "accent",
  className,
}: {
  children: ReactNode;
  tone?: "accent" | "teal";
  className?: string;
}) {
  return (
    <span
      className={cn(
        "stamp",
        tone === "accent" ? "stamp-accent" : "stamp-teal",
        className,
      )}
    >
      {children}
    </span>
  );
}

/* ---- Input: underline style (transparent bg, bottom hairline, serif value) ----
   Props unchanged: label / hint / error / id passthrough + a11y wiring. */
interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
}

export function Input({ label, hint, error, className, id, ...rest }: InputProps) {
  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={id}
          className="input-label"
        >
          {label}
        </label>
      )}
      <input
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined}
        className={cn("input-underline", error && "border-red-500/60", className)}
        {...rest}
      />
      {error ? (
        <p id={`${id}-error`} role="alert" className="mt-1.5 font-mono text-xs text-[#f87171]">
          {error}
        </p>
      ) : hint ? (
        <p id={`${id}-hint`} className="mt-1.5 font-mono text-[11px] uppercase tracking-[0.14em] text-[#8FA3A0]">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

/* ---- Spinner / busy indicator (teal) ---- */
export function Spinner({ label = "Loading…" }: { label?: string }) {
  return (
    <span className="inline-flex items-center gap-2 font-mono text-xs uppercase tracking-[0.14em] text-[#8FA3A0]" role="status">
      <span className="live-dot inline-block h-2 w-2 animate-pulse rounded-full bg-[#3AA99E]" />
      {label}
    </span>
  );
}

/* ---- Toast (error alert, bottom-center) ---- */
export function Toast({
  message,
  onDismiss,
}: {
  message: string;
  onDismiss: () => void;
}) {
  return (
    <div
      role="alert"
      className="fixed bottom-5 left-1/2 z-50 w-[min(92vw,28rem)] -translate-x-1/2 rounded-none border border-red-500/30 bg-[#06090A] px-4 py-3"
    >
      <div className="flex items-start justify-between gap-3">
        <p className="font-serif text-sm text-[#f87171]">{message}</p>
        <button
          type="button"
          onClick={onDismiss}
          className="rounded-none px-2.5 py-0.5 font-mono text-xs uppercase tracking-[0.14em] text-[#8FA3A0] transition-colors duration-150 ease-out hover:bg-white/[0.05] hover:text-[#83DDDA] focus-ring"
        >
          Dismiss
        </button>
      </div>
    </div>
  );
}
