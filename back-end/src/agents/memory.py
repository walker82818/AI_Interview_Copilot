"""V4: Memory 系统 — 短期/长期记忆管理。

为 Agent 提供记忆能力：
- ShortTermMemory: 当前会话上下文（滑动窗口）
- LongTermMemory: 跨会话持久化记忆（候选人大数据）
- ConversationMemory: 面试对话的摘要记忆
"""

import json
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MemoryItem:
    """单条记忆条目。"""
    content: str
    role: str  # user / assistant / system
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)
    importance: float = 1.0  # 重要性权重 0-1


class ShortTermMemory:
    """短期记忆 — 当前会话的滑动窗口。

    特性：
    - 固定窗口大小，自动淘汰旧记忆
    - 支持重要性加权保留
    """

    def __init__(self, max_size: int = 20):
        self.max_size = max_size
        self._items: list[MemoryItem] = []

    def add(self, content: str, role: str, importance: float = 1.0) -> None:
        """添加记忆条目。"""
        item = MemoryItem(
            content=content,
            role=role,
            importance=importance,
        )
        self._items.append(item)

        # 超限时淘汰低重要性条目
        if len(self._items) > self.max_size:
            self._items.sort(key=lambda x: x.importance, reverse=True)
            self._items = self._items[:self.max_size]

    def get_context(
        self, limit: int | None = None, min_importance: float = 0.0
    ) -> list[dict[str, str]]:
        """获取记忆上下文。"""
        items = self._items
        if min_importance > 0:
            items = [i for i in items if i.importance >= min_importance]
        if limit:
            items = items[-limit:]
        return [{"role": i.role, "content": i.content} for i in items]

    def get_summary(self) -> str:
        """获取记忆摘要。"""
        if not self._items:
            return "暂无记忆"
        roles_count: dict[str, int] = {}
        for item in self._items:
            roles_count[item.role] = roles_count.get(item.role, 0) + 1
        total = len(self._items)
        parts = [f"共 {total} 条记忆: "]
        parts.extend(f"{r}: {c}条" for r, c in roles_count.items())
        return ", ".join(parts)

    def clear(self) -> None:
        self._items.clear()

    def __len__(self) -> int:
        return len(self._items)


class LongTermMemory:
    """长期记忆 — 跨会话的候选人大数据。

    存储候选人的历史面试数据、技能画像、改进轨迹等。
    当前为内存实现，生产环境建议使用 PostgreSQL/Redis。
    """

    def __init__(self):
        self._store: dict[str, dict[str, Any]] = {}

    def update_profile(self, user_id: str, profile_data: dict[str, Any]) -> None:
        """更新候选人画像。"""
        if user_id not in self._store:
            self._store[user_id] = {
                "skill_levels": {},
                "weak_areas": [],
                "interview_history": [],
                "avg_score": 0.0,
                "total_interviews": 0,
            }
        profile = self._store[user_id]
        profile.update(profile_data)

    def record_interview(
        self, user_id: str, score: float, dimensions: list[dict], summary: str
    ) -> None:
        """记录一次面试结果。"""
        if user_id not in self._store:
            self._store[user_id] = {
                "skill_levels": {},
                "weak_areas": [],
                "interview_history": [],
                "avg_score": 0.0,
                "total_interviews": 0,
            }
        profile = self._store[user_id]
        profile["interview_history"].append({
            "score": score,
            "dimensions": dimensions,
            "summary": summary,
            "timestamp": time.time(),
        })
        profile["total_interviews"] = len(profile["interview_history"])
        scores = [h["score"] for h in profile["interview_history"]]
        profile["avg_score"] = sum(scores) / len(scores) if scores else 0.0

    def get_profile(self, user_id: str) -> dict[str, Any]:
        """获取候选人画像。"""
        return self._store.get(user_id, {})

    def get_weak_areas(self, user_id: str) -> list[str]:
        """获取候选人的薄弱领域。"""
        profile = self._store.get(user_id, {})
        return profile.get("weak_areas", [])

    def get_progress(self, user_id: str) -> dict[str, Any]:
        """获取候选人进步轨迹。"""
        profile = self._store.get(user_id, {})
        history = profile.get("interview_history", [])
        if len(history) < 2:
            return {"trend": "insufficient_data", "improvement": 0}

        recent = history[-1]["score"]
        first = history[0]["score"]
        improvement = recent - first
        trend = "up" if improvement > 0 else "down" if improvement < 0 else "stable"
        return {
            "trend": trend,
            "improvement": round(improvement, 1),
            "first_score": first,
            "latest_score": recent,
            "total_interviews": len(history),
        }


class ConversationMemory:
    """对话记忆 — 面试对话的摘要和关键信息提取。

    在面试场景中，长对话需要压缩为关键信息才能有效利用。
    """

    def __init__(self, summary_interval: int = 6):
        self.summary_interval = summary_interval  # 每 N 轮生成一次摘要
        self._full_history: list[dict[str, str]] = []
        self._summaries: list[str] = []
        self._key_points: list[str] = []

    def add_exchange(self, user_msg: str, assistant_msg: str) -> None:
        """添加一轮对话。"""
        self._full_history.append({"role": "user", "content": user_msg})
        self._full_history.append({"role": "assistant", "content": assistant_msg})

    def add_key_point(self, point: str) -> None:
        """记录关键信息点。"""
        self._key_points.append(point)

    def add_summary(self, summary: str) -> None:
        """添加摘要。"""
        self._summaries.append(summary)

    def get_full_history(self, limit: int | None = None) -> list[dict[str, str]]:
        """获取完整对话历史。"""
        if limit:
            return self._full_history[-limit:]
        return self._full_history

    def get_compressed_context(self) -> str:
        """获取压缩后的对话上下文（摘要 + 关键点）。"""
        parts = []
        if self._summaries:
            parts.append("对话摘要: " + " ".join(self._summaries[-3:]))
        if self._key_points:
            parts.append("关键信息: " + "; ".join(self._key_points[-10:]))
        return "\n".join(parts)

    def get_stats(self) -> dict[str, Any]:
        """获取对话统计。"""
        user_msgs = [m for m in self._full_history if m["role"] == "user"]
        total_words = sum(len(m["content"]) for m in user_msgs)
        return {
            "total_exchanges": len(user_msgs),
            "total_user_words": total_words,
            "avg_response_length": total_words / len(user_msgs) if user_msgs else 0,
            "summaries_count": len(self._summaries),
            "key_points_count": len(self._key_points),
        }

    def clear(self) -> None:
        self._full_history.clear()
        self._summaries.clear()
        self._key_points.clear()

    def to_dict(self) -> dict:
        return {
            "full_history": self._full_history,
            "summaries": self._summaries,
            "key_points": self._key_points,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConversationMemory":
        mem = cls()
        mem._full_history = data.get("full_history", [])
        mem._summaries = data.get("summaries", [])
        mem._key_points = data.get("key_points", [])
        return mem


# 全局记忆实例
short_term_memory = ShortTermMemory(max_size=20)
long_term_memory = LongTermMemory()
