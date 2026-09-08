from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, Callable

from src.config import get_settings


class AgentSession:
    def __init__(self, tenant: str, on_question: Callable[[str, str], Any] | None = None):
        self.id = uuid.uuid4().hex
        self.tenant = tenant
        self.created_at = time.time()
        self.last_active_at = time.time()
        self._on_question = on_question
        self._pending: asyncio.Future[str] | None = None
        self._lock = asyncio.Lock()

    def touch(self) -> None:
        self.last_active_at = time.time()

    def expired(self, timeout: int) -> bool:
        return (time.time() - self.last_active_at) > timeout

    async def ask_user(self, question: str) -> str:
        self.touch()
        if self._on_question is None:
            return "user unavailable"
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[str] = loop.create_future()
        async with self._lock:
            self._pending = fut
        try:
            maybe = self._on_question(self.id, question)
            if asyncio.iscoroutine(maybe):
                await maybe
        except Exception:
            pass
        try:
            return await asyncio.wait_for(fut, timeout=get_settings().question_timeout_seconds)
        except asyncio.TimeoutError:
            return "user did not respond within timeout"
        finally:
            async with self._lock:
                self._pending = None

    async def deliver_answer(self, answer: str) -> bool:
        async with self._lock:
            fut = self._pending
        if fut is None or fut.done():
            return False
        fut.set_result(answer)
        return True


class SessionRegistry:
    def __init__(self) -> None:
        self._sessions: dict[str, AgentSession] = {}
        self._task: asyncio.Task | None = None

    def register(self, s: AgentSession) -> None:
        self._sessions[s.id] = s

    def drop(self, sid: str) -> None:
        self._sessions.pop(sid, None)

    def get(self, sid: str) -> AgentSession | None:
        return self._sessions.get(sid)

    async def cleanup_loop(self) -> None:
        settings = get_settings()
        while True:
            await asyncio.sleep(30)
            stale = [sid for sid, s in self._sessions.items() if s.expired(settings.session_timeout_seconds)]
            for sid in stale:
                self._sessions.pop(sid, None)

    def start(self) -> None:
        if self._task is None:
            try:
                loop = asyncio.get_event_loop()
                self._task = loop.create_task(self.cleanup_loop())
            except RuntimeError:
                pass


registry = SessionRegistry()
