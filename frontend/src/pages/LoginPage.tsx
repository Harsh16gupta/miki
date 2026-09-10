import { Link } from "react-router-dom";
import { Card } from "../components/common/Primitives";

/** Placeholder — full login form lands in Wave 4 (Tasks 32–35). */
export default function LoginPage() {
  return (
    <Card className="mx-auto max-w-md">
      <h1 className="text-lg font-medium tracking-tight text-white sm:text-xl">
        Sign in
      </h1>
      <p className="mt-2 text-sm leading-relaxed text-neutral-300">
        Email + password sign-in ships in Wave 4. Guest mode works now — head
        to setup to start practicing.
      </p>
      <div className="mt-4 flex gap-3">
        <Link
          to="/setup"
          className="rounded-lg bg-white px-4 py-2 text-sm font-medium text-zinc-950 shadow-sm transition-colors hover:bg-neutral-200 focus-ring"
        >
          Go to Setup
        </Link>
        <Link
          to="/"
          className="rounded-lg px-3 py-1.5 text-sm text-neutral-400 transition-colors hover:bg-white/[0.05] hover:text-white focus-ring"
        >
          Back to Home
        </Link>
      </div>
    </Card>
  );
}
