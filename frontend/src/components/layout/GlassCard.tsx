import type { ReactNode } from "react";
import { Card } from "../common/Primitives";

/** @deprecated Use {@link Card} from ../common/Primitives directly. */
export default function GlassCard({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <Card className={className}>{children}</Card>;
}
