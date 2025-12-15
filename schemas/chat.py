from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Chat(BaseModel):
    """Represents a chat thread."""

    id: str = Field(alias="_id")
    user_id: str
    title: Optional[str] = None
    status: str = "active"
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Config:
        populate_by_name = True


class ChatCreate(BaseModel):
    """Payload for creating a chat thread."""

    user_id: str
    title: Optional[str] = None
    status: str = "active"
    tags: List[str] = Field(default_factory=list)
