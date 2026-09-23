import { Stamp } from "../common/Primitives";
import Breadcrumb from "../common/Breadcrumb";

/** Landing hero copy (image 02): stamps, serif H1, serif body. */
export default function HeroBanner() {
  return (
    <div>
      <Breadcrumb trail={[{ label: "Home", to: "/" }, { label: "Interview" }]} />
      <div className="mt-6 flex flex-wrap gap-4">
        <Stamp tone="accent">Evidence-grounded</Stamp>
        <Stamp tone="teal">Voice-first</Stamp>
      </div>
      <h1 className="mt-6 font-serif text-5xl font-semibold leading-[1.05] tracking-tight text-[#83DDDA] sm:text-6xl xl:text-7xl">
        Defend your resume{" "}
        <em className="italic text-[#E4621F]">out&nbsp;loud.</em>
      </h1>
      <p className="mt-6 max-w-xl font-serif text-lg leading-relaxed text-[#83DDDA]">
        Upload your resume and a job description, get{" "}
        <em className="italic text-[#E4621F]">realistic</em> voice interviews,
        and a detailed report with <em className="italic text-[#E4621F]">evidence</em>{" "}
        from your responses. Practice like a real interview, know exactly where
        you stand, and <em className="italic text-[#E4621F]">improve</em> with
        personalized feedback.
      </p>
    </div>
  );
}
