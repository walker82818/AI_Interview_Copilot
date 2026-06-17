"""V5: MCP (Model Context Protocol) 工具集。

为 Agent 提供标准化的外部工具调用接口，支持：
- GitHub 仓库分析
- LeetCode 解题记录分析
- 未来可扩展更多 MCP 工具
"""

from dataclasses import dataclass, field
from typing import Any, Callable

import httpx

from src.core.config import settings
from src.core.logger import logger


@dataclass
class MCPTool:
    """MCP 工具定义。"""
    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    handler: Callable | None = None


class MCPRegistry:
    """MCP 工具注册中心。

    注册和管理所有可用的外部工具，Agent 可以按需调用。
    """

    def __init__(self):
        self._tools: dict[str, MCPTool] = {}

    def register(self, tool: MCPTool) -> None:
        self._tools[tool.name] = tool
        logger.info("MCP tool registered: {}", tool.name)

    def get_tool(self, name: str) -> MCPTool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            }
            for t in self._tools.values()
        ]

    async def execute(self, name: str, **kwargs) -> dict[str, Any]:
        """执行指定工具。"""
        tool = self._tools.get(name)
        if not tool:
            return {"error": f"工具 {name} 不存在"}
        if not tool.handler:
            return {"error": f"工具 {name} 未绑定处理函数"}
        try:
            result = await tool.handler(**kwargs)
            return {"success": True, "data": result}
        except Exception as exc:
            logger.error("MCP tool {} error: {}", name, exc)
            return {"error": str(exc)}


# 全局注册中心
mcp_registry = MCPRegistry()


# ── GitHub 分析工具 ────────────────────────────────────────────────


# 通用请求头，避免被 GitHub / LeetCode 拦截
_GITHUB_HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "AI-Interview-Copilot/1.0",
}
_LEETCODE_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
    "Origin": "https://leetcode.com",
    "Referer": "https://leetcode.com/",
}


async def _analyze_github_profile(username: str) -> dict[str, Any]:
    """分析 GitHub 用户公开资料。"""
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        # 获取用户信息
        resp = await client.get(
            f"https://api.github.com/users/{username}",
            headers=_GITHUB_HEADERS,
        )
        if resp.status_code == 403:
            return {"error": "GitHub API 限流，请稍后重试或配置 GitHub Token", "status": 403}
        if resp.status_code == 404:
            return {"error": f"GitHub 用户 {username} 未找到", "status": 404}
        if resp.status_code != 200:
            return {"error": f"GitHub API 请求失败 (HTTP {resp.status_code})", "status": resp.status_code}

        user_data = resp.json()

        # 获取仓库列表
        repos_resp = await client.get(
            f"https://api.github.com/users/{username}/repos?sort=stars&per_page=10",
            headers=_GITHUB_HEADERS,
        )
        repos = repos_resp.json() if repos_resp.status_code == 200 else []

        return {
            "login": user_data.get("login"),
            "name": user_data.get("name"),
            "bio": user_data.get("bio"),
            "public_repos": user_data.get("public_repos"),
            "followers": user_data.get("followers"),
            "top_languages": _extract_languages(repos),
            "top_repos": [
                {
                    "name": r.get("name"),
                    "description": r.get("description"),
                    "language": r.get("language"),
                    "stars": r.get("stargazers_count"),
                    "topics": r.get("topics", []),
                }
                for r in repos[:5]
            ],
        }


def _extract_languages(repos: list[dict]) -> list[dict]:
    """从仓库列表提取语言统计。"""
    lang_count: dict[str, int] = {}
    for repo in repos:
        lang = repo.get("language")
        if lang:
            lang_count[lang] = lang_count.get(lang, 0) + 1
    sorted_langs = sorted(lang_count.items(), key=lambda x: x[1], reverse=True)
    return [{"language": lang, "repos": count} for lang, count in sorted_langs[:8]]


