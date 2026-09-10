import { Navigate, useLocation } from "react-router-dom";
import type { ReactNode } from "react";
import { useAuth } from "./useAuth";
import { Spinner } from "../components/common/Primitives";

/** T39: redirects unauthenticated visitors to /login (remembers origin). */
export function RequireAuth({ children }: { children: ReactNode }) {
  const { status } = useAuth();
  const location = useLocation();
  if (status === "loading") {
    return (
      <div className="flex justify-center py-16">
        <Spinner label="Checking session…" />
      </div>
    );
  }
  if (status === "guest") {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <>{children}</>;
}
