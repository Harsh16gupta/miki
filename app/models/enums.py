from enum import StrEnum


class SessionStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABORTED = "aborted"


class Speaker(StrEnum):
    CANDIDATE = "candidate"
    MIKI = "miki"


class EvidenceType(StrEnum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    VAGUE = "vague"

