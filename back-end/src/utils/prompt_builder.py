from typing import Any


def build_rag_prompt(
    question: str,
    context_chunks: list[str],
    resume_summary: str = "",
    jd_summary: str = "",
) -> list[dict[str, str]]:
    context = "\n\n".join(f"[{i + 1}] {c}" for i, c in enumerate(context_chunks))
    system = (
        "你是一位专业的 AI 面试官。根据候选人简历、岗位 JD 和检索到的上下文，"
        "提出有针对性的面试问题或追问。回答简洁、专业，一次只问一个问题。"
    )
    user_parts = []
    if resume_summary:
        user_parts.append(f"## 简历摘要\n{resume_summary}")
    if jd_summary:
        user_parts.append(f"## 岗位 JD\n{jd_summary}")
    if context:
        user_parts.append(f"## 检索上下文\n{context}")
    user_parts.append(f"## 当前输入\n{question}")
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": "\n\n".join(user_parts)},
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
                "你是面试评估专家。根据面试对话、简历和岗位，"
                "给出综合评分、各维度得分和学习建议。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"岗位: {jd_title}\n简历摘要: {resume_summary}\n\n对话记录:\n{history}"
            ),
        },
    ]
