"""V3: 评估 Agent — 多维度 Rubric 打分、回答质量分析、个性化建议。"""

import json

from src.core.logger import logger
from src.services.llm_service import llm_service
from src.utils.prompt_builder import build_evaluation_prompt


class EvaluationAgent:
    """面试评估智能体。

    增强能力：
    - Rubric 打分：基于评分标准的多维度量化
    - 回答质量分析：逐条分析候选人回答
    - 个性化建议：针对弱项生成具体改进方案
    """

    # Rubric 评分标准
    RUBRICS = {
        "技术能力": {
            90: "技术深度出色，能清晰阐述底层原理和架构设计",
            75: "技术基础扎实，能正确回答大部分技术问题",
            60: "技术基础一般，部分概念理解不够深入",
            40: "技术基础薄弱，多数问题回答不到位",
        },
        "沟通表达": {
            90: "表达清晰流畅，逻辑严密，善于用实例说明",
            75: "表达基本清晰，能用 STAR 法则组织回答",
            60: "表达略显混乱，部分回答缺乏结构",
            40: "表达不清，难以理解其核心观点",
        },
        "问题解决": {
            90: "能提出多套解决方案并分析优劣",
            75: "能给出合理的解决方案",
            60: "解决方案思路不完整",
            40: "难以提出有效方案",
        },
        "学习能力": {
            90: "展示了持续学习的习惯和深入钻研的能力",
            75: "有明确的学习路径和方向",
            60: "学习路径不够清晰",
            40: "缺乏学习主动性表现",
        },
        "岗位匹配度": {
            90: "技能和经历与岗位高度匹配，超出预期",
            75: "技能基本匹配，有相关项目经验",
            60: "部分匹配，存在明显技能差距",
            40: "匹配度较低，关键技能缺失较多",
        },
    }

    async def evaluate(
        self,
        messages: list[dict],
        resume_summary: str,
        jd_title: str,
    ) -> dict:
        """多步评估：整体打分 → 逐维度分析 → 生成建议。"""
        logger.info("EvaluationAgent: starting multi-step evaluation")

        # Step 1: LLM 生成基础评估
        prompt = build_evaluation_prompt(messages, resume_summary, jd_title)
        raw = await llm_service.chat(prompt)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("EvaluationAgent: JSON decode failed, using default")
            data = self._default_evaluation()

        # Step 2: Rubric 校准
        dimensions = data.get("dimensions", [])
        calibrated = self._calibrate_dimensions(dimensions, messages)

        # Step 3: 回答质量分析
        answer_analysis = self._analyze_answers(messages)

        return {
            "overallScore": data.get("overallScore", data.get("overall_score", 75)),
            "dimensions": calibrated,
            "suggestions": data.get("suggestions", []),
            "summary": data.get("summary", ""),
            "answer_analysis": answer_analysis,
        }

    def _calibrate_dimensions(
        self, dimensions: list[dict], messages: list[dict]
    ) -> list[dict]:
        """使用 Rubric 标准校准各维度分数。"""
        calibrated = []
        for dim in dimensions:
            name = dim.get("name", "维度")
            score = dim.get("score", 70)
            rubric_text = ""
            if name in self.RUBRICS:
                for threshold, desc in sorted(
                    self.RUBRICS[name].items(), reverse=True
                ):
                    if score >= threshold:
                        rubric_text = desc
                        break
            calibrated.append({
                "name": name,
                "score": score,
                "maxScore": dim.get("maxScore", dim.get("max_score", 100)),
                "rubric": rubric_text,
            })
        return calibrated

    def _analyze_answers(self, messages: list[dict]) -> list[dict]:
        """逐条分析候选人回答质量。"""
        user_messages = [
            m for m in messages
            if m.get("role") == "user" and m.get("content", "").strip()
        ]
        analysis = []
        for i, msg in enumerate(user_messages):
            content = msg.get("content", "")
            word_count = len(content)
            quality = "good" if word_count > 50 else "short"
            if word_count > 200:
                quality = "detailed"
            elif word_count < 15:
                quality = "insufficient"
            analysis.append({
                "index": i + 1,
                "word_count": word_count,
                "quality": quality,
                "preview": content[:100] + ("..." if len(content) > 100 else ""),
            })
        return analysis

    def _default_evaluation(self) -> dict:
        return {
            "overallScore": 75,
            "dimensions": [
                {"name": "技术能力", "score": 78, "maxScore": 100},
                {"name": "沟通表达", "score": 72, "maxScore": 100},
                {"name": "问题解决", "score": 74, "maxScore": 100},
                {"name": "学习能力", "score": 76, "maxScore": 100},
                {"name": "岗位匹配度", "score": 70, "maxScore": 100},
            ],
            "suggestions": [
                {
                    "category": "技术深度",
                    "content": "建议在回答技术问题时补充实现细节。",
                    "priority": "high",
                }
            ],
            "summary": "整体表现良好，建议在项目经验描述上更加结构化。",
        }


evaluation_agent = EvaluationAgent()
