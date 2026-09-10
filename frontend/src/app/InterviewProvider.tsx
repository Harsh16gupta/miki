import type { ReactNode } from "react";
import { useInterview } from "../hooks/useInterview";
import { useVoice } from "../hooks/useVoice";
import { InterviewContext } from "./InterviewContext";

export function InterviewProvider({ children }: { children: ReactNode }) {
  const interview = useInterview();
  const voice = useVoice(interview);
  return (
    <InterviewContext.Provider value={{ interview, voice }}>
      {children}
    </InterviewContext.Provider>
  );
}
