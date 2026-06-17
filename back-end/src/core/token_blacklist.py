"""JWT Token 黑名单 — 防止登出后 token 被重放。

生产环境建议使用 Redis 替代内存存储。
"""

import threading
from datetime import datetime, timezone


class TokenBlacklist:
    """基于内存的 token 黑名单，使用 JWT exp 自动过期清理。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._store: dict[str, datetime] = {}

    def add(self, token: str, payload: dict | None = None) -> None:
        """将 token 加入黑名单，使用 JWT exp 作为过期时间。"""
        expire_at: datetime | None = None
        if payload and "exp" in payload:
            try:
                expire_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            except (TypeError, ValueError, OSError):
                pass
        if expire_at is None:
            expire_at = datetime.now(timezone.utc)
        with self._lock:
            self._store[token] = expire_at

    def is_blacklisted(self, token: str) -> bool:
        """检查 token 是否在黑名单中，同时清理过期条目。"""
        now = datetime.now(timezone.utc)
        with self._lock:
            expired = [k for k, v in self._store.items() if v < now]
            for k in expired:
                del self._store[k]
            return token in self._store

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)


token_blacklist = TokenBlacklist()
