import { useCallback, useRef, useState } from "react";
import {
  apiPostJson,
  apiUpload,
  ApiError,
  apiFetch,
  authHeaders,
} from "../lib/api";
import { apiUrl } from "../lib/config";
import type {
  AnswerResponse,
  AnswerStreamEvent,
  CandidateProfileResponse,
  ChatMessage,
  EvaluationReport,
  RoleProfileResponse,
  SessionDetail,
  StartResponse,
} from "../types/api";

export type Stage = "setup" | "interview" | "report";
export type Status =
  | "idle"
  | "uploading"
  | "ready"
  | "starting"
  | "live"
  | "thinking"
  | "scoring"
  | "done"
  | "error";

export interface ProfileState {
  candId: number | null;
  roleId: number | null;
  candClaims: number;
  roleSkills: number;
  candName: string;
  roleName: string;
  candClaimsList: string[];
  candSkills: string[];
  roleSkillsList: string[];
}

const MAX_UPLOAD_MB = 10;

function checkFile(file: File): string | null {
  const okExt = /\.(pdf|txt)$/i.test(file.name);
  if (!okExt) return "Only .pdf or .txt files are accepted";
  if (file.size > MAX_UPLOAD_MB * 1024 * 1024)
    return `File is too large (max ${MAX_UPLOAD_MB} MB)`;
  if (file.size === 0) return "File is empty";
  return null;
}

let msgSeq = 1;

