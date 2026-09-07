"""Deterministic state-machine validator (Phase 5, no LLM).

Every proposal — hardcoded or (from Phase 7) LLM-made — goes through
:meth:`StateMachine.propose_transition`, which checks the legal-transition
table plus policy gates and persists a ``state_transition`` row either way.
Accepted proposals advance ``current_state``; rejected ones leave it unchanged.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session as DbSession

from app.interview.states import LEGAL_TRANSITIONS, InterviewState
from app.models import StateTransition
from app.policy.loader import InterviewPolicy


class TransitionContext(BaseModel):
    """Facts the policy gates need. Defaults mean 'no info, skip gates'."""

    followups_on_current_claim: int = Field(default=0, ge=0)
    elapsed_minutes: float = Field(default=0.0, ge=0.0)
    projects_covered: int = Field(default=0, ge=0)
    required_skills_covered: int = Field(default=0, ge=0)


class StateMachine:
    """Validator + persistence for one interview session's state."""

    def __init__(
        self,
        session_id: int,
        db: DbSession,
        policy: InterviewPolicy,
        current_state: InterviewState = InterviewState.OPENING,
    ) -> None:
        self.session_id = session_id
        self.db = db
        self.policy = policy
        self.current_state = current_state

    def _policy_rejection(
        self, target: InterviewState, ctx: TransitionContext
    ) -> str | None:
        """Return a rejection reason if a policy gate blocks this move."""
        if (
            target == InterviewState.FOLLOWING_UP
            and ctx.followups_on_current_claim >= self.policy.max_followups_per_claim
        ):
            return (
                f"max follow-ups per claim reached "
                f"({ctx.followups_on_current_claim}>= "
                f"{self.policy.max_followups_per_claim}): move on"
            )
        if target == InterviewState.CLOSING:
            hard_cap = (
                self.policy.target_duration_minutes + self.policy.max_overtime_minutes
            )
            coverage_met = (
                ctx.projects_covered >= self.policy.min_projects_covered
                and ctx.required_skills_covered
                >= self.policy.min_required_skills_covered
            )
            if ctx.elapsed_minutes >= hard_cap:
                return None  # hard cap always allows closing
            if not (
                coverage_met
                and ctx.elapsed_minutes >= self.policy.target_duration_minutes
            ):
                return (
                    f"closing blocked: need coverage "
                    f"(projects {ctx.projects_covered}/"
                    f"{self.policy.min_projects_covered}, skills "
                    f"{ctx.required_skills_covered}/"
                    f"{self.policy.min_required_skills_covered}) "
                    f"AND elapsed>={self.policy.target_duration_minutes}min "
                    f"(now {ctx.elapsed_minutes:.1f}min)"
                )
        return None

    def propose_transition(
        self,
        target_state: InterviewState | str,
        reason: str,
        ctx: TransitionContext | None = None,
        *,
        proposed_by_llm: bool = False,
        model_id: str = "manual",
    ) -> bool:
        """Validate a proposal, persist the attempt, advance iff accepted."""
        context = ctx or TransitionContext()
        try:
            target = (
                target_state
                if isinstance(target_state, InterviewState)
                else InterviewState(str(target_state))
            )
        except ValueError:
            self._persist(
                to_state=str(target_state),
                accepted=False,
                reason=f"unknown state: {target_state!r}",
                proposed_by_llm=proposed_by_llm,
                model_id=model_id,
            )
            return False

        if target not in LEGAL_TRANSITIONS[self.current_state]:
            self._persist(
                to_state=target.value,
                accepted=False,
                reason=(
                    f"illegal transition {self.current_state.value}->{target.value}"
                ),
                proposed_by_llm=proposed_by_llm,
                model_id=model_id,
            )
            return False

        rejection = self._policy_rejection(target, context)
        if rejection is not None:
            self._persist(
                to_state=target.value,
                accepted=False,
                reason=rejection,
                proposed_by_llm=proposed_by_llm,
                model_id=model_id,
            )
            return False

        from_state = self.current_state
        self.current_state = target
        self._persist(
            to_state=target.value,
            accepted=True,
            reason=None,
            proposed_by_llm=proposed_by_llm,
            model_id=model_id,
            from_state=from_state.value,
        )
        return True

    def _persist(
        self,
        *,
        to_state: str,
        accepted: bool,
        reason: str | None,
        proposed_by_llm: bool,
        model_id: str,
        from_state: str | None = None,
    ) -> None:
        row = StateTransition(
            session_id=self.session_id,
            from_state=from_state or self.current_state.value,
            to_state=to_state,
            proposed_by_llm=proposed_by_llm,
            was_validated=accepted,
            rejection_reason=reason,
            model_id=model_id,
        )
        self.db.add(row)
        self.db.commit()
