from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class LongTermMemory(BaseModel):
    """Persistent user-specific memory."""

    id: str = Field(alias="_id")
    user_id: str
    profile: Dict[str, Any] = Field(default_factory=dict)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    background: Optional[str] = None
    topics: list[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=utc_now)

    class Config:
        populate_by_name = True


class ShortTermMemory(BaseModel):
    """Session/chat-scoped transient memory."""

    id: str = Field(alias="_id")
    chat_id: str
    user_id: str
    task: Optional[str] = None
    topic: Optional[str] = None
    temporary_preferences: Dict[str, Any] = Field(default_factory=dict)
    last_interaction_at: datetime = Field(default_factory=utc_now)

    class Config:
        populate_by_name = True
