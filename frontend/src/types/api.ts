/** Typed mirrors of the FastAPI schemas (routers/profiles.py, sessions.py). */

export interface CandidateExtracted {
  skills: string[];
  projects: { name: string; description: string }[];
  claims: string[];
}

export interface RoleExtracted {
  required_skills: string[];
  preferred_skills: string[];
  responsibilities: string[];
  seniority_signal: string;
}

export interface ProfileResponse<T> {
  id: number;
  extracted_json: T;
}

export type CandidateProfileResponse = ProfileResponse<CandidateExtracted>;
export type RoleProfileResponse = ProfileResponse<RoleExtracted>;

export interface StartResponse {
  session_id: number;
  state: string;
  question: string;
  policy_version: string;
}

export interface AnswerResponse {
  question: string;
  state: string;
  finished: boolean;
  transition_applied: boolean;
  claims_found: number;
}

export interface SessionDetail {
  session_id: number;
  state: string;
  status: string;
  turns: number;
  claims: number;
  policy_version: string;
  engine_version: string;
  started_at: string;
  ended_at: string | null;
  duration_s: number | null;
}

export interface RefPreview {
  id: number;
  text: string;
}

export interface ReportDimension {
  dimension: string;
  score: number;
  rubric_version: string;
  refs: {
    claims: RefPreview[];
    evidence: RefPreview[];
    turns: RefPreview[];
  };
}

export interface EvaluationReport {
  session_id: number;
  status: string;
  policy_version: string;
  engine_version: string;
  rubric_version: string;
  dimensions: ReportDimension[];
  claims_examined: number;
  strengths: string[];
  weaknesses: string[];
  hard_to_defend_claims: string[];
  study_topics: string[];
}

export type ChatWho = "miki" | "you";

export interface ChatMessage {
  id: number;
  who: ChatWho;
  text: string;
  voice?: boolean;
}

/** Server -> client WS frames (routers/voice.py protocol). */
export type VoiceServerFrame =
  | { type: "ready"; session_id: number; silence_threshold_seconds: number }
  | { type: "answer"; transcript: string }
  | { type: "question"; text: string; finished: boolean }
  | { type: "audio"; format: string; data_b64: string }
  | { type: "done" }
  | { type: "error"; detail: string };
