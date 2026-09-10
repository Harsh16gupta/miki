import ReportCard from "../components/report/ReportCard";
import { useInterviewCtx } from "../app/useInterviewCtx";

export default function ReportPage() {
  const { interview } = useInterviewCtx();
  return <ReportCard interview={interview} />;
}
