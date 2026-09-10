import { useRef, useState } from "react";
import { FileUp } from "lucide-react";
import { cn } from "../../lib/cn";

interface Props {
  label: string;
  hint: string;
  fileName: string;
  meta: string;
  busy: boolean;
  onFile: (file: File) => void;
}

export default function Dropzone({ label, hint, fileName, meta, busy, onFile }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label={`${label} upload`}
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
        if (f) onFile(f);
      }}
      className={cn(
        "cursor-pointer rounded-xl border border-dashed p-5 transition focus-ring",
        dragOver
          ? "border-cyan-500/60 bg-cyan-500/5"
          : "border-white/15 bg-white/[0.03] hover:border-white/30",
      )}
    >
      <div className="flex items-start gap-3">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-white/10 bg-white/[0.03] text-amber-300">
          <FileUp size={16} />
        </span>
        <div className="min-w-0">
          <p className="text-sm font-medium text-white">{label}</p>
          <p className="mt-0.5 truncate text-xs text-zinc-400">
            {fileName || hint}
          </p>
          <p className="mt-2 font-mono text-[11px] text-cyan-300">
            {busy ? "Parsing…" : meta}
          </p>
        </div>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.txt"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFile(f);
          e.target.value = "";
        }}
      />
    </div>
  );
}
