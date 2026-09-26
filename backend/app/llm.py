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
from pydantic import BaseModel

from .config import GROQ_API_KEY, GROQ_MODEL

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


def generate_structured(system_prompt: str, user_content: str, schema: Type[T]) -> T:
    client = get_client()
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
    content = response.choices[0].message.content or "{}"
    try:
        return schema.model_validate(json.loads(content))
    except JSONDecodeError as exc:
        raise RuntimeError("Groq returned malformed JSON for a structured response.") from exc


def generate_text(system_prompt: str, user_content: str) -> str:
    client = get_client()
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.4,
    )
    return (response.choices[0].message.content or "").strip()
