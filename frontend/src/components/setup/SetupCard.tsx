import { Play } from "lucide-react";
import { useNavigate } from "react-router-dom";
import type { InterviewApi } from "../../hooks/useInterview";
import GlassCard from "../layout/GlassCard";
import { PillBadge, Spinner } from "../common/Primitives";
import Dropzone from "./Dropzone";

function CheckItem({ done, label }: { done: boolean; label: string }) {
  return (
    <li className="flex items-center gap-2">
      <span
        aria-hidden="true"
        className={
          done
            ? "flex h-4 w-4 items-center justify-center rounded-full bg-emerald-500/15 text-[10px] text-emerald-400"
            : "h-4 w-4 rounded-full border border-white/15"
        }
      >
        {done ? "✓" : ""}
      </span>
      <span className={done ? "text-zinc-200" : "text-zinc-500"}>{label}</span>
    </li>
  );
}

export default function SetupCard({ interview }: { interview: InterviewApi }) {
  const { profiles, status } = interview;
  const navigate = useNavigate();
  const canStart =
    profiles.candId != null && profiles.roleId != null && status !== "starting";

  const handleStart = async () => {
    const ok = await interview.start();
    if (ok) navigate("/interview");
  };

  return (
    <GlassCard className="px-6 py-6 sm:px-8" >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-medium tracking-tight text-white sm:text-xl">
          <span className="mr-2 font-mono text-xs text-amber-300">01</span> Profiles
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
      <div className="mt-5 border-t border-white/[0.08] pt-4">
        <p className="text-xs font-medium uppercase tracking-wider text-neutral-400">
          Readiness checklist
        </p>
        <ul className="mt-2 space-y-1.5 text-sm">
          <CheckItem
            done={profiles.candId != null}
            label={`Resume parsed (${profiles.candClaims} claims)`}
          />
          <CheckItem
            done={profiles.roleId != null}
            label={`Job description parsed (${profiles.roleSkills} required skills)`}
          />
          <CheckItem
            done={canStart}
            label="Ready to launch — expect a ~40 minute session"
          />
        </ul>
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <button
          type="button"
          disabled={!canStart}
          onClick={() => void handleStart()}
          className="inline-flex items-center gap-2 rounded-lg bg-white px-4 py-2 text-sm font-medium text-zinc-950 shadow-sm transition-colors hover:bg-neutral-200 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Play size={15} />
          {status === "starting" ? "Starting…" : "Start interview"}
        </button>
        {status === "starting" && <Spinner label="Generating opening question…" />}
        {status === "uploading" && <Spinner label="Parsing document…" />}
        {!canStart && status !== "starting" && (
          <p className="text-xs text-zinc-500">
            Upload both files to unlock the interview.
          </p>
        )}
      </div>
    </GlassCard>
  );
}
