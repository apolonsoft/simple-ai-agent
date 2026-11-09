# app/schemas/llm.py
from typing import Literal

from pydantic import BaseModel, Field


class LLMMessage(BaseModel):
    """Canonical chat message format passed into LLM providers."""

    role: Literal["system", "user", "assistant"]
    content: str = Field(..., min_length=1)


class LLMStreamChunk(BaseModel):
    """Individual streamed delta token/chunk from the provider."""

    content: str
    finish_reason: str | None = None
