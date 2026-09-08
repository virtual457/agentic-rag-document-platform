from __future__ import annotations

import json
import time
from functools import lru_cache
from typing import Any

from cachetools import TTLCache

from src.config import get_settings


class MemoryCache:
    name = "memory"

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if expires_at < time.time():
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        self._store[key] = (time.time() + ttl, value)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)


class RedisCache:
    name = "redis"

    def __init__(self) -> None:
        import redis

        self._client = redis.Redis.from_url(get_settings().redis_url, decode_responses=False)

    def get(self, key: str) -> Any | None:
        v = self._client.get(key)
        if v is None:
            return None
        try:
            return json.loads(v)
        except Exception:
            return v

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        try:
            payload = json.dumps(value, default=str).encode()
        except Exception:
            payload = str(value).encode()
        self._client.set(key, payload, ex=ttl)

    def delete(self, key: str) -> None:
        self._client.delete(key)


@lru_cache
def get_cache() -> MemoryCache | RedisCache:
    backend = get_settings().cache_backend.lower()
    if backend == "redis":
        try:
            return RedisCache()
        except Exception:
            pass
    return MemoryCache()


# Layer-typed helpers so we can enforce separate TTLs
@lru_cache
def _embedding_cache() -> TTLCache:
    return TTLCache(maxsize=10000, ttl=get_settings().cache_ttl_embedding)


@lru_cache
def _answer_cache() -> TTLCache:
    return TTLCache(maxsize=1000, ttl=get_settings().cache_ttl_answer)


def cache_embedding(text_key: str, value: list[float]) -> None:
    _embedding_cache()[text_key] = value


def read_embedding(text_key: str) -> list[float] | None:
    return _embedding_cache().get(text_key)


def cache_answer(key: str, value: dict) -> None:
    _answer_cache()[key] = value


def read_answer(key: str) -> dict | None:
    return _answer_cache().get(key)
