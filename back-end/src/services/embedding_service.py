import httpx

from src.core.config import settings
from src.core.logger import logger

# 百炼 embedding 模型 → 维度映射
_EMBEDDING_DIMENSIONS: dict[str, int] = {
    "text-embedding-v1": 1536,
    "text-embedding-v2": 1536,
    "text-embedding-v3": 1024,
    "text-embedding-v4": 1024,
}


class EmbeddingService:
    """阿里百炼 Embedding 服务（OpenAI 兼容接口）。"""

    def __init__(self) -> None:
        self.api_key = settings.llm_api_key
        self.base_url = settings.llm_base_url.rstrip("/")
        self.model_name = settings.embedding_model
        self._dimension = _EMBEDDING_DIMENSIONS.get(self.model_name, 1024)

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        if not self.api_key:
            logger.warning("LLM API key not set, returning zero vectors")
            return [[0.0] * self._dimension for _ in texts]

        logger.debug("Embedding {} texts with {}", len(texts), self.model_name)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_name,
                    "input": texts,
                },
            )
            response.raise_for_status()
            data = response.json()
            # OpenAI 兼容格式: data[].embedding
            return [item["embedding"] for item in data["data"]]

    async def embed_query(self, query: str) -> list[float]:
        vectors = await self.embed_texts([query])
        return vectors[0] if vectors else [0.0] * self._dimension


embedding_service = EmbeddingService()
