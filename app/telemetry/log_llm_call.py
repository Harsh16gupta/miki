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

    Pipes to Langfuse (v4 SDK) as a generation observation on its own trace,
    carrying the model, input messages, output, latency, token usage and
    success/failure metadata. Failures are marked with level ERROR so they
    stand out in the Langfuse dashboard.
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

        host = (
            os.getenv("LANGFUSE_HOST")
            or os.getenv("LANGFUSE_BASE_URL")
            or "https://cloud.langfuse.com"
        )

        client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )

        def _as_int(value: Any) -> int | None:
            return value if isinstance(value, int) else None

        # OpenRouter reports prompt/completion/total tokens; Langfuse v4
        # wants a flat str->int usage_details map.
        prompt_tokens = _as_int((usage or {}).get("prompt_tokens"))
        completion_tokens = _as_int((usage or {}).get("completion_tokens"))
        total_tokens = _as_int((usage or {}).get("total_tokens"))
        usage_details = {
            k: v
            for k, v in {
                "input": prompt_tokens,
                "output": completion_tokens,
                "total": total_tokens,
            }.items()
            if v is not None
        }

        observation = client.start_observation(
            trace_context={"trace_id": client.create_trace_id()},
            name=f"llm:{task_type}",
            as_type="generation",
            input=messages,
            output=output,
            model=model_id,
            metadata={
                "task_type": task_type,
                "model_id": model_id,
                "success": success,
                "error": error,
                "latency_ms": latency_ms,
            },
            usage_details=usage_details or None,
            level="ERROR" if not success else "DEFAULT",
        )
        observation.end()
        client.flush()
    except Exception:
        logger.exception("telemetry logging failed (task=%s)", task_type)
