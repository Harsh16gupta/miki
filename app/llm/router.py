"""Static task -> model router for all LLM calls.

Every LLM call in the project goes through :func:`call_llm`, which picks the
model from ``model_config.yaml`` based on ``task_type``. No intelligent or
adaptive routing in V1 — this is a deliberate static mapping.
"""

from __future__ import annotations

import json
import os
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

import httpx
import yaml
from dotenv import load_dotenv

from app.telemetry.log_llm_call import log_llm_call

load_dotenv()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
CONFIG_PATH = Path(__file__).with_name("model_config.yaml")

# Retry policy (V1, deliberately simple): up to this many *retries* — i.e.
# MAX_RETRIES + 1 total attempts — on network errors, timeouts, 429s and 5xxs.
MAX_RETRIES = 2
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


@lru_cache(maxsize=1)
def _load_config() -> dict[str, str]:
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)
    if not isinstance(config, dict) or not config:
        raise RuntimeError(f"LLM model config is empty or invalid: {CONFIG_PATH}")
    return config


def model_for_task(task_type: str) -> str:
    """Return the model id configured for ``task_type``.

    Raises:
        ValueError: If ``task_type`` is not in the config.
    """
    try:
        return _load_config()[task_type]
    except KeyError:
        valid = sorted(_load_config())
        raise ValueError(
            f"Unknown LLM task_type {task_type!r}. Valid types: {valid}"
        ) from None


def _is_retryable(exc_or_status: httpx.HTTPError | int) -> bool:
    if isinstance(exc_or_status, int):
        return exc_or_status in RETRYABLE_STATUS_CODES
    # Network errors, timeouts, connection drops: always retryable.
    return True


def call_llm(
    task_type: str,
    messages: list[dict[str, Any]],
    response_format: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Make one LLM call via OpenRouter for the given task.

    Args:
        task_type: Key into ``model_config.yaml`` (e.g. ``"extraction"``).
        messages: Chat messages in OpenAI format (``role``/``content`` dicts).
        response_format: Optional OpenAI-style response format, e.g.
            ``{"type": "json_object"}`` for reliable structured output.

    Returns:
        Dict with ``model_id``, ``content`` (raw text), ``parsed_json``
        (parsed object when ``response_format`` was requested, else ``None``),
        ``usage`` (token counts as reported by the provider, may be empty)
        and ``latency_ms``.

    Raises:
        ValueError: Unknown ``task_type``, or model returned invalid JSON
            when structured output was requested.
        RuntimeError: ``OPENROUTER_API_KEY`` is not set.
        httpx.HTTPError: Network failure or retryable status after retries.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Copy .env.example to .env and set it."
        )

    model_id = model_for_task(task_type)
    payload: dict[str, Any] = {"model": model_id, "messages": messages}
    if response_format is not None:
        payload["response_format"] = response_format

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    last_error: str | None = None
    start = time.monotonic()
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = httpx.post(
                OPENROUTER_URL, headers=headers, json=payload, timeout=60.0
            )
            if response.status_code in RETRYABLE_STATUS_CODES:
                last_error = f"HTTP {response.status_code}: {response.text[:500]}"
                time.sleep(attempt + 1)
                continue
            if response.status_code >= 400:
                # Non-retryable client error: record telemetry, then raise.
                latency_ms = int((time.monotonic() - start) * 1000)
                log_llm_call(
                    task_type=task_type,
                    model_id=model_id,
                    messages=messages,
                    output=None,
                    latency_ms=latency_ms,
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text[:500]}",
                )
                response.raise_for_status()
            data = response.json()
            break
        except httpx.HTTPError as e:
            last_error = f"{type(e).__name__}: {e}"
            if attempt < MAX_RETRIES:
                time.sleep(attempt + 1)
                continue
            latency_ms = int((time.monotonic() - start) * 1000)
            log_llm_call(
                task_type=task_type,
                model_id=model_id,
                messages=messages,
                output=None,
                latency_ms=latency_ms,
                success=False,
                error=last_error,
            )
            raise
    else:  # Retries exhausted on retryable HTTP statuses.
        latency_ms = int((time.monotonic() - start) * 1000)
        log_llm_call(
            task_type=task_type,
            model_id=model_id,
            messages=messages,
            output=None,
            latency_ms=latency_ms,
            success=False,
            error=last_error,
        )
        raise httpx.HTTPError(f"LLM call failed after retries: {last_error}")

    latency_ms = int((time.monotonic() - start) * 1000)
    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})

    parsed_json: Any | None = None
    if response_format is not None:
        try:
            parsed_json = json.loads(content)
        except json.JSONDecodeError as e:
            log_llm_call(
                task_type=task_type,
                model_id=model_id,
                messages=messages,
                output=content,
                latency_ms=latency_ms,
                success=False,
                error=f"Invalid JSON from model: {e}",
                usage=usage,
            )
            raise ValueError(f"Model did not return valid JSON: {e}") from e

    log_llm_call(
        task_type=task_type,
        model_id=model_id,
        messages=messages,
        output=content,
        latency_ms=latency_ms,
        success=True,
        usage=usage,
    )
    return {
        "model_id": model_id,
        "content": content,
        "parsed_json": parsed_json,
        "usage": usage,
        "latency_ms": latency_ms,
    }
