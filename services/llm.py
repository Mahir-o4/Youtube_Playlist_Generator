"""Gemini model factory and structured-output helpers."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage

from core.cache import cache_key, read_json, write_json
from prompts import build_decomposition_messages
from schemas import SyllabusBreakdown, SyllabusInput

Decomposer = Callable[[SyllabusInput], SyllabusBreakdown]
DEFAULT_MODEL = "gemini-3.5-flash-lite"
_ROOT = Path(__file__).resolve().parents[1]
_ENV_PATH = _ROOT / ".env"
_EVAL_CACHE_DIR = _ROOT / "data" / "cache"


def load_environment() -> None:
    """Load the repo-local .env without overriding real environment variables."""
    load_dotenv(_ENV_PATH)
    load_dotenv(Path.cwd() / ".env")


def has_api_key() -> bool:
    load_environment()
    return bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))


def init_model(model: str | None = None) -> BaseChatModel:
    """Lazily initialize a chat model via LangChain's universal factory."""
    load_environment()
    model_name = model or os.getenv("APP_GEMINI_MODEL") or DEFAULT_MODEL
    return init_chat_model(f"google_genai:{model_name}")


def structured_model(schema: type, model: str | None = None):
    """Return a runnable that produces a validated Pydantic instance."""
    return init_model(model).with_structured_output(schema, method="json_schema")


def cached_structured_invoke(
    model, messages: list[BaseMessage], schema: type
):
    """Invoke a structured model, caching results by prompt content."""
    key = cache_key(
        [schema.__name__, [getattr(m, "content", "") for m in messages]]
    )
    path = _EVAL_CACHE_DIR / f"structured_{key}.json"
    cached = read_json(path)
    if cached is not None:
        return schema.model_validate(cached)
    result = model.invoke(messages)
    write_json(path, result.model_dump())
    return result


def make_decomposer(model: str | None = None) -> Decomposer:
    """Build the syllabus decomposer. Requires a Gemini API key."""
    load_environment()
    if not has_api_key():
        raise RuntimeError(
            "Gemini API key missing. Set GOOGLE_API_KEY in .env or the environment."
        )

    structured = structured_model(SyllabusBreakdown, model=model)

    def decomposer(data: SyllabusInput) -> SyllabusBreakdown:
        return cached_structured_invoke(
            structured, build_decomposition_messages(data), SyllabusBreakdown
        )

    return decomposer
