import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";
import { cn } from "../../lib/cn";

/* ---- Button (DESIGN.md §5) ---- */
type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

const buttonStyles: Record<ButtonVariant, string> = {
  primary:
    "bg-white text-zinc-950 hover:bg-neutral-200 font-medium px-4 py-2 rounded-lg text-sm transition-colors shadow-sm disabled:opacity-50",
  secondary:
    "border border-white/10 bg-white/[0.03] text-neutral-200 hover:bg-white/[0.08] hover:text-white px-4 py-2 rounded-lg text-sm transition-colors disabled:opacity-50",
  ghost:
    "text-neutral-400 hover:text-white hover:bg-white/[0.05] px-3 py-1.5 rounded-lg text-sm transition-colors disabled:opacity-50",
  danger:
    "border border-red-500/30 bg-red-500/[0.08] text-red-400 hover:bg-red-500/[0.14] hover:text-red-300 px-4 py-2 rounded-lg text-sm transition-colors disabled:opacity-50",
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

/* ---- Card (DESIGN.md §5): single-level container, no nested cards ---- */
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
        "rounded-xl border border-white/[0.08] bg-zinc-900/60 p-5 shadow-xl sm:p-6",
        className,
      )}
    >
      {children}
    </section>
  );
}

/* ---- Badge (DESIGN.md §5) with optional dot indicator ---- */
type BadgeTone = "default" | "success" | "amber" | "cyan";

const badgeStyles: Record<BadgeTone, string> = {
  default: "bg-white/[0.06] text-neutral-300 border border-white/[0.08]",
  success:
    "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20",
  amber: "bg-amber-500/10 text-amber-300 border border-amber-500/20",
  cyan: "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20",
};

const dotStyles: Record<BadgeTone, string> = {
  default: "bg-neutral-400",
  success: "bg-emerald-400",
  amber: "bg-amber-400",
  cyan: "bg-cyan-400",
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
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium",
        badgeStyles[tone],
        className,
      )}
    >
      {dot && <span className={cn("h-1.5 w-1.5 rounded-full", dotStyles[tone])} />}
      {children}
    </span>
  );
}

/* ---- Input (Surface 2 per DESIGN.md §2) ---- */
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
          className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-neutral-400"
        >
          {label}
        </label>
      )}
      <input
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined}
        className={cn(
          "w-full rounded-lg border bg-[rgba(24,24,27,0.6)] px-3 py-2 text-sm text-zinc-50 placeholder:text-zinc-500 transition-colors focus-ring",
          error
            ? "border-red-500/30 focus:border-red-500/60"
            : "border-white/[0.06] focus:border-white/25",
          className,
        )}
        {...rest}
      />
      {error ? (
        <p id={`${id}-error`} role="alert" className="mt-1.5 text-xs text-red-400">
          {error}
        </p>
      ) : hint ? (
        <p id={`${id}-hint`} className="mt-1.5 text-xs text-zinc-500">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

/* ---- Spinner / busy indicator ---- */
export function Spinner({ label = "Loading…" }: { label?: string }) {
  return (
    <span className="inline-flex items-center gap-2 text-sm text-zinc-400" role="status">
      <span className="live-dot inline-block h-2 w-2 animate-pulse rounded-full bg-cyan-500" />
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
      className="fixed bottom-5 left-1/2 z-50 w-[min(92vw,28rem)] -translate-x-1/2 rounded-xl border border-red-500/30 bg-[#18181b] px-4 py-3 shadow-xl"
    >
      <div className="flex items-start justify-between gap-3">
        <p className="text-sm text-red-400">{message}</p>
        <button
          type="button"
          onClick={onDismiss}
          className="rounded-lg px-2.5 py-0.5 text-xs text-neutral-400 transition-colors hover:bg-white/[0.05] hover:text-white focus-ring"
        >
          Dismiss
        </button>
      </div>
    </div>
  );
}
