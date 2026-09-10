import { useEffect, useState } from "react";
import ReportCard from "../components/report/ReportCard";
import { useInterviewCtx } from "../app/useInterviewCtx";
import { apiFetch } from "../lib/api";
import type { SessionDetail } from "../types/api";

export default function ReportPage() {
  const { interview } = useInterviewCtx();
  const [meta, setMeta] = useState<SessionDetail | null>(null);
  const sessionId = interview.report?.session_id ?? null;

  // Session dates/duration for the T22 summary header (best-effort).
  useEffect(() => {
    if (sessionId == null) return;
    let cancelled = false;
    apiFetch<SessionDetail>(`/session/${sessionId}`)
      .then((d) => {
        if (!cancelled) setMeta(d);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  return <ReportCard interview={interview} meta={meta} />;
}
