from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


Sender = Literal["user", "assistant", "system", "tool"]


class Conversation(BaseModel):
    """Represents a single message in a chat thread."""

    id: str = Field(alias="_id")
    chat_id: str
    user_id: str
    sender: Sender
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)

    class Config:
        populate_by_name = True


class ConversationCreate(BaseModel):
    """Payload for creating a conversation message."""

    chat_id: str
    user_id: str
    sender: Sender
    content: str
    metadata: Optional[Dict[str, Any]] = None
