from src.core.logger import logger
from src.services.llm_service import llm_service
from src.services.retrieval_service import retrieval_service
from src.services.rerank_service import rerank_service
from src.utils.prompt_builder import build_rag_prompt


class RAGService:
    """RAG 核心：检索 → Prompt 构造 → LLM 生成。"""

    async def retrieve_context(
        self,
        query: str,
        top_k: int = 5,
        rerank_top_k: int = 3,
        filter_expr: str | None = None,
    ) -> list[str]:
        hits = await retrieval_service.search(query, top_k=top_k, filter_expr=filter_expr)
        texts = [h["text"] for h in hits if h.get("text")]
        if not texts:
            return []
        reranked = await rerank_service.rerank(query, texts, top_k=rerank_top_k)
        return [doc for doc, _ in reranked]

    async def generate(
        self,
        question: str,
        resume_summary: str = "",
        jd_summary: str = "",
        filter_expr: str | None = None,
        conversation_history: list[dict[str, str]] | None = None,
        interview_stage: str = "",
    ) -> str:
        context_chunks = await self.retrieve_context(question, filter_expr=filter_expr)
        messages = build_rag_prompt(
            question=question,
            context_chunks=context_chunks,
            resume_summary=resume_summary,
            jd_summary=jd_summary,
            conversation_history=conversation_history,
            interview_stage=interview_stage,
        )
        logger.info("RAG generate with {} context chunks, stage={}", len(context_chunks), interview_stage)
        return await llm_service.chat(messages)

    async def generate_stream(
        self,
        question: str,
        resume_summary: str = "",
        jd_summary: str = "",
        filter_expr: str | None = None,
        conversation_history: list[dict[str, str]] | None = None,
        interview_stage: str = "",
    ):
        context_chunks = await self.retrieve_context(question, filter_expr=filter_expr)
        messages = build_rag_prompt(
            question=question,
            context_chunks=context_chunks,
            resume_summary=resume_summary,
            jd_summary=jd_summary,
            conversation_history=conversation_history,
            interview_stage=interview_stage,
        )
        logger.info("RAG stream with {} context chunks, stage={}", len(context_chunks), interview_stage)
        async for token in llm_service.chat_stream(messages):
            yield token


rag_service = RAGService()
