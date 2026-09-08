import type { ReactNode } from "react";
import { cn } from "../../lib/cn";

interface Props {
  children: ReactNode;
  className?: string;
}

/** Frosted dark-glass container with specular sheen. */
export default function GlassCard({ children, className }: Props) {
  return (
    <section className={cn("glass glass-sheen", className)}>
      <div className="glass-inner">{children}</div>
    </section>
  );
}
