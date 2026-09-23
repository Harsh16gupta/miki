import { useRef, useState } from "react";
import { FileText, X } from "lucide-react";
import { cn } from "../../lib/cn";

interface Props {
  label: string;
  hint: string;
  fileName: string;
  meta: string;
  busy: boolean;
  onFile: (file: File) => void;
  /** Compact one-line variant for secondary upload slots. */
  compact?: boolean;
  /** Override the dropzone title (default: CLICK TO UPLOAD …). */
  title?: string;
}

function formatSize(bytes: number | null): string | null {
  if (bytes == null) return null;
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** 3-state upload zone (design sheet): default dashed sage · hover teal +
    "Release to upload" · filled filename + size + Uploaded + replace.
    Same props as before; `compact`/`title` are additive. */
export default function Dropzone({
  label,
  hint,
  fileName,
  meta,
  busy,
  onFile,
  compact = false,
  title,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [lastSize, setLastSize] = useState<number | null>(null);
  const filled = fileName !== "";

  const handleFile = (f: File) => {
    setLastSize(f.size);
    onFile(f);
  };

  if (compact) {
    return (
      <div
        role="button"
        tabIndex={0}
        aria-label={`${label} upload (.pdf or .txt)`}
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
          if (f) handleFile(f);
        }}
        className={cn(
          "upload-zone cursor-pointer px-3 py-2 font-mono text-[11px] uppercase tracking-[0.14em] focus-ring",
          dragOver ? "upload-zone-hover text-[#3AA99E]" : "text-[#8FA3A0] hover:text-[#83DDDA]",
        )}
      >
        {filled ? (
          <span className="flex items-center justify-between gap-2">
            <span className="truncate text-[#83DDDA] normal-case tracking-normal">
              {fileName}
            </span>
            <span className="shrink-0 text-[#3AA99E]">
              {busy ? "Parsing…" : "Uploaded"}
            </span>
          </span>
        ) : (
          <span>{dragOver ? "Release to upload" : hint}</span>
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
            if (f) handleFile(f);
            e.target.value = "";
          }}
        />
      </div>
    );
  }

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label={`${label} upload (.pdf or .txt, max 10 MB)`}
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
        if (f) handleFile(f);
      }}
      className={cn(
        "upload-zone cursor-pointer px-4 py-6 text-center transition-colors duration-150 ease-out focus-ring",
        dragOver && "upload-zone-hover",
        filled && "upload-zone-filled text-left",
      )}
    >
      {filled ? (
        <div className="flex items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <FileText size={20} className="shrink-0 text-[#3AA99E]" strokeWidth={1.5} />
            <div className="min-w-0">
              <p className="truncate font-mono text-xs text-[#83DDDA]">{fileName}</p>
              <p className="mt-0.5 font-mono text-[11px] uppercase tracking-[0.14em] text-[#8FA3A0]">
                {formatSize(lastSize) ? `${formatSize(lastSize)} · ` : ""}
                <span className="text-[#3AA99E]">
                  {busy ? "Parsing…" : "Uploaded"}
                </span>
              </p>
            </div>
          </div>
          <button
            type="button"
            aria-label={`Replace ${label}`}
            onClick={(e) => {
              e.stopPropagation();
              inputRef.current?.click();
            }}
            className="shrink-0 rounded-none p-1 text-[#8FA3A0] transition-colors duration-150 ease-out hover:text-[#83DDDA] focus-ring"
          >
            <X size={16} />
          </button>
        </div>
      ) : (
        <>
          <FileText size={24} className="mx-auto text-[#83DDDA]" strokeWidth={1.5} />
          <p className="mt-3 font-mono text-xs uppercase tracking-[0.18em] text-[#83DDDA]">
            {dragOver ? "Release to upload" : (title ?? `Click to upload ${label}`)}
          </p>
          <p className="mt-1.5 font-mono text-[11px] uppercase tracking-[0.14em] text-[#8FA3A0]">
            {busy ? "Parsing…" : hint}
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
          if (f) handleFile(f);
          e.target.value = "";
        }}
      />
      <span className="sr-only">{meta}</span>
    </div>
  );
}
