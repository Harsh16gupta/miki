"""ORM models for the Miki interview engine (Phase 1 schema).

Importing this package registers every model on ``app.database.Base``,
which is what Alembic uses as ``target_metadata`` for autogenerate
(see ``migrations/env.py``). Prefer importing from here
(``from app.models import Session``) over deep module paths.
"""

from app.models.candidate_profile import CandidateProfile
from app.models.claim import Claim
from app.models.enums import EvidenceType, SessionStatus, Speaker
from app.models.evaluation import Evaluation
from app.models.evidence import Evidence
from app.models.ping import Ping
from app.models.role_profile import RoleProfile
from app.models.session import Session
from app.models.state_transition import StateTransition
from app.models.turn import Turn

__all__ = [
    "CandidateProfile",
    "Claim",
    "Evaluation",
    "Evidence",
    "EvidenceType",
    "Ping",
    "RoleProfile",
    "Session",
    "SessionStatus",
    "Speaker",
    "StateTransition",
    "Turn",
]
