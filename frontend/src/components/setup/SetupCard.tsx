import { Play } from "lucide-react";
import type { InterviewApi } from "../../hooks/useInterview";
import GlassCard from "../layout/GlassCard";
import { PillBadge, Spinner } from "../common/Primitives";
import Dropzone from "./Dropzone";

export default function SetupCard({ interview }: { interview: InterviewApi }) {
  const { profiles, status } = interview;
  const canStart =
    profiles.candId != null && profiles.roleId != null && status !== "starting";

  return (
    <GlassCard className="px-6 py-6 sm:px-8" >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-base font-semibold text-white">
          <span className="mr-2 text-[#d6c7a5]">01</span> Profiles
        </h2>
        <div className="flex gap-1.5">
          {profiles.candId != null && (
            <PillBadge tone="gold">{profiles.candClaims} claims</PillBadge>
          )}
          {profiles.roleId != null && (
            <PillBadge tone="gold">{profiles.roleSkills} req. skills</PillBadge>
          )}
        </div>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <Dropzone
          label="Resume"
          hint="Drop .pdf / .txt or click to browse"
          fileName={profiles.candName}
          meta={
            profiles.candId != null
              ? `Parsed · id ${profiles.candId}`
              : "Not uploaded"
          }
          busy={status === "uploading"}
          onFile={(f) => void interview.uploadProfile("candidate", f)}
        />
        <Dropzone
          label="Job description"
          hint="Drop .pdf / .txt or click to browse"
          fileName={profiles.roleName}
          meta={
            profiles.roleId != null
              ? `Parsed · id ${profiles.roleId}`
              : "Not uploaded"
          }
          busy={status === "uploading"}
          onFile={(f) => void interview.uploadProfile("role", f)}
        />
      </div>
      <div className="mt-5 flex flex-wrap items-center gap-3">
        <button
          type="button"
          disabled={!canStart}
          onClick={() => void interview.start()}
          className="inline-flex items-center gap-2 rounded-full bg-[#f5f3ee] px-5 py-2.5 text-sm font-semibold text-[#0b1120] transition enabled:hover:bg-white disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Play size={15} />
          {status === "starting" ? "Starting…" : "Start interview"}
        </button>
        {status === "starting" && <Spinner label="Generating opening question…" />}
        {status === "uploading" && <Spinner label="Parsing document…" />}
        {!canStart && status !== "starting" && (
          <p className="text-xs text-[#a8a29e]">
            Upload both files to unlock the interview.
          </p>
        )}
      </div>
    </GlassCard>
  );
}
