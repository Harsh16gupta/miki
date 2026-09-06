"""Typed loader for interview policy configs (Phase 4).

The YAML file is the single source of truth; all engine code references
these typed fields, never raw dict lookups. ``version`` is stamped onto
every ``session`` row using the policy.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

POLICIES_DIR = Path(__file__).resolve().parent.parent.parent / "policies"
NORMAL_POLICY_PATH = POLICIES_DIR / "normal_interview.yaml"


class InterviewPolicy(BaseModel):
    """Typed view of one interview policy file."""

    version: str = Field(description="Manual semver, bumped on any change")
    mode: str = "normal"
    target_duration_minutes: int = Field(gt=0)
    max_overtime_minutes: int = Field(ge=0)
    min_projects_covered: int = Field(ge=0)
    min_required_skills_covered: int = Field(ge=0)
    max_followups_per_claim: int = Field(gt=0)
    difficulty_escalation_rule: str
    difficulty_deescalation_rule: str
    silence_threshold_seconds: int = Field(ge=1, le=30)
    closing_rule: str


def load_policy(path: Path | str = NORMAL_POLICY_PATH) -> InterviewPolicy:
    """Parse a policy YAML file into a validated ``InterviewPolicy``."""
    path = Path(path)
    with open(path) as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Policy file is not a mapping: {path}")
    return InterviewPolicy(**data)


@lru_cache(maxsize=1)
def get_normal_policy() -> InterviewPolicy:
    """Cached accessor for the normal-interview policy (V1 has one mode)."""
    return load_policy(NORMAL_POLICY_PATH)
