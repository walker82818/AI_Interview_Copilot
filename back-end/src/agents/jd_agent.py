"""V3: JD 分析 Agent — 技能图谱、级别推断、岗位画像。"""

import json

from src.core.logger import logger
from src.services.llm_service import llm_service
from src.utils.prompt_builder import build_jd_analysis_prompt


class JDAgent:
    """JD 分析智能体。

    增强能力：
    - 技能分级（初级/中级/高级/专家）
    - 岗位级别推断（Junior/Mid/Senior/Staff）
    - 生成岗位画像
    """

    LEVEL_KEYWORDS = {
        "junior": ["应届", "初级", "junior", "1-3年", "1-3 年", "毕业生", "实习"],
        "mid": ["中级", "mid", "3-5年", "3-5 年"],
        "senior": ["高级", "senior", "5-10年", "5-10 年", "资深"],
        "staff": ["专家", "staff", "架构师", "10年", "10 年", "principal", "lead"],
    }

    async def analyze(self, text: str) -> dict:
        """多步分析：提取技能 → 分级 → 推断岗位级别。"""
        logger.info("JDAgent: starting multi-step analysis")

        # Step 1: 基础提取
        raw = await self._extract_raw(text)
        required_skills = raw.get("requiredSkills", raw.get("required_skills", []))
        preferred_skills = raw.get("preferredSkills", raw.get("preferred_skills", []))
        responsibilities = raw.get("responsibilities", [])
        summary = raw.get("summary", "")

        # Step 2: 技能分级
        graded_required = self._grade_skills(required_skills, text)
        graded_preferred = self._grade_skills(preferred_skills, text)

        # Step 3: 岗位级别推断
        level = self._infer_level(text)

        # Step 4: 岗位画像
        profile = self._build_profile(text, graded_required, responsibilities)

        return {
            "required_skills": graded_required,
            "preferred_skills": graded_preferred,
            "responsibilities": responsibilities,
            "summary": summary,
            "level": level,
            "profile": profile,
        }

    async def _extract_raw(self, text: str) -> dict:
        messages = build_jd_analysis_prompt(text)
        raw = await llm_service.chat(messages)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("JDAgent: JSON decode failed, using fallback")
            return {
                "requiredSkills": [],
                "preferredSkills": [],
                "responsibilities": [raw[:300]],
                "summary": raw[:200],
            }

    def _grade_skills(self, skills: list[str], text: str) -> list[dict]:
        """为技能推断要求级别。"""
        graded = []
        for skill in skills:
            level = "中级"
            text_lower = text.lower()
            if f"精通 {skill}" in text or f"精通{skill}" in text:
                level = "专家"
            elif f"熟悉 {skill}" in text or f"熟悉{skill}" in text:
                level = "中级"
            elif f"了解 {skill}" in text or f"了解{skill}" in text:
                level = "初级"
            graded.append({"name": skill, "level": level})
        return graded

    def _infer_level(self, text: str) -> str:
        text_lower = text.lower()
        for level, keywords in self.LEVEL_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                return level
        return "mid"

    def _build_profile(
        self, text: str, skills: list[dict], responsibilities: list[str]
    ) -> str:
        """生成岗位画像摘要。"""
        tech_stack = [s["name"] for s in skills[:5]]
        duties = responsibilities[:3]
        parts = []
        if tech_stack:
            parts.append(f"核心技术栈: {', '.join(tech_stack)}")
        if duties:
            parts.append(f"主要职责: {'; '.join(duties)}")
        return "。".join(parts) if parts else text[:300]


jd_agent = JDAgent()
