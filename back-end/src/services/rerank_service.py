import httpx

from src.core.config import settings
from src.core.logger import logger


class RerankService:
    """Rerank 重排序 — 对接阿里百炼 qwen3-rerank / Cohere / Jina 等模型。

    通过 OpenAI 兼容的 /v1/rerank 接口调用，按语义相关性对文档重新排序。
    """

    def __init__(self) -> None:
        self.api_key = settings.llm_api_key
        self.base_url = settings.llm_base_url.rstrip("/")
        self.model = settings.rerank_model

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int = 3,
    ) -> list[tuple[str, float]]:
        if not documents:
            return []

        if not self.is_configured:
            logger.warning("LLM API key not set, using fallback rerank ordering")
            return self._fallback_rerank(documents, top_k)

        try:
            return await self._call_rerank_api(query, documents, top_k)
        except Exception as e:
            logger.error("Rerank API failed: {}, falling back to original order", e)
            return self._fallback_rerank(documents, top_k)

    async def _call_rerank_api(
        self,
        query: str,
        documents: list[str],
        top_k: int,
    ) -> list[tuple[str, float]]:
        """调用 OpenAI 兼容的 /v1/rerank 接口。"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/rerank",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "query": query,
                    "documents": documents,
                    "top_n": top_k,
                },
            )
            response.raise_for_status()
            data = response.json()

        # 标准 Rerank API 返回格式: {"results": [{"index": 0, "relevance_score": 0.95}, ...]}
        results = data.get("results", [])
        if not results:
            logger.warning("Rerank API returned empty results, falling back")
            return self._fallback_rerank(documents, top_k)

        scored = [
            (documents[r["index"]], r["relevance_score"])
            for r in sorted(results, key=lambda x: x["relevance_score"], reverse=True)
        ]
        logger.info(
            "Reranked {} docs → top {} (model={})",
            len(documents), len(scored[:top_k]), self.model,
        )
        return scored[:top_k]

    @staticmethod
    def _fallback_rerank(
        documents: list[str], top_k: int
    ) -> list[tuple[str, float]]:
        """API 不可用时的兜底：保持原始检索顺序。"""
        scored = [(doc, 1.0 - i * 0.01) for i, doc in enumerate(documents)]
        return scored[:top_k]


rerank_service = RerankService()
