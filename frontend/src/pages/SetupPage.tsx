import SetupCard from "../components/setup/SetupCard";
import ClaimsPreview from "../components/setup/ClaimsPreview";
import { useInterviewCtx } from "../app/useInterviewCtx";

/** T11: focused setup header — criteria, formats, size guideline. */
export default function SetupPage() {
  const { interview } = useInterviewCtx();
  const { profiles } = interview;
  return (
    <div className="space-y-4">
      <div>
        <p className="text-xs font-medium uppercase tracking-wider text-neutral-400">
          Step 1 · Setup
        </p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight text-white sm:text-3xl">
          Upload your profile
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-neutral-300">
          Miki extracts verifiable <span className="text-zinc-50">claims</span>{" "}
          from your resume and <span className="text-zinc-50">required skills</span>{" "}
          from the job description, then probes whether your claims hold up.
          Accepted formats: <span className="font-mono text-xs">.pdf</span>,{" "}
          <span className="font-mono text-xs">.txt</span> · max 10&nbsp;MB per file.
        </p>
      </div>
      <SetupCard interview={interview} />
      <ClaimsPreview
        candClaimsList={profiles.candClaimsList}
        candSkills={profiles.candSkills}
        roleSkillsList={profiles.roleSkillsList}
      />
    </div>
  );
}
