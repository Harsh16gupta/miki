"""Telemetry sink for LLM calls.

Everything else in the codebase imports :func:`log_llm_call` from here and
never imports Langfuse directly — Langfuse is just a sink behind this thin
wrapper. Safe to call when Langfuse keys are missing (logs a warning, no-op)
and never raises, so telemetry can never break the interview engine.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def log_llm_call(
    *,
    task_type: str,
    model_id: str,
    messages: list[dict[str, Any]],
    output: str | None,
    latency_ms: int,
    success: bool,
    error: str | None = None,
    usage: dict[str, Any] | None = None,
) -> None:
    """Emit one structured telemetry event for an LLM call.

    Pipes to Langfuse as a trace with a generation span carrying model,
    latency, token usage and success/failure metadata.
    """
    try:
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        if not public_key or not secret_key:
            logger.warning(
                "telemetry skipped (LANGFUSE_* keys not set): task=%s model=%s",
                task_type,
                model_id,
            )
            return

        from langfuse import Langfuse

        client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )
        trace = client.trace(
            name=f"llm:{task_type}",
            input=messages,
            output=output,
            metadata={
                "task_type": task_type,
                "model_id": model_id,
                "success": success,
                "error": error,
            },
        )
        trace.generation(
            name=task_type,
            model=model_id,
            input=messages,
            output=output,
            metadata={"latency_ms": latency_ms, "success": success},
            usage=usage,
        )
        client.flush()
    except Exception:
        logger.exception("telemetry logging failed (task=%s)", task_type)
