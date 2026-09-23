import { Check } from "lucide-react";
import { Stamp } from "../components/common/Primitives";
import Breadcrumb from "../components/common/Breadcrumb";
import SetupCard from "../components/setup/SetupCard";
import ClaimsPreview from "../components/setup/ClaimsPreview";
import { useInterviewCtx } from "../app/useInterviewCtx";

const CHECKLIST = [
  {
    title: "Upload your resume",
    body: "We extract your skills, projects and experience",
  },
  {
    title: "Add a job description",
    body: "So questions match the role and company",
  },
  {
    title: "Get a tailored interview",
    body: "Realistic questions and an evidence-cited report",
  },
];

/** Setup route (image 03): two-minute promise left, SESSION SETUP panel right. */
export default function SetupPage() {
  const { interview } = useInterviewCtx();
  const { profiles } = interview;
  return (
    <div className="space-y-8">
      <section className="grid items-start gap-10 pt-4 lg:grid-cols-[1.05fr_0.95fr]">
        <div>
          <Breadcrumb
            trail={[
              { label: "Home", to: "/" },
              { label: "Interview", to: "/interview" },
              { label: "Setup" },
            ]}
          />
          <div className="mt-6 flex flex-wrap gap-4">
            <Stamp tone="accent">Setup</Stamp>
            <Stamp tone="teal">Resume + JD</Stamp>
          </div>
          <h1 className="mt-6 font-serif text-5xl font-semibold leading-[1.05] tracking-tight text-[#83DDDA] sm:text-6xl xl:text-7xl">
            Start in{" "}
            <em className="italic text-[#E4621F]">two&nbsp;minutes.</em>
          </h1>
          <p className="mt-6 max-w-xl font-serif text-lg leading-relaxed text-[#83DDDA]">
            Upload your resume and a job description. Miki will create a
            tailored voice interview with realistic questions and a detailed,
            evidence-cited report. Accepted formats:{" "}
            <span className="font-mono text-base">.pdf</span>,{" "}
            <span className="font-mono text-base">.txt</span> · max 10&nbsp;MB
            per file.
          </p>
          <ul className="mt-8 space-y-5">
            {CHECKLIST.map((c) => (
              <li key={c.title} className="flex items-start gap-3.5">
                <span
                  aria-hidden="true"
                  className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center bg-[#3AA99E] text-black"
                >
                  <Check size={15} strokeWidth={3} />
                </span>
                <span>
                  <span className="block font-mono text-xs uppercase tracking-[0.18em] text-[#83DDDA]">
                    {c.title}
                  </span>
                  <span className="mt-1 block font-mono text-[11px] uppercase tracking-[0.14em] text-[#8FA3A0]">
                    {c.body}
                  </span>
                </span>
              </li>
            ))}
          </ul>
        </div>
        <SetupCard interview={interview} />
      </section>
      <ClaimsPreview
        candClaimsList={profiles.candClaimsList}
        candSkills={profiles.candSkills}
        roleSkillsList={profiles.roleSkillsList}
      />
    </div>
  );
}