export function useInterview() {
  const [stage, setStage] = useState<Stage>("setup");
  const [status, setStatus] = useState<Status>("idle");
  const [profiles, setProfiles] = useState<ProfileState>({
    candId: null,
    roleId: null,
    candClaims: 0,
    roleSkills: 0,
    candName: "",
    roleName: "",
    candClaimsList: [],
    candSkills: [],
    roleSkillsList: [],
  });
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [detail, setDetail] = useState<SessionDetail | null>(null);
  const [interviewState, setInterviewState] = useState<string>("");
  const [policyVersion, setPolicyVersion] = useState<string>("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [claimsFound, setClaimsFound] = useState(0);
  const [report, setReport] = useState<EvaluationReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const busyRef = useRef(false);

  const toast = useCallback((msg: string) => setError(msg), []);

  const uploadProfile = useCallback(
    async (kind: "candidate" | "role", file: File) => {
      const problem = checkFile(file);
      if (problem) {
        setError(problem);
        return;
      }
      setStatus("uploading");
      setError(null);
      try {
        if (kind === "candidate") {
          const body = await apiUpload<CandidateProfileResponse>(
            "/candidate-profile/upload",
            file,
          );
          setProfiles((p) => ({
            ...p,
            candId: body.id,
            candClaims: body.extracted_json.claims?.length ?? 0,
            candName: file.name,
            candClaimsList: body.extracted_json.claims ?? [],
            candSkills: body.extracted_json.skills ?? [],
          }));
        } else {
          const body = await apiUpload<RoleProfileResponse>(
            "/role-profile/upload",
            file,
          );
          setProfiles((p) => ({
            ...p,
            roleId: body.id,
            roleSkills: body.extracted_json.required_skills?.length ?? 0,
            roleName: file.name,
            roleSkillsList: body.extracted_json.required_skills ?? [],
          }));
        }
        setStatus("ready");
      } catch (e) {
        setStatus("error");
        setError(
          e instanceof ApiError
            ? `Upload failed: ${e.detail}`
            : "Upload failed. Check the backend is running.",
        );
      }
    },
    [],
  );

  const start = useCallback(async (): Promise<boolean> => {
    if (busyRef.current) return false;
    if (!profiles.candId || !profiles.roleId) {
      setError("Upload both resume and job description first");
      return false;
    }
    busyRef.current = true;
    setStatus("starting");
    setError(null);
    try {
      const body = await apiPostJson<StartResponse>("/session/start", {
        candidate_profile_id: profiles.candId,
        role_profile_id: profiles.roleId,
        mode: "normal",
      });
      setSessionId(body.session_id);
      setStartedAt(Date.now());
      setDetail(null);
      setInterviewState(body.state);
      setPolicyVersion(body.policy_version);
      setMessages([{ id: msgSeq++, who: "miki", text: body.question }]);
      setStage("interview");
      setStatus("live");
      return true;
    } catch (e) {
      setStatus("error");
      setError(
        e instanceof ApiError
          ? `Could not start: ${e.detail}`
          : "Could not start the interview.",
      );
      return false;
    } finally {
      busyRef.current = false;
    }
  }, [profiles.candId, profiles.roleId]);

  const loadReport = useCallback(async (sid: number) => {
    // Evaluation runs lazily server-side; poll until the report lands.
    // Retry transient states (eval still running, overloaded provider),
    // fail fast on client errors (bad session, forbidden, malformed eval).
    const RETRYABLE = new Set([409, 429, 502, 503, 504]);
    setStatus("scoring");
    for (let attempt = 1; ; attempt++) {
      try {
        const rep = await apiFetch<EvaluationReport>(`/session/${sid}/report`);
        setReport(rep);
        setStage("report");
        setStatus("done");
        return;
      } catch (e) {
        const retryable =
          !(e instanceof ApiError) || RETRYABLE.has(e.status);
        if (!retryable || attempt >= 10) {
          setStatus("live");
          setError(
            e instanceof ApiError
              ? `Report failed: ${e.detail}`
              : "Report failed to load.",
          );
          return;
        }
        await new Promise((r) => setTimeout(r, 4000));
      }
    }
  }, []);

  const answerNonStream = useCallback(
    async (clean: string, sid: number) => {
      const body = await apiPostJson<AnswerResponse>(`/session/${sid}/answer`, {
        text: clean,
      });
      setInterviewState(body.state);
      setClaimsFound((c) => c + (body.claims_found ?? 0));
      setMessages((m) => [...m, { id: msgSeq++, who: "miki", text: body.question }]);
      if (body.finished) {
        await loadReport(sid);
      } else {
        setStatus("live");
      }
    },
    [loadReport],
  );

  const answerStream = useCallback(
    async (
      clean: string,
      sid: number,
      mikiId: number,
    ): Promise<"done" | "empty"> => {
      // Returns "done" once ANY server event arrived (turn is committed
      // server-side — no non-stream fallback after this point), "empty"
      // when the stream died before the first event (safe to fall back).
      const res = await fetch(apiUrl(`/session/${sid}/answer/stream`), {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ text: clean }),
      });
      if (!res.ok || !res.body) return "empty";
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      let acc = "";
      let seen: AnswerStreamEvent | null = null;
      const patchMiki = () =>
        setMessages((m) => m.map((x) => (x.id === mikiId ? { ...x, text: acc } : x)));
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const frames = buf.split("\n\n");
        buf = frames.pop() ?? "";
        for (const frame of frames) {
          for (const line of frame.split("\n")) {
            if (!line.startsWith("data:")) continue;
            let ev: AnswerStreamEvent;
            try {
              ev = JSON.parse(line.slice(5)) as AnswerStreamEvent;
            } catch {
              continue;
            }
            if (ev.type === "error") {
              throw new ApiError(ev.status, ev.detail);
            }
            seen = ev;
            if (ev.type === "delta") {
              acc += ev.delta;
              patchMiki();
            } else if (ev.type === "done") {
              setInterviewState(ev.state);
              setClaimsFound((c) => c + (ev.claims_found ?? 0));
              if (ev.finished) {
                await loadReport(sid);
              } else {
                setStatus("live");
              }
            }
          }
        }
      }
      if (!seen) return "empty";
      if (seen.type !== "done") {
        throw new Error("Stream ended before the question completed.");
      }
      return "done";
    },
    [loadReport],
  );

  const answer = useCallback(
    async (text: string, opts?: { fromVoice?: boolean; transcript?: string }) => {
      const clean = text.trim();
      if (!clean || sessionId == null || busyRef.current) return;
      if (status === "thinking" || status === "scoring") return;
      busyRef.current = true;
      setMessages((m) => [
        ...m,
        {
          id: msgSeq++,
          who: "you",
          text: opts?.fromVoice ? `[voice] ${clean}` : clean,
          voice: opts?.fromVoice,
        },
      ]);
      setStatus("thinking");
      setError(null);
      const sid = sessionId;
      try {
        // Streaming placeholder: filled token-by-token; dropped if the
        // stream yields nothing (clean non-stream fallback, no double turn).
        const mikiId = msgSeq++;
        setMessages((m) => [...m, { id: mikiId, who: "miki", text: "…" }]);
        let outcome: "done" | "empty";
        try {
          outcome = await answerStream(clean, sid, mikiId);
        } catch (e) {
          // Stream committed (turn persisted) but broke mid-flight: keep
          // whatever streamed and surface the error instead of duplicating.
          setMessages((m) =>
            m.some((x) => x.id === mikiId && x.text !== "" && x.text !== "…")
              ? m
              : m.filter((x) => x.id !== mikiId),
          );
          throw e;
        }
        if (outcome === "empty") {
          setMessages((m) => m.filter((x) => x.id !== mikiId));
          await answerNonStream(clean, sid);
        }
      } catch (e) {
        setStatus("live");
        setError(
          e instanceof ApiError
            ? `Answer failed: ${e.detail}`
            : "Answer failed. Try again.",
        );
      } finally {
        busyRef.current = false;
      }
    },
    [sessionId, status, answerStream, answerNonStream],
  );

  const refreshDetail = useCallback(async () => {
    if (sessionId == null) return;
    try {
      const d = await apiFetch<SessionDetail>(`/session/${sessionId}`);
      setDetail(d);
      setInterviewState(d.state);
    } catch {
      // telemetry is best-effort; errors surface via answer/report flows
    }
  }, [sessionId]);

  const reset = useCallback(() => {
    setStage("setup");
    setStatus("idle");
    setSessionId(null);
    setStartedAt(null);
    setDetail(null);
    setMessages([]);
    setReport(null);
    setClaimsFound(0);
    setInterviewState("");
    setError(null);
    msgSeq = 1;
  }, []);

  const abort = useCallback(async (): Promise<boolean> => {
    if (sessionId == null || busyRef.current) return false;
    busyRef.current = true;
    setError(null);
    try {
      await apiPostJson(`/session/${sessionId}/abort`, {});
    } catch (e) {
      setError(
        e instanceof ApiError
          ? `End session failed: ${e.detail}`
          : "End session failed.",
      );
      return false;
    } finally {
      busyRef.current = false;
    }
    reset();
    return true;
  }, [sessionId, reset]);

  const pushMikiVoice = useCallback((text: string) => {
    setMessages((m) => [...m, { id: msgSeq++, who: "miki", text }]);
  }, []);

  const pushCandidateVoice = useCallback((text: string) => {
    setMessages((m) => [
      ...m,
      { id: msgSeq++, who: "you", text: `[voice] ${text}`, voice: true },
    ]);
  }, []);

  return {
    stage,
    status,
    profiles,
    sessionId,
    startedAt,
    detail,
    interviewState,
    policyVersion,
    messages,
    claimsFound,
    report,
    error,
    toast,
    dismissError: () => setError(null),
    uploadProfile,
    start,
    answer,
    abort,
    refreshDetail,
    loadReport,
    pushMikiVoice,
    pushCandidateVoice,
    setInterviewState,
    reset,
  };
}

export type InterviewApi = ReturnType<typeof useInterview>;
