"""
Matching Agent - Domain specialist for BOQ description matching against Master DB.

ISOLATION: Creates its own HybridMatcherService inside execute().
EXPERTISE: Analyzes match quality, categorizes results, provides
           detailed per-item findings and recommendations.
"""
from typing import Any, Dict, List

from app.services.agents.base_agent import BaseAgent, AgentReport, AgentStatus


class MatchingAgent(BaseAgent):
    name = "matching"
    description = "Chuyên gia đối soát mô tả với Master DB (3-tier hybrid matching)"

    def execute(self, task: Dict[str, Any]) -> AgentReport:
        """
        Task keys:
            descriptions (list[str]): Normalized descriptions to match
            db_url (str): Database connection URL (for creating own session)
            method (str): '3_tier' (default) or 'semantic_only'
        """
        descriptions = task.get("descriptions", [])
        if not descriptions:
            return AgentReport.fail(self.name, "Thiếu 'descriptions' trong task")

        # CREATE OWN SERVICE INSTANCE
        from app.services.hybrid_matcher import HybridMatcherService
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            matcher = HybridMatcherService(db)
            matcher.initialize()

            method = task.get("method", "3_tier")
            if method == "semantic_only":
                results = matcher.match_batch_semantic_only(descriptions)
            else:
                results = matcher.match_batch(descriptions)

            # EXPERT ANALYSIS
            findings = []
            exact_count = 0
            fuzzy_count = 0
            new_count = 0

            for i, match_result in enumerate(results):
                match_type = match_result.match_type
                finding = {
                    "index": i,
                    "query": match_result.query,
                    "match_type": match_type,
                    "similarity_score": match_result.similarity_score,
                    "matched_tier": match_result.matched_tier,
                    "master_id": match_result.master_id,
                    "work_code": match_result.work_code,
                    "master_description": match_result.master_description,
                }
                findings.append(finding)

                if match_type == "exact":
                    exact_count += 1
                elif match_type == "fuzzy":
                    fuzzy_count += 1
                else:
                    new_count += 1

            total = len(findings)
            recommendations = []
            if new_count > 0:
                recommendations.append(
                    f"{new_count} items mới chưa có trong Master DB - "
                    f"cần qua validation trước khi thêm."
                )
            if fuzzy_count > 0:
                recommendations.append(
                    f"{fuzzy_count} items fuzzy match (80-94%) - nên review thủ công."
                )
            if exact_count == total:
                recommendations.append("Tất cả items đã match chính xác trong Master DB.")

            human_summary = (
                f"Đối soát {total} mô tả với Master DB. "
                f"Kết quả: {exact_count} exact match, {fuzzy_count} fuzzy match, {new_count} mới. "
                f"Phương pháp: {method}."
            )

            return AgentReport(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                findings=findings,
                recommendations=recommendations,
                human_summary=human_summary,
                metrics={
                    "total": total,
                    "exact": exact_count,
                    "fuzzy": fuzzy_count,
                    "new": new_count,
                    "method": method,
                },
            )
        finally:
            db.close()