async def _analyze_github_repo(owner: str, repo: str) -> dict[str, Any]:
    """分析指定 GitHub 仓库。"""
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        resp = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}",
            headers=_GITHUB_HEADERS,
        )
        if resp.status_code == 403:
            return {"error": "GitHub API 限流，请稍后重试或配置 GitHub Token", "status": 403}
        if resp.status_code == 404:
            return {"error": f"仓库 {owner}/{repo} 未找到", "status": 404}
        if resp.status_code != 200:
            return {"error": f"GitHub API 请求失败 (HTTP {resp.status_code})", "status": resp.status_code}

        data = resp.json()

        # 获取主要语言
        langs_resp = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/languages",
            headers=_GITHUB_HEADERS,
        )
        languages = langs_resp.json() if langs_resp.status_code == 200 else {}

        return {
            "full_name": data.get("full_name"),
            "description": data.get("description"),
            "language": data.get("language"),
            "stars": data.get("stargazers_count"),
            "forks": data.get("forks_count"),
            "open_issues": data.get("open_issues_count"),
            "topics": data.get("topics", []),
            "languages": languages,
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
        }


# ── LeetCode 分析工具 ──────────────────────────────────────────────


async def _analyze_leetcode_profile(username: str) -> dict[str, Any]:
    """分析 LeetCode 用户公开资料（通过 LeetCode GraphQL API）。"""
    query = """
    query userProfile($username: String!) {
      matchedUser(username: $username) {
        username
        profile { realName ranking }
        submitStats {
          acSubmissionNum { difficulty count }
        }
      }
      userContestRanking(username: $username) {
        rating
        attendedContestsCount
      }
      recentSubmissionList(username: $username, limit: 10) {
        title titleSlug statusDisplay lang
      }
    }
    """
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        resp = await client.post(
            "https://leetcode.com/graphql",
            json={"query": query, "variables": {"username": username}},
            headers=_LEETCODE_HEADERS,
        )
        if resp.status_code == 403:
            return {"error": "LeetCode API 访问被拒绝，可能触发了反爬机制，请稍后重试"}
        if resp.status_code != 200:
            return {"error": f"LeetCode API 请求失败 (HTTP {resp.status_code})"}

        data = resp.json()
        if "errors" in data:
            return {"error": f"LeetCode 用户 {username} 未找到"}

        user = data.get("data", {}).get("matchedUser")
        if not user:
            return {"error": f"LeetCode 用户 {username} 未找到"}

        stats = user.get("submitStats", {}).get("acSubmissionNum", [])
        contest = data.get("data", {}).get("userContestRanking") or {}
        recent = data.get("data", {}).get("recentSubmissionList") or []

        difficulty_map = {}
        for item in stats:
            difficulty_map[item.get("difficulty", "")] = item.get("count", 0)

        return {
            "username": username,
            "ranking": user.get("profile", {}).get("ranking"),
            "total_solved": sum(d.get("count", 0) for d in stats),
            "easy": difficulty_map.get("Easy", 0),
            "medium": difficulty_map.get("Medium", 0),
            "hard": difficulty_map.get("Hard", 0),
            "contest_rating": contest.get("rating"),
            "contests_attended": contest.get("attendedContestsCount"),
            "recent_submissions": [
                {
                    "title": s.get("title"),
                    "language": s.get("lang"),
                }
                for s in recent[:5]
            ],
        }


# ── 注册工具 ────────────────────────────────────────────────────────


def register_mcp_tools() -> None:
    """注册所有 MCP 工具。"""
    mcp_registry.register(MCPTool(
        name="github_profile",
        description="分析 GitHub 用户公开资料，包括仓库、语言偏好、贡献统计",
        parameters={
            "username": {"type": "string", "description": "GitHub 用户名"},
        },
        handler=_analyze_github_profile,
    ))

    mcp_registry.register(MCPTool(
        name="github_repo",
        description="分析指定 GitHub 仓库的详细信息",
        parameters={
            "owner": {"type": "string", "description": "仓库所有者"},
            "repo": {"type": "string", "description": "仓库名称"},
        },
        handler=_analyze_github_repo,
    ))

    mcp_registry.register(MCPTool(
        name="leetcode_profile",
        description="分析 LeetCode 用户解题数据，包括刷题统计和竞赛排名",
        parameters={
            "username": {"type": "string", "description": "LeetCode 用户名"},
        },
        handler=_analyze_leetcode_profile,
    ))

    logger.info("MCP tools registered: {}", len(mcp_registry._tools))


# 启动时注册
register_mcp_tools()
