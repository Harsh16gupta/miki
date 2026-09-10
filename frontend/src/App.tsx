import { useRef } from "react";
import { useInterview } from "./hooks/useInterview";
import { useVoice } from "./hooks/useVoice";
import AmbientBackground from "./components/background/AmbientBackground";
import SiteHeader from "./components/layout/SiteHeader";
import HeroCard from "./components/layout/HeroCard";
import SetupCard from "./components/setup/SetupCard";
import InterviewCard from "./components/interview/InterviewCard";
import ReportCard from "./components/report/ReportCard";
import { Toast } from "./components/common/Primitives";

export default function App() {
  const interview = useInterview();
  const voice = useVoice(interview);
  const setupRef = useRef<HTMLDivElement>(null);

  return (
    <div className="relative min-h-svh">
      <AmbientBackground />
      <div className="relative z-10 mx-auto w-full max-w-4xl space-y-4 px-4 py-6 sm:px-6">
        <SiteHeader onReset={interview.reset} />
        <HeroCard
          onBegin={() =>
            setupRef.current?.scrollIntoView({ behavior: "smooth" })
          }
        />
        <div ref={setupRef} className="scroll-mt-6">
          <SetupCard interview={interview} />
        </div>
        <InterviewCard interview={interview} voice={voice} />
        <ReportCard interview={interview} />
        <footer className="pb-4 pt-2 text-center text-[11px] text-zinc-500">
          Miki · evidence-grounded interview trainer
        </footer>
      </div>
      {interview.error && (
        <Toast message={interview.error} onDismiss={interview.dismissError} />
      )}
    </div>
  );
}
