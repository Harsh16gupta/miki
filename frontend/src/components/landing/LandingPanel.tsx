import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Check, FileText } from "lucide-react";
import { cn } from "../../lib/cn";
import { useInterviewCtx } from "../../app/useInterviewCtx";

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

const SETTINGS = [
  "Voice mock interview",
  "Evidence-cited report",
  "Technical + behavioral",
  "Personalized feedback",
];

/** Landing hero panel (image 02): 3 numbered rows. Row 1 is a live resume
    dropzone on shared interview context; rows 2–3 preview the setup form
    (JD paste needs the setup route — backend accepts file uploads only). */
export default function LandingPanel() {
  const { interview } = useInterviewCtx();
  const { profiles, status } = interview;
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const busy = status === "uploading";
  const filled = profiles.candId != null;

  return (
    <aside aria-label="Get started" className="panel-hard p-6 sm:p-8">
      {/* 1 — upload resume */}
      <div className="flex items-center gap-3">
        <NumberChip n="1" />
        <h2 className="font-mono text-xs uppercase tracking-[0.18em] text-[#83DDDA]">
          Upload resume
        </h2>
      </div>
      <div
        role="button"
        tabIndex={0}
        aria-label="Upload resume (.pdf or .txt, max 10 MB)"
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          const f = e.dataTransfer.files?.[0];
          if (f) void interview.uploadProfile("candidate", f);
        }}
        className={cn(
          "upload-zone mt-4 cursor-pointer px-4 py-6 text-center transition-colors duration-150 ease-out focus-ring",
          dragOver && "upload-zone-hover",
          filled && "upload-zone-filled text-left",
        )}
      >
        {filled ? (
          <div className="flex items-center justify-between gap-3">
            <div className="flex min-w-0 items-center gap-3">
              <FileText size={20} className="shrink-0 text-[#3AA99E]" />
              <div className="min-w-0">
                <p className="truncate font-mono text-xs text-[#83DDDA]">
                  {profiles.candName}
                </p>
                <p className="mt-0.5 font-mono text-[11px] uppercase tracking-[0.14em] text-[#3AA99E]">
                  Uploaded · {profiles.candClaims} claims
                </p>
              </div>
            </div>
            <span className="shrink-0 font-mono text-xs uppercase tracking-[0.14em] text-[#8FA3A0]">
              {busy ? "Parsing…" : "Replace"}
            </span>
          </div>
        ) : (
          <>
            <FileText size={24} className="mx-auto text-[#83DDDA]" strokeWidth={1.5} />
            <p className="mt-3 font-mono text-xs uppercase tracking-[0.18em] text-[#83DDDA]">
              {dragOver ? "Release to upload" : "Drag & drop your resume"}
            </p>
            <p className="mt-1.5 font-mono text-[11px] uppercase tracking-[0.14em] text-[#8FA3A0]">
              {busy ? "Parsing…" : "PDF · TXT (max 10MB)"}
            </p>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.txt"
          className="hidden"
          aria-hidden="true"
          tabIndex={-1}
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) void interview.uploadProfile("candidate", f);
            e.target.value = "";
          }}
        />
      </div>

      {/* 2 — job description (preview of the setup form) */}
      <div className="mt-7 flex items-center gap-3">
        <NumberChip n="2" />
        <h2 className="font-mono text-xs uppercase tracking-[0.18em] text-[#83DDDA]">
          Job description
        </h2>
      </div>
      <p className="mt-4 font-mono text-[11px] uppercase tracking-[0.18em] text-[#8FA3A0]">
        Paste job description
      </p>
      <div aria-hidden="true" className="mt-2 space-y-2.5 pb-1">
        {[100, 100, 100, 92].map((w, i) => (
          <div key={i} className="h-px bg-[#83DDDA]/40" style={{ width: `${w}%` }} />
        ))}
      </div>
      <Link
        to="/setup"
        className="mt-1 inline-block rounded-none font-mono text-[11px] uppercase tracking-[0.14em] text-[#8FA3A0] transition-colors duration-150 ease-out hover:text-[#83DDDA] focus-ring"
      >
        Attach it in setup →
      </Link>

      {/* 3 — interview settings */}
      <div className="mt-7 flex items-center gap-3">
        <NumberChip n="3" />
        <h2 className="font-mono text-xs uppercase tracking-[0.18em] text-[#83DDDA]">
          Interview settings
        </h2>
      </div>
      <ul className="mt-4 grid gap-x-6 gap-y-3 sm:grid-cols-2">
        {SETTINGS.map((s) => (
          <li key={s} className="flex items-center gap-2.5">
            <span
              aria-hidden="true"
              className="flex h-5 w-5 shrink-0 items-center justify-center bg-[#3AA99E] text-black"
            >
              <Check size={14} strokeWidth={3} />
            </span>
            <span className="font-mono text-[11px] uppercase tracking-[0.14em] text-[#83DDDA]">
              {s}
            </span>
          </li>
        ))}
      </ul>
    </aside>
  );
}
