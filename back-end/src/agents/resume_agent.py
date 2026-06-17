"""V3: 简历分析 Agent — 多步推理、结构化输出校验、技能图谱。"""

import json
import re

from src.core.logger import logger
from src.services.llm_service import llm_service
from src.utils.prompt_builder import build_resume_analysis_prompt


class ResumeAgent:
    """简历分析智能体。

    采用两步分析策略：
    1. 快速提取：从原始文本提取技能/经历/学历
    2. 深度推理：对提取结果进行归类、去重、级别推断
    """

    SKILL_CATEGORIES = {
        "编程语言": ["python", "java", "go", "rust", "c++", "c", "typescript", "javascript",
                     "kotlin", "swift", "scala", "ruby", "php", "dart", "lua"],
        "框架": ["react", "vue", "angular", "django", "flask", "fastapi", "spring",
                "express", "nestjs", "gin", "echo", "fiber", "laravel", "rails"],
        "数据库": ["mysql", "postgresql", "mongodb", "redis", "elasticsearch",
                  "cassandra", "dynamodb", "neo4j", "tidb", "clickhouse"],
        "云平台": ["aws", "azure", "gcp", "阿里云", "腾讯云", "docker", "kubernetes",
                  "terraform", "jenkins", "github actions", "gitlab ci"],
        "AI/ML": ["机器学习", "深度学习", "nlp", "cv", "tensorflow", "pytorch",
                  "transformer", "llm", "rag", "langchain"],
        "软技能": ["项目管理", "团队协作", "沟通", "领导力", "敏捷", "scrum"],
    }

    async def analyze(self, text: str) -> dict:
        """多步分析：提取 → 分类 → 级别推断。"""
        logger.info("ResumeAgent: starting multi-step analysis")

        # Step 1: 快速提取
        raw = await self._extract_raw(text)
        skills = raw.get("skills", [])
        experience = raw.get("experience", [])
        education = raw.get("education", [])
        summary = raw.get("summary", "")

        # Step 2: 技能分类
        categorized = self._categorize_skills(skills)

        # Step 3: 年限推断
        years = self._infer_years(text)

        return {
            "skills": skills,
            "skill_categories": categorized,
            "experience": experience,
            "education": education,
            "summary": summary,
            "years_of_experience": years,
        }

    async def _extract_raw(self, text: str) -> dict:
        messages = build_resume_analysis_prompt(text)
        raw = await llm_service.chat(messages)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("ResumeAgent: JSON decode failed, using fallback")
            return {"skills": [], "experience": [], "education": [], "summary": raw[:500]}

    def _categorize_skills(self, skills: list[str]) -> dict[str, list[str]]:
        """将技能按类别分组。"""
        result: dict[str, list[str]] = {}
        for skill in skills:
            skill_lower = skill.lower()
            categorized = False
            for category, keywords in self.SKILL_CATEGORIES.items():
                if any(kw in skill_lower for kw in keywords):
                    result.setdefault(category, []).append(skill)
                    categorized = True
                    break
            if not categorized:
                result.setdefault("其他", []).append(skill)
        return result

    def _infer_years(self, text: str) -> int | None:
        """从文本推断工作年限。"""
        patterns = [
            r"(\d+)\s*年.*?工作经验",
            r"工作经验[：:]\s*(\d+)\s*年",
            r"(\d+)\+?\s*年.*?开发经验",
            r"从业\s*(\d+)\s*年",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        return None


resume_agent = ResumeAgent()
