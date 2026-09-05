"""LLM access layer (Phase 2).

All LLM calls in the project go through :func:`call_llm` in
``app.llm.router``, which picks the model from ``model_config.yaml`` by task
type. Use :func:`model_for_task` when you need the configured model id for a
task without making a call.
"""

from app.llm.router import call_llm, model_for_task

__all__ = ["call_llm", "model_for_task"]
