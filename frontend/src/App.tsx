import { Route, Routes } from "react-router-dom";
import { InterviewProvider } from "./app/InterviewProvider";
import { useInterviewCtx } from "./app/useInterviewCtx";
import AmbientBackground from "./components/background/AmbientBackground";
import Navbar from "./components/layout/Navbar";
import Footer from "./components/layout/Footer";
import { Toast } from "./components/common/Primitives";
import LandingPage from "./pages/LandingPage";
import SetupPage from "./pages/SetupPage";
import InterviewPage from "./pages/InterviewPage";
import ReportPage from "./pages/ReportPage";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import HistoryPage from "./pages/HistoryPage";

function Shell() {
  const { interview } = useInterviewCtx();
  return (
    <div className="relative min-h-svh">
      <AmbientBackground />
      <div className="relative z-10 mx-auto w-full max-w-4xl space-y-4 px-4 py-6 sm:px-6">
        <Navbar onReset={interview.reset} />
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/setup" element={<SetupPage />} />
          <Route path="/interview" element={<InterviewPage />} />
          <Route path="/report" element={<ReportPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="*" element={<LandingPage />} />
        </Routes>
        <Footer />
      </div>
      {interview.error && (
        <Toast message={interview.error} onDismiss={interview.dismissError} />
      )}
    </div>
  );
}

export default function App() {
  return (
    <InterviewProvider>
      <Shell />
    </InterviewProvider>
  );
}
