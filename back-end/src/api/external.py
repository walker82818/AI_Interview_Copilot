"""V5: 外部分析 API — GitHub / LeetCode 数据获取。

提供候选人外部数据源的分析能力，辅助面试评估。
"""

from fastapi import APIRouter, HTTPException, Query, status

from src.agents.mcp_tools import mcp_registry

router = APIRouter()


@router.get("/github/profile")
async def analyze_github_profile(
    username: str = Query(..., min_length=1, description="GitHub 用户名"),
):
    """分析 GitHub 用户公开资料。"""
    result = await mcp_registry.execute("github_profile", username=username)
    if "error" in result:
        status_code = result.get("status", status.HTTP_404_NOT_FOUND)
        raise HTTPException(
            status_code=status_code,
            detail=result["error"],
        )
    return result["data"]


@router.get("/github/repo")
async def analyze_github_repo(
    owner: str = Query(..., min_length=1, description="仓库所有者"),
    repo: str = Query(..., min_length=1, description="仓库名称"),
):
    """分析指定 GitHub 仓库。"""
    result = await mcp_registry.execute("github_repo", owner=owner, repo=repo)
    if "error" in result:
        status_code = result.get("status", status.HTTP_404_NOT_FOUND)
        raise HTTPException(
            status_code=status_code,
            detail=result["error"],
        )
    return result["data"]


@router.get("/leetcode/profile")
async def analyze_leetcode_profile(
    username: str = Query(..., min_length=1, description="LeetCode 用户名"),
):
    """分析 LeetCode 用户解题数据。"""
    result = await mcp_registry.execute("leetcode_profile", username=username)
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=result["error"],
        )
    return result["data"]


@router.get("/tools")
async def list_available_tools():
    """列出所有可用的外部分析工具。"""
    return {"tools": mcp_registry.list_tools()}
