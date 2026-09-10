import { useContext } from "react";
import { InterviewContext } from "./InterviewContext";

export function useInterviewCtx() {
  const ctx = useContext(InterviewContext);
  if (!ctx) throw new Error("useInterviewCtx must be used inside InterviewProvider");
  return ctx;
}
