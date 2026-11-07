# app/schemas/chat.py
import uuid
import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ChatMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, description="Message text from user")


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    tokens: Optional[int] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class ChatSessionCreate(BaseModel):
    title: Optional[str] = Field(default="New Chat", max_length=255)


class ChatSessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class ChatSessionDetailResponse(ChatSessionResponse):
    messages: List[ChatMessageResponse] = []
