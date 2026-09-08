import type { InterviewApi } from "../../hooks/useInterview";
import type { useVoice } from "../../hooks/useVoice";
import GlassCard from "../layout/GlassCard";
import { PillBadge, Spinner } from "../common/Primitives";
import ChatThread from "./ChatThread";
import Composer from "./Composer";

interface Props {
  interview: InterviewApi;
  voice: ReturnType<typeof useVoice>;
}

export default function InterviewCard({ interview, voice }: Props) {
  const active = interview.stage !== "setup";
  const busy = interview.status === "thinking" || interview.status === "starting";

  return (
    <GlassCard className="px-6 py-6 sm:px-8" >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-base font-semibold text-white">
          <span className="mr-2 text-[#d6c7a5]">02</span> Interview
        </h2>
        <div className="flex flex-wrap gap-1.5">
          {interview.sessionId != null && (
            <PillBadge>session #{interview.sessionId}</PillBadge>
          )}
          {interview.interviewState && (
            <PillBadge tone="cyan">{interview.interviewState}</PillBadge>
          )}
          {interview.claimsFound > 0 && (
            <PillBadge tone="gold">{interview.claimsFound} claims</PillBadge>
          )}
          {interview.policyVersion && (
            <PillBadge>policy {interview.policyVersion}</PillBadge>
          )}
        </div>
      </div>

      <div className="mt-4">
        {!active ? (
          <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-8 text-center text-sm text-[#a8a29e]">
            Complete setup to unlock the arena.
          </div>
        ) : (
          <div className="space-y-4">
            <ChatThread messages={interview.messages} />
            {busy && <Spinner label="Miki is thinking…" />}
            <Composer
              busy={busy}
              recording={voice.recording}
              voiceStatus={voice.voiceStatus}
              canVoice={interview.sessionId != null}
              onSend={(t) => void interview.answer(t)}
              onToggleVoice={voice.toggle}
            />
          </div>
        )}
      </div>
    </GlassCard>
  );
}
