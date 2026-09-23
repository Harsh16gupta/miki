import { Link } from "react-router-dom";

/** Pre-footer conversion banner. */
export default function CtaBanner() {
  return (
    <section className="rounded-none border border-white/[0.08] bg-[#0E1223] p-5 text-center sm:p-10">
      <h2 className="mx-auto max-w-xl font-serif text-3xl font-semibold leading-tight text-[#83DDDA] sm:text-4xl">
        Your next interview is already scheduled.{" "}
        <em className="italic text-[#E4621F]">Practice</em> for it.
      </h2>
      <p className="mx-auto mt-3 max-w-md font-serif text-base leading-relaxed text-[#8FA3A0]">
        No account, no setup hurdles — two files and forty minutes.
      </p>
      <div className="mt-6">
        <Link
          to="/setup"
          className="inline-block rounded-none bg-[#E4621F] px-6 py-3 font-mono text-xs font-medium uppercase tracking-[0.14em] text-black transition-all duration-150 ease-out hover:brightness-110 focus-ring"
        >
          Start practicing →
        </Link>
      </div>
    </section>
  );
}
