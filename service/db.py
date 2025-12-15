from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

from schemas import Chat, ChatCreate, Conversation, ConversationCreate


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MongoStorage:
    """Simple Mongo storage helper for chats and conversations backed by Pydantic schemas."""

    def __init__(self, uri: str, db_name: str) -> None:
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[db_name]
        self.chat: AsyncIOMotorCollection = self.db["chat"]
        self.conversation: AsyncIOMotorCollection = self.db["conversation"]

    async def ensure_indexes(self) -> None:
        await self.chat.create_index([("user_id", 1), ("created_at", -1)])
        await self.conversation.create_index([("chat_id", 1), ("created_at", 1)])

    @staticmethod
    def _object_id(id_value: str) -> ObjectId:
        return ObjectId(id_value)

    async def create_chat(self, payload: ChatCreate) -> Chat:
        doc = payload.model_dump()
        now = utc_now()
        doc["created_at"] = now
        doc["updated_at"] = now
        result = await self.chat.insert_one(doc)
        stored = await self.chat.find_one({"_id": result.inserted_id})
        if stored and "_id" in stored:
            stored["_id"] = str(stored["_id"])
        return Chat.model_validate(stored)

    async def get_chat(self, chat_id: str) -> Optional[Chat]:
        doc = await self.chat.find_one({"_id": self._object_id(chat_id)})
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return Chat.model_validate(doc) if doc else None

    async def insert_message(self, payload: ConversationCreate) -> Conversation:
        doc = payload.model_dump()
        doc["chat_id"] = self._object_id(doc["chat_id"])
        doc["metadata"] = doc.get("metadata") or {}
        doc["created_at"] = utc_now()
        result = await self.conversation.insert_one(doc)
        stored = await self.conversation.find_one({"_id": result.inserted_id})
        if stored and "_id" in stored:
            stored["_id"] = str(stored["_id"])
        if stored and "chat_id" in stored:
            stored["chat_id"] = str(stored["chat_id"])
        if stored and "metadata" in stored and stored["metadata"] is None:
            stored["metadata"] = {}
        return Conversation.model_validate(stored)

    async def get_recent_history(
        self, chat_id: str, limit: int = 20
    ) -> List[Dict[str, str]]:
        """
        Return recent conversation as list[dict] compatible with ChatService history.
        """
        cursor = (
            self.conversation.find({"chat_id": self._object_id(chat_id)})
            .sort("created_at", 1)
            .limit(limit)
        )
        history: List[Dict[str, str]] = []
        async for doc in cursor:
            history.append(
                {"role": doc.get("sender", "assistant"), "content": doc.get("content", "")}
            )
        return history
