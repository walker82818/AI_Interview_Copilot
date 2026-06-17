from src.core.logger import logger
from src.db.milvus import get_collection
from src.services.embedding_service import embedding_service


class RetrievalService:
    """Milvus 向量检索。"""

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter_expr: str | None = None,
    ) -> list[dict]:
        collection = get_collection()
        if collection is None:
            logger.warning("Milvus unavailable, returning empty retrieval results")
            return []

        query_vector = await embedding_service.embed_query(query)
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
        results = collection.search(
            data=[query_vector],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=filter_expr,
            output_fields=["text", "doc_id", "chunk_index"],
        )

        hits: list[dict] = []
        for hit in results[0]:
            hits.append(
                {
                    "text": hit.entity.get("text", ""),
                    "score": hit.distance,
                    "doc_id": hit.entity.get("doc_id"),
                    "chunk_index": hit.entity.get("chunk_index"),
                }
            )
        return hits


retrieval_service = RetrievalService()
