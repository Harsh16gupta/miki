import { createContext } from "react";
import type { InterviewApi } from "../hooks/useInterview";
import type { useVoice } from "../hooks/useVoice";

export interface InterviewContextValue {
  interview: InterviewApi;
  voice: ReturnType<typeof useVoice>;
}

export const InterviewContext = createContext<InterviewContextValue | null>(null);
