"""Conversation memory with Redis backend and in-memory fallback."""
import json
import time
from dataclasses import dataclass, asdict
from typing import Optional

import structlog

from app.config.settings import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


@dataclass
class Message:
    role: str  # "user" | "assistant"
    content: str
    timestamp: float
    session_id: str
    tool_calls: Optional[list] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Message":
        return Message(**data)


class ConversationMemory:
    """Manages conversation history per session using Redis or in-memory."""

    def __init__(self):
        self._redis = None
        self._local: dict[str, list[Message]] = {}

    async def _get_redis(self):
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
                self._redis = await aioredis.from_url(
                    settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
                await self._redis.ping()
                logger.info("Redis connected for conversation memory")
            except Exception as exc:
                logger.warning("Redis unavailable, falling back to in-memory", error=str(exc))
                self._redis = None
        return self._redis

    def _key(self, session_id: str) -> str:
        return f"conversation:{session_id}"

    async def add_message(self, message: Message) -> None:
        redis = await self._get_redis()
        if redis:
            try:
                key = self._key(message.session_id)
                await redis.rpush(key, json.dumps(message.to_dict()))
                await redis.expire(key, settings.redis_conversation_ttl)
                return
            except Exception as exc:
                logger.error("Redis write failed", error=str(exc))

        # Fallback to in-memory
        sid = message.session_id
        if sid not in self._local:
            self._local[sid] = []
        self._local[sid].append(message)

    async def get_history(self, session_id: str) -> list[Message]:
        redis = await self._get_redis()
        if redis:
            try:
                raw = await redis.lrange(self._key(session_id), 0, -1)
                return [Message.from_dict(json.loads(r)) for r in raw]
            except Exception as exc:
                logger.error("Redis read failed", error=str(exc))

        return self._local.get(session_id, [])

    async def clear_session(self, session_id: str) -> None:
        redis = await self._get_redis()
        if redis:
            try:
                await redis.delete(self._key(session_id))
                return
            except Exception as exc:
                logger.error("Redis delete failed", error=str(exc))
        self._local.pop(session_id, None)

    async def get_messages_for_agent(self, session_id: str) -> list[dict]:
        """Return messages in Google ADK-compatible format."""
        history = await self.get_history(session_id)
        return [
            {"role": msg.role, "parts": [{"text": msg.content}]}
            for msg in history
        ]


# Singleton
conversation_memory = ConversationMemory()
