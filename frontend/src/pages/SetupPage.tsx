import SetupCard from "../components/setup/SetupCard";
import { useInterviewCtx } from "../app/useInterviewCtx";

export default function SetupPage() {
  const { interview } = useInterviewCtx();
  return <SetupCard interview={interview} />;
}
