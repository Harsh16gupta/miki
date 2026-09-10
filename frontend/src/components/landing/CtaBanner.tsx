import { Link } from "react-router-dom";

/** T10: pre-footer conversion banner. */
export default function CtaBanner() {
  return (
    <section className="rounded-xl border border-white/[0.08] bg-zinc-900/60 p-5 text-center shadow-xl sm:p-8">
      <h2 className="text-lg font-medium tracking-tight text-white sm:text-xl">
        Your next interview is already scheduled. Practice for it.
      </h2>
      <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-neutral-300">
        No account, no setup hurdles — two files and forty minutes.
      </p>
      <div className="mt-5">
        <Link
          to="/setup"
          className="inline-block rounded-lg bg-white px-4 py-2 text-sm font-medium text-zinc-950 shadow-sm transition-colors hover:bg-neutral-200 focus-ring"
        >
          Start Practicing Now
        </Link>
      </div>
    </section>
  );
}
