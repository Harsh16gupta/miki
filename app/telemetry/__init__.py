"""Telemetry layer (Phase 2).

The rest of the codebase must import :func:`log_llm_call` from here and never
import Langfuse directly — Langfuse is only a sink behind this thin wrapper.
"""

from app.telemetry.log_llm_call import log_llm_call

__all__ = ["log_llm_call"]
