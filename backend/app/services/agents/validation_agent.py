"""
Validation Agent - Domain specialist for Master DB data quality gatekeeping.

ISOLATION: Creates its own MasterDataGatekeeper inside execute().
EXPERTISE: Validates items with category-specific rules, provides
           per-item verdicts (APPROVED/PENDING/REJECTED) with detailed reasons.
"""
from typing import Any, Dict, List

from app.services.agents.base_agent import BaseAgent, AgentReport, AgentStatus


class ValidationAgent(BaseAgent):
    name = "validation"
    description = "Chuyên gia kiểm duyệt chất lượng dữ liệu trước khi thêm vào Master DB"

    def execute(self, task: Dict[str, Any]) -> AgentReport:
        """
        Task keys:
            items (list[dict]): Items to validate. Each dict should have
                                'normalized_description' or 'description'.
            category (str, optional): Work category hint
        """
        items = task.get("items", [])
        if not items:
            return AgentReport.fail(self.name, "Thiếu 'items' trong task")

        # CREATE OWN SERVICE INSTANCE
        from app.services.master_data_gatekeeper import MasterDataGatekeeper
        gatekeeper = MasterDataGatekeeper()

        category = task.get("category")

        findings = []
        approved = 0
        pending = 0
        rejected = 0
        skipped = 0

        for i, item in enumerate(items):
            result = gatekeeper.validate(item, category=category)
            finding = {
                "index": i,
                "description": item.get("normalized_description") or item.get("description", ""),
                "status": result.status,
                "score": result.score,
                "reasons": result.reasons,
                "indicators": result.indicators,
                "defaults_applied": result.defaults_applied,
            }
            findings.append(finding)

            if result.status == "APPROVED":
                approved += 1
            elif result.status == "PENDING_REVIEW":
                pending += 1
            elif result.status == "REJECTED":
                rejected += 1
            else:
                skipped += 1

        total = len(findings)
        recommendations = []
        if approved > 0:
            recommendations.append(f"{approved} items đạt chuẩn - sẵn sàng thêm vào Master DB.")
        if pending > 0:
            recommendations.append(f"{pending} items cần review thủ công trước khi thêm.")
        if rejected > 0:
            rejected_descs = [
                f["description"][:40] for f in findings if f["status"] == "REJECTED"
            ][:3]
            recommendations.append(
                f"{rejected} items bị từ chối. Ví dụ: {rejected_descs}"
            )

        human_summary = (
            f"Kiểm duyệt {total} items. "
            f"Kết quả: {approved} approved, {pending} pending review, "
            f"{rejected} rejected, {skipped} skipped."
        )

        return AgentReport(
            agent_name=self.name,
            status=AgentStatus.COMPLETED,
            findings=findings,
            recommendations=recommendations,
            human_summary=human_summary,
            metrics={
                "total": total,
                "approved": approved,
                "pending": pending,
                "rejected": rejected,
                "skipped": skipped,
            },
        )
