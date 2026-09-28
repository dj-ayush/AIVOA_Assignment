"""
Thin wrapper around Groq's OpenAI-compatible SDK.

Two helpers are exposed to the rest of the app:
  - generate_structured(...): asks the model for JSON matching a Pydantic
    schema (used for extraction / editing / impact and severity assessment).
  - generate_text(...): plain conversational text (used for general chit-chat
    that should not touch the form).
"""
from __future__ import annotations

from copy import deepcopy
import json
from json import JSONDecodeError
from typing import Type, TypeVar

from groq import Groq
from pydantic import BaseModel, ValidationError

from .config import GROQ_API_KEY, GROQ_MODEL
from .observability import elapsed_ms, now_ms, record_llm_call, record_validation

T = TypeVar("T", bound=BaseModel)

_client: Groq | None = None


def get_client() -> Groq:
    global _client
    if _client is None:
        if not GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Copy backend/.env.example to backend/.env "
                "and paste in your Groq API key from https://console.groq.com/keys"
            )
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


def _strict_json_schema(schema: Type[BaseModel]) -> dict:
    json_schema = deepcopy(schema.model_json_schema())

    def normalize(node: dict) -> None:
        if node.get("type") == "object":
            node["additionalProperties"] = False
            if "properties" in node:
                node["required"] = list(node["properties"].keys())
        for value in node.values():
            if isinstance(value, dict):
                normalize(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        normalize(item)

    normalize(json_schema)
    return json_schema


def _token_usage(response) -> dict | None:
    usage = getattr(response, "usage", None)
    if usage is None:
        return None
    usage_data = {}
    for key in (
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "queue_time",
        "prompt_time",
        "completion_time",
        "total_time",
    ):
        value = getattr(usage, key, None)
        if value is not None:
            usage_data[key] = value
    return usage_data or None


def generate_structured(system_prompt: str, user_content: str, schema: Type[T]) -> T:
    client = get_client()
    llm_start = now_ms()
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": schema.__name__,
                    "strict": True,
                    "schema": _strict_json_schema(schema),
                },
            },
            temperature=0.2,
        )
    except Exception as exc:
        record_llm_call(
            operation="structured",
            model=GROQ_MODEL,
            schema=schema.__name__,
            duration_ms=elapsed_ms(llm_start),
            success=False,
            error=exc,
        )
        raise
    record_llm_call(
        operation="structured",
        model=GROQ_MODEL,
        schema=schema.__name__,
        duration_ms=elapsed_ms(llm_start),
        success=True,
        token_usage=_token_usage(response),
    )
    content = response.choices[0].message.content or "{}"
    validation_start = now_ms()
    try:
        data = json.loads(content)
        result = schema.model_validate(data)
    except JSONDecodeError as exc:
        record_validation(schema=schema.__name__, duration_ms=elapsed_ms(validation_start), success=False, error=exc)
        raise RuntimeError("Groq returned malformed JSON for a structured response.") from exc
    except ValidationError as exc:
        record_validation(schema=schema.__name__, duration_ms=elapsed_ms(validation_start), success=False, error=exc)
        raise
    record_validation(schema=schema.__name__, duration_ms=elapsed_ms(validation_start), success=True)
    return result


def generate_text(system_prompt: str, user_content: str) -> str:
    client = get_client()
    llm_start = now_ms()
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.4,
        )
    except Exception as exc:
        record_llm_call(
            operation="text",
            model=GROQ_MODEL,
            duration_ms=elapsed_ms(llm_start),
            success=False,
            error=exc,
        )
        raise
    record_llm_call(
        operation="text",
        model=GROQ_MODEL,
        duration_ms=elapsed_ms(llm_start),
        success=True,
        token_usage=_token_usage(response),
    )
    return (response.choices[0].message.content or "").strip()
