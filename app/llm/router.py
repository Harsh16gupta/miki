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

# LLM provider switch (default: Meta Model API, OpenAI-compatible chat completions).
# - meta (default): base https://api.meta.ai/v1/chat/completions, key META_API_KEY,
#   model e.g. "muse-spark-1.3-contributor" (see model_config.yaml).
# - openrouter (fallback): base https://openrouter.ai/api/v1/chat/completions,
#   key OPENROUTER_API_KEY. Select with LLM_PROVIDER=openrouter.
META_URL = os.getenv("META_BASE_URL", "https://api.meta.ai/v1/chat/completions")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
CONFIG_PATH = Path(__file__).with_name("model_config.yaml")


def _provider() -> str:
    """Return the configured LLM provider (``meta`` default, ``openrouter`` fallback)."""
    return os.getenv("LLM_PROVIDER", "meta").lower().strip() or "meta"


def _provider_url_and_key(provider: str) -> tuple[str, str]:
    """Resolve (url, api_key) for a provider; raises RuntimeError when key missing."""
    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set. Copy .env.example to .env and set it."
            )
        return OPENROUTER_URL, api_key
    api_key = os.getenv("META_API_KEY") or os.getenv("MODEL_API_KEY")
    if not api_key:
        raise RuntimeError(
            "META_API_KEY is not set. Copy .env.example to .env and set it."
        )
    return META_URL, api_key

# Retry policy (V1, deliberately simple): up to this many *retries* — i.e.
# MAX_RETRIES + 1 total attempts — on network errors, timeouts, 429s and 5xxs.
MAX_RETRIES = 2
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

# Shared client: connection keep-alive across calls (saves a TLS handshake
# per LLM call vs one-shot httpx.post). Lazily created; never closed
# explicitly (process-lifetime pool, like the DB engine).
_client: httpx.Client | None = None


def _http() -> httpx.Client:
    global _client
    if _client is None:
        _client = httpx.Client(timeout=60.0)
    return _client


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
        model_id = _load_config()[task_type]
    except KeyError:
        valid = sorted(k for k in _load_config() if k != "reasoning_effort")
        raise ValueError(
            f"Unknown LLM task_type {task_type!r}. Valid types: {valid}"
        ) from None
    if not isinstance(model_id, str):
        valid = sorted(k for k in _load_config() if k != "reasoning_effort")
        raise ValueError(
            f"Unknown LLM task_type {task_type!r}. Valid types: {valid}"
        )
    return model_id


def _fail(
    *,
    task_type: str,
    model_id: str,
    messages: list[dict[str, Any]],
    latency_ms: int,
    error: str | None,
) -> None:
    """Log one failure telemetry event (never raises itself)."""
    log_llm_call(
        task_type=task_type,
        model_id=model_id,
        messages=messages,
        output=None,
        latency_ms=latency_ms,
        success=False,
        error=error,
    )


def effort_for_task(task_type: str) -> str | None:
    """Return the configured ``reasoning_effort`` for ``task_type`` (or None).

    Read from the ``reasoning_effort:`` section of ``model_config.yaml``.
    Missing entries mean "omit the parameter" (model default depth).
    """
    section = _load_config().get("reasoning_effort", {})
    if not isinstance(section, dict):
        return None
    effort = section.get(task_type)
    return str(effort) if effort else None


def _int_section(name: str, task_type: str) -> int | None:
    """Read an int from a ``model_config.yaml`` section (or None)."""
    section = _load_config().get(name, {})
    if not isinstance(section, dict):
        return None
    value = section.get(task_type)
    return int(value) if isinstance(value, (int, float)) and value else None


def max_tokens_for_task(task_type: str) -> int | None:
    """Return the configured ``max_tokens`` cap for ``task_type`` (or None)."""
    return _int_section("max_tokens", task_type)


