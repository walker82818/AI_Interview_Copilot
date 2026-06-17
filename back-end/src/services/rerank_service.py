from src.core.config import settings
from src.core.logger import logger


class RerankService:
    """BGE-Reranker 重排序。"""

    def __init__(self) -> None:
        self.model_name = settings.rerank_model

    async def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int = 3,
    ) -> list[tuple[str, float]]:
        if not documents:
            return []
        logger.debug("Reranking {} docs with {}", len(documents), self.model_name)
        # TODO: 接入 BGE-Reranker
        scored = [(doc, 1.0 - i * 0.01) for i, doc in enumerate(documents)]
        return scored[:top_k]


rerank_service = RerankService()
