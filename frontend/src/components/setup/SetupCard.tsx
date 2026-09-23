import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Check } from "lucide-react";
import type { InterviewApi } from "../../hooks/useInterview";
import { Button, Spinner } from "../common/Primitives";
import Dropzone from "./Dropzone";

function NumberChip({ n }: { n: string }) {
  return (
    <span
      aria-hidden="true"
      className="flex h-6 w-6 shrink-0 items-center justify-center border border-white/[0.2] font-mono text-xs text-[#83DDDA]"
    >
      {n}
    </span>
  );
}

/** Session-setup form panel (image 03). JD paste is bridged to the frozen
    file-upload backend by wrapping text in a .txt File — hooks/api untouched. */
export default function SetupCard({ interview }: { interview: InterviewApi }) {
  const { profiles, status } = interview;
  const navigate = useNavigate();
  const [jdText, setJdText] = useState("");
  const canStart =
    profiles.candId != null && profiles.roleId != null && status !== "starting";

  const handleStart = async () => {
    const ok = await interview.start();
    if (ok) navigate("/interview");
  };

  const handleAttachPaste = () => {
    const clean = jdText.trim();
    if (!clean || status === "uploading") return;
    const file = new File([clean], "job-description.txt", { type: "text/plain" });
    void interview.uploadProfile("role", file);
  };

  return (
    <aside aria-label="Session setup" className="panel-hard p-6 sm:p-8">
      <div className="flex items-center justify-between gap-3 border-b border-white/[0.14] pb-4">
        <h2 className="font-mono text-xs uppercase tracking-[0.18em] text-[#83DDDA]">
          Session setup
        </h2>
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-[#8FA3A0]">
          Form · SES-001
        </p>
      </div>

      {/* 1 — resume */}
      <div className="mt-6 flex items-center gap-3">
        <NumberChip n="1" />
        <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-[#83DDDA]">
          Upload your resume
        </h3>
      </div>
      <div className="mt-4">
        <Dropzone
          label="your resume"
          title="Click to upload your resume"
          hint="PDF or TXT · up to 10MB"
          fileName={profiles.candName}
          meta={
            profiles.candId != null
              ? `Parsed · id ${profiles.candId}`
              : "Not uploaded"
          }
          busy={status === "uploading"}
          onFile={(f) => void interview.uploadProfile("candidate", f)}
        />
      </div>

      {/* 2 — job description */}
      <div className="mt-7 flex items-center gap-3">
        <NumberChip n="2" />
        <h3 className="font-mono text-xs uppercase tracking-[0.18em] text-[#83DDDA]">
          Job description
        </h3>
      </div>
      <div className="mt-4">
        <label
          htmlFor="jd-paste"
          className="input-label sr-only"
        >
          Paste the job description
        </label>
        <textarea
          id="jd-paste"
          rows={3}
          value={jdText}
          onChange={(e) => setJdText(e.target.value)}
          placeholder="Paste the job description here…"
          className="input-underline min-h-[4.5rem] resize-y italic placeholder:text-[#8FA3A0]/75 focus-ring"
        />
        <p className="mt-2 font-mono text-[11px] uppercase tracking-[0.14em] text-[#8FA3A0]">
          Include the full description for better results.
        </p>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <Button
            variant="secondary"
            disabled={jdText.trim() === "" || status === "uploading"}
            onClick={handleAttachPaste}
          >
            {status === "uploading" ? "Attaching…" : "Attach pasted text →"}
          </Button>
        </div>
        <div className="mt-3">
          <Dropzone
            compact
            label="Job description file"
            hint="…or drop a .pdf / .txt file instead"
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
        {(profiles.roleId != null || profiles.candId != null) && (
          <ul className="mt-4 space-y-1.5">
            {profiles.candId != null && (
              <li className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.14em] text-[#3AA99E]">
                <Check size={13} strokeWidth={3} /> Resume parsed ·{" "}
                {profiles.candClaims} claims
              </li>
            )}
            {profiles.roleId != null && (
              <li className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.14em] text-[#3AA99E]">
                <Check size={13} strokeWidth={3} /> Role parsed ·{" "}
                {profiles.roleSkills} required skills
              </li>
            )}
          </ul>
        )}
      </div>

      <div aria-hidden="true" className="mt-7 border-t border-dashed border-white/[0.2]" />

      <div className="mt-6">
        <Button
          variant="primary"
          disabled={!canStart}
          onClick={() => void handleStart()}
          className="w-full py-3.5 text-sm"
        >
          {status === "starting" ? "Starting…" : "Begin interview →"}
        </Button>
        {status === "starting" && (
          <p className="mt-3">
            <Spinner label="Generating opening question…" />
          </p>
        )}
        {status === "uploading" && (
          <p className="mt-3">
            <Spinner label="Parsing document…" />
          </p>
        )}
        {!canStart && status !== "starting" && status !== "uploading" && (
          <p className="mt-3 font-mono text-[11px] uppercase tracking-[0.14em] text-[#8FA3A0]">
            Upload your resume and job description to unlock the interview.
          </p>
        )}
      </div>
    </aside>
  );
}
