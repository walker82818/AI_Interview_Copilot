from typing import Any


def build_rag_prompt(
    question: str,
    context_chunks: list[str],
    resume_summary: str = "",
    jd_summary: str = "",
    conversation_history: list[dict[str, str]] | None = None,
    interview_stage: str = "",
) -> list[dict[str, str]]:
    context = "\n\n".join(f"[{i + 1}] {c}" for i, c in enumerate(context_chunks))
    system = (
        "你是一位经验丰富的专业 AI 面试官。你的任务是：\n"
        "1. 根据候选人简历、岗位 JD 和检索到的上下文，提出有针对性的面试问题或追问\n"
        "2. 回答简洁、专业，一次只问一个问题\n"
        "3. 不要重复已经问过的问题，要根据候选人的回答自然地深入追问\n"
        "4. 保持友善但专业的态度\n"
    )
    if interview_stage:
        system += f"\n当前面试阶段: {interview_stage}"
    user_parts = []
    if resume_summary:
        user_parts.append(f"## 简历摘要\n{resume_summary}")
    if jd_summary:
        user_parts.append(f"## 岗位 JD\n{jd_summary}")
    if context:
        user_parts.append(f"## 检索上下文\n{context}")
    if conversation_history:
        history_text = "\n".join(
            f"{m['role']}: {m['content']}" for m in conversation_history[-6:]
        )
        user_parts.append(f"## 对话历史\n{history_text}")
    user_parts.append(f"## 当前输入\n{question}")
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": "\n\n".join(user_parts)},
    ]


def build_interview_opening_prompt(
    resume_summary: str,
    jd_summary: str,
    jd_title: str = "",
) -> list[dict[str, str]]:
    """生成面试开场白。"""
    return [
        {
            "role": "system",
            "content": (
                "你是一位专业友好的 AI 面试官。请根据候选人的简历和岗位 JD，"
                "生成一段简短的面试开场白，包括：\n"
                "1. 欢迎语\n"
                "2. 简要说明面试岗位\n"
                "3. 请候选人做自我介绍\n"
                "保持热情但专业，不超过 3 句话。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"岗位: {jd_title}\n"
                f"岗位要求摘要: {jd_summary[:500]}\n"
                f"候选人背景摘要: {resume_summary[:500]}"
            ),
        },
    ]


def build_interview_closing_prompt(
    conversation_history: list[dict[str, str]],
) -> list[dict[str, str]]:
    """生成面试结束语。"""
    history_text = "\n".join(
        f"{m['role']}: {m['content']}" for m in conversation_history[-10:]
    )
    return [
        {
            "role": "system",
            "content": (
                "你是 AI 面试官，面试即将结束。请生成一段结束语：\n"
                "1. 感谢候选人参与面试\n"
                "2. 简短总结面试内容\n"
                "3. 告知后续会生成评分报告\n"
                "保持鼓励和专业，不超过 3 句话。"
            ),
        },
        {
            "role": "user",
            "content": f"对话记录:\n{history_text}",
        },
    ]


def build_resume_analysis_prompt(text: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "你是简历分析专家。请从简历中提取技能、工作经历、学历和摘要。"
                "必须严格按照以下 JSON 格式输出，不要包含任何其他内容：\n"
                '{"skills": ["技能1", "技能2"], "experience": ["经历1", "经历2"], '
                '"education": ["学历1"], "summary": "一句话摘要"}'
            ),
        },
        {"role": "user", "content": text[:8000]},
    ]


def build_jd_analysis_prompt(text: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "你是 HR 专家，请分析岗位 JD，提取必备技能、加分技能和职责描述。"
                "必须严格按照以下 JSON 格式输出，不要包含任何其他内容：\n"
                '{"required_skills": ["技能1"], "preferred_skills": ["技能2"], '
                '"responsibilities": ["职责1"], "summary": "一句话摘要"}'
            ),
        },
        {"role": "user", "content": text[:8000]},
    ]


def build_evaluation_prompt(
    messages: list[dict[str, Any]],
    resume_summary: str,
    jd_title: str,
) -> list[dict[str, str]]:
    history = "\n".join(
        f"{m['role']}: {m['content']}" for m in messages if m.get("content")
    )
    return [
        {
            "role": "system",
            "content": (
                "你是专业的面试评估专家。请根据以下面试对话记录、候选人简历和岗位要求，"
                "给出全面的面试评估。\n\n"
                "评估要求：\n"
                "1. 综合评分（0-100）\n"
                "2. 多维度评分（技术能力、沟通表达、问题解决、学习能力、岗位匹配度），每个维度 0-100 分\n"
                "3. 3-5 条具体的学习改进建议，按优先级分类（high/medium/low）\n"
                "4. 一段总结性评语\n\n"
                "请严格按照以下 JSON 格式输出，不要包含任何其他内容：\n"
                '{"overallScore": 85, '
                '"dimensions": [{"name": "技术能力", "score": 85, "maxScore": 100}, ...], '
                '"suggestions": [{"category": "技术深度", "content": "建议...", "priority": "high"}, ...], '
                '"summary": "整体评估总结..."}'
            ),
        },
        {
            "role": "user",
            "content": (
                f"岗位: {jd_title}\n简历摘要: {resume_summary}\n\n对话记录:\n{history}"
            ),
        },
    ]
