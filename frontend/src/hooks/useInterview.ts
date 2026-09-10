import { useCallback, useRef, useState } from "react";
import { apiPostJson, apiUpload, ApiError, apiFetch } from "../lib/api";
import type {
  AnswerResponse,
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

  const start = useCallback(async () => {
    if (busyRef.current) return;
    if (!profiles.candId || !profiles.roleId) {
      setError("Upload both resume and job description first");
      return;
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
      setMessages([
        { id: msgSeq++, who: "miki", text: body.question },
      ]);
      setStage("interview");
      setStatus("live");
    } catch (e) {
      setStatus("error");
      setError(
        e instanceof ApiError
          ? `Could not start: ${e.detail}`
          : "Could not start the interview.",
      );
    } finally {
      busyRef.current = false;
    }
  }, [profiles.candId, profiles.roleId]);

  const loadReport = useCallback(async (sid: number) => {
    setStatus("scoring");
    try {
      const rep = await apiFetch<EvaluationReport>(`/session/${sid}/report`);
      setReport(rep);
      setStage("report");
      setStatus("done");
    } catch (e) {
      setStatus("live");
      setError(
        e instanceof ApiError
          ? `Report failed: ${e.detail}`
          : "Report failed to load.",
      );
    }
  }, []);

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
      try {
        const body = await apiPostJson<AnswerResponse>(
          `/session/${sessionId}/answer`,
          { text: clean },
        );
        setInterviewState(body.state);
        setClaimsFound((c) => c + (body.claims_found ?? 0));
        setMessages((m) => [...m, { id: msgSeq++, who: "miki", text: body.question }]);
        if (body.finished) {
          await loadReport(sessionId);
        } else {
          setStatus("live");
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
    [sessionId, status, loadReport],
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

  const abort = useCallback(async () => {
    if (sessionId == null || busyRef.current) return;
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
      return;
    } finally {
      busyRef.current = false;
    }
    reset();
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
