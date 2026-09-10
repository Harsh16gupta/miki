import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import InterviewCard from "../components/interview/InterviewCard";
import { useInterviewCtx } from "../app/useInterviewCtx";

export default function InterviewPage() {
  const { interview, voice } = useInterviewCtx();
  const navigate = useNavigate();

  // Finished sessions land on the report route automatically.
  useEffect(() => {
    if (interview.stage === "report") navigate("/report");
  }, [interview.stage, navigate]);

  return <InterviewCard interview={interview} voice={voice} />;
}