def call_llm(
    task_type: str,
    messages: list[dict[str, Any]],
    response_format: dict[str, Any] | None = None,
    reasoning_effort: str | None = "__default__",
    max_tokens: int | None = None,
) -> dict[str, Any]:
    """Make one LLM call for the given task (Meta default, OpenRouter fallback).

    Args:
        task_type: Key into ``model_config.yaml`` (e.g. ``"extraction"``).
        messages: Chat messages in OpenAI format (``role``/``content`` dicts).
        response_format: Optional OpenAI-style response format, e.g.
            ``{"type": "json_object"}`` for reliable structured output.
        reasoning_effort: ``minimal``/``low``/``medium``/``high``/``xhigh``
            (Meta only; omitted for other providers). ``"__default__"``
            resolves from the ``reasoning_effort:`` config section;
            pass ``None`` to force-omit the parameter.
        max_tokens: output cap (reasoning + visible tokens combined on Meta).
            ``None`` (default) resolves from the ``max_tokens:`` config
            section. Caps bound cost and tail latency; keep them generous so
            reasoning never starves the visible answer.

    Returns:
        Dict with ``model_id``, ``content`` (raw text), ``parsed_json``
        (parsed object when ``response_format`` was requested, else ``None``),
        ``usage`` (token counts as reported by the provider, may be empty)
        and ``latency_ms``.

    Raises:
        ValueError: Unknown ``task_type``; model returned invalid JSON when
            structured output was requested; or provider returned a 200 with
            a malformed/unexpected body.
        RuntimeError: Provider API key (``META_API_KEY`` / ``OPENROUTER_API_KEY``)
            is not set.
        httpx.HTTPError: Network failure or retryable status after retries,
            or a non-retryable 4xx client error.
    """
    provider = _provider()
    url, api_key = _provider_url_and_key(provider)

    model_id = model_for_task(task_type)
    if reasoning_effort == "__default__":
        reasoning_effort = effort_for_task(task_type)
    payload: dict[str, Any] = {"model": model_id, "messages": messages}
    if response_format is not None:
        payload["response_format"] = response_format
    # reasoning_effort is Meta-only; other providers may 400 unknown fields.
    if provider == "meta" and reasoning_effort:
        payload["reasoning_effort"] = reasoning_effort
    resolved_cap = max_tokens if max_tokens else max_tokens_for_task(task_type)
    if resolved_cap:
        payload["max_tokens"] = resolved_cap

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    last_error: str | None = None
    start = time.monotonic()
    data: dict[str, Any] | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = _http().post(url, headers=headers, json=payload)
        except httpx.HTTPError as e:
            # Network error / timeout / connection drop: retryable.
            last_error = f"{type(e).__name__}: {e}"
            if attempt >= MAX_RETRIES:
                _fail(
                    task_type=task_type,
                    model_id=model_id,
                    messages=messages,
                    latency_ms=int((time.monotonic() - start) * 1000),
                    error=last_error,
                )
                raise
            time.sleep(attempt + 1)
            continue
        if response.status_code in RETRYABLE_STATUS_CODES:
            last_error = f"HTTP {response.status_code}: {response.text[:500]}"
            if attempt >= MAX_RETRIES:
                _fail(
                    task_type=task_type,
                    model_id=model_id,
                    messages=messages,
                    latency_ms=int((time.monotonic() - start) * 1000),
                    error=last_error,
                )
                raise httpx.HTTPError(f"LLM call failed after retries: {last_error}")
            time.sleep(attempt + 1)
            continue
        if response.status_code >= 400:
            # Non-retryable client error: single telemetry event, raise now.
            last_error = f"HTTP {response.status_code}: {response.text[:500]}"
            _fail(
                task_type=task_type,
                model_id=model_id,
                messages=messages,
                latency_ms=int((time.monotonic() - start) * 1000),
                error=last_error,
            )
            response.raise_for_status()
        try:
            data = response.json()
            _ = data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as e:
            # 200 with a malformed/unexpected body: not retryable, fail loud.
            # Include a snippet of the raw body so the cause is diagnosable
            # from the API error + server log (e.g. provider error object).
            last_error = f"Malformed LLM response: {e} body={response.text[:500]!r}"
            _fail(
                task_type=task_type,
                model_id=model_id,
                messages=messages,
                latency_ms=int((time.monotonic() - start) * 1000),
                error=last_error,
            )
            raise ValueError(last_error) from e
        break

    assert data is not None  # loop only exits via break (success) or raise
    latency_ms = int((time.monotonic() - start) * 1000)
    content = data["choices"][0]["message"].get("content")
    usage = data.get("usage", {})
    if not isinstance(content, str) or not content.strip():
        # Reasoning models occasionally return null/empty content (glitch or
        # refusal): fail loud as malformed so callers map it to 422/502.
        finish = data["choices"][0].get("finish_reason")
        err = f"Model returned empty content (finish_reason={finish})"
        log_llm_call(
            task_type=task_type,
            model_id=model_id,
            messages=messages,
            output=content,
            latency_ms=latency_ms,
            success=False,
            error=err,
            usage=usage,
        )
        raise ValueError(f"Malformed LLM response: {err}")

    parsed_json: Any | None = None
    if response_format is not None:
        try:
            parsed_json = json.loads(content)
        except (json.JSONDecodeError, TypeError) as e:
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


def call_llm_stream(
    task_type: str,
    messages: list[dict[str, Any]],
    reasoning_effort: str | None = "__default__",
    max_tokens: int | None = None,
):
    """Stream one LLM completion, yielding text deltas (OpenAI SSE shape).

    Yields ``str`` chunks from ``choices[0].delta.content`` as they arrive.
    No retries (callers fall back to :func:`call_llm` on error). Telemetry is
    emitted once, on completion, with the full text. Raises on HTTP errors
    or malformed streams. ``response_format`` is intentionally unsupported
    (streaming targets user-facing prose, not JSON).
    """
    from collections.abc import Iterator

    provider = _provider()
    url, api_key = _provider_url_and_key(provider)
    model_id = model_for_task(task_type)
    if reasoning_effort == "__default__":
        reasoning_effort = effort_for_task(task_type)
    payload: dict[str, Any] = {
        "model": model_id,
        "messages": messages,
        "stream": True,
    }
    if provider == "meta" and reasoning_effort:
        payload["reasoning_effort"] = reasoning_effort
    resolved_cap = max_tokens if max_tokens else max_tokens_for_task(task_type)
    if resolved_cap:
        payload["max_tokens"] = resolved_cap
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    def _gen() -> Iterator[str]:
        start = time.monotonic()
        parts: list[str] = []
        try:
            with _http().stream("POST", url, headers=headers, json=payload) as r:
                if r.status_code >= 400:
                    body = r.read().decode(errors="replace")[:500]
                    raise httpx.HTTPError(
                        f"LLM stream failed: HTTP {r.status_code}: {body}"
                    )
                for line in r.iter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if not data or data == "[DONE]":
                        continue
                    try:
                        event = json.loads(data)
                        delta = event["choices"][0]["delta"].get("content") or ""
                    except (ValueError, KeyError, IndexError, TypeError):
                        continue
                    if delta:
                        parts.append(delta)
                        yield delta
        except Exception as e:
            log_llm_call(
                task_type=task_type,
                model_id=model_id,
                messages=messages,
                output="".join(parts) or None,
                latency_ms=int((time.monotonic() - start) * 1000),
                success=False,
                error=f"Stream failed: {e}",
            )
            raise
        log_llm_call(
            task_type=task_type,
            model_id=model_id,
            messages=messages,
            output="".join(parts),
            latency_ms=int((time.monotonic() - start) * 1000),
            success=True,
        )

    return _gen()
