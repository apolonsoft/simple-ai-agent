# app/schemas/chat.py
import datetime
import json
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ToolCallSchema(BaseModel):
    id: str
    tool: str
    arguments: dict[str, Any]
    status: str = "pending"  # "pending" | "approved" | "rejected" | "executed"
    result: Any | None = None


class ToolApprovalRequest(BaseModel):
    tool_call_id: str
    approved: bool
    message_id: uuid.UUID | None = None
    tool_name: str | None = None
    arguments: dict[str, Any] | None = None


class ChatMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, description="Message text from user")


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    tokens: int | None = None
    created_at: datetime.datetime
    tool_calls: list[ToolCallSchema] | list[dict[str, Any]] | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("tool_calls", mode="before")
    @classmethod
    def parse_tool_calls(cls, v: Any) -> Any:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return None
        return v


class ChatSessionCreate(BaseModel):
    title: str | None = Field(default="New Chat", max_length=255)


class ChatSessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class ChatSessionDetailResponse(ChatSessionResponse):
    messages: list[ChatMessageResponse] = []
