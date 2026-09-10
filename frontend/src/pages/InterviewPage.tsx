import InterviewCard from "../components/interview/InterviewCard";
import { useInterviewCtx } from "../app/useInterviewCtx";

export default function InterviewPage() {
  const { interview, voice } = useInterviewCtx();
  return <InterviewCard interview={interview} voice={voice} />;
}
