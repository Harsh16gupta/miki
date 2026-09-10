import { Link } from "react-router-dom";
import { Card } from "../components/common/Primitives";

/** Placeholder — session history UI lands in Wave 4 (Task 36). */
export default function HistoryPage() {
  return (
    <Card className="mx-auto max-w-2xl">
      <h1 className="text-lg font-medium tracking-tight text-white sm:text-xl">
        Past sessions
      </h1>
      <p className="mt-2 text-sm leading-relaxed text-neutral-300">
        Sign in to see your interview history. History view ships in Wave 4 —
        the <span className="font-mono text-xs">GET /sessions/history</span>{" "}
        API is already live.
      </p>
      <div className="mt-4">
        <Link
          to="/login"
          className="rounded-lg bg-white px-4 py-2 text-sm font-medium text-zinc-950 shadow-sm transition-colors hover:bg-neutral-200 focus-ring"
        >
          Sign In
        </Link>
      </div>
    </Card>
  );
}
