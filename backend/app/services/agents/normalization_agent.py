"""
Normalization Agent - Domain specialist for Vietnamese construction description normalization.

ISOLATION: Creates its own NormalizationOrchestrator inside execute().
           No shared state between calls.
EXPERTISE: Analyzes normalization quality per-item, detects patterns,
           provides actionable findings and human-readable summary.
"""
import re
from typing import Any, Dict, List

from app.services.agents.base_agent import BaseAgent, AgentReport, AgentStatus


# Patterns for detecting specs and materials in text
_SPEC_PATTERN = re.compile(
    r'(?:M\d+|D\d+|K\d+|\d+x\d+|\d+mm|\d+cm|\d+m\b|PN\d+|'
    r'\d+MPa|Φ\d+|φ\d+|@\d+|\d+kg|\d+kN|\d+A|\d+kV|'
    r'\d+mm2|\d+kW|\d+HP|\d+m3|\d+m²)',
    re.IGNORECASE
)
_MATERIAL_PATTERN = re.compile(
    r'(?:bê tông|thép|nhựa|HDPE|PVC|UPVC|đồng|nhôm|inox|'
    r'gang|composite|PE|PP|PPR|Cu|XLPE|thạch cao|granite|'
    r'ceramic|gạch|đá|gỗ|kính|sơn|bitum|BTN|CPĐD|xi măng)',
    re.IGNORECASE
)

# Thresholds
_CONFIDENCE_BAD = 50.0
_CONFIDENCE_WARN = 70.0
_INFO_LOSS_CRITICAL = 0.5


class NormalizationAgent(BaseAgent):
    name = "normalization"
    description = "Chuyên gia chuẩn hóa mô tả công tác xây dựng tiếng Việt"

    def execute(self, task: Dict[str, Any]) -> AgentReport:
        """
        Task keys:
            descriptions (list[str]): Raw BOQ descriptions to normalize
            enable_ai (bool): Enable AI-enhanced normalization (default False)
        """
        descriptions = task.get("descriptions", [])
        if not descriptions:
            return AgentReport.fail(self.name, "Thiếu 'descriptions' trong task")

        # CREATE OWN SERVICE INSTANCE - no shared state
        from app.services.normalization_orchestrator import NormalizationOrchestrator
        orchestrator = NormalizationOrchestrator(
            enable_ai=task.get("enable_ai", False)
        )

        # Process each item and analyze quality
        findings = []
        good_count = 0
        warn_count = 0
        bad_count = 0
        blocked_indices = []

        for i, desc in enumerate(descriptions):
            # Normalize
            result = orchestrator.normalize(desc)
            result_dict = result.to_dict()

            # EXPERT ANALYSIS: per-item quality review
            review = self._review_item(desc, result_dict)
            finding = {
                "index": i,
                "original": desc,
                "normalized": result_dict["normalized"],
                "confidence": result_dict["confidence"],
                "work_category": result_dict["work_category"],
                "normalizer_used": result_dict["normalizer_used"],
                "specs": result_dict.get("specs", {}),
                "verdict": review["verdict"],
                "issues": review["issues"],
                "info_lost": review["info_lost"],
                "pass": review["pass"],
            }
            findings.append(finding)

            if review["verdict"] == "GOOD":
                good_count += 1
            elif review["verdict"] == "FIXABLE":
                warn_count += 1
            else:
                bad_count += 1
                blocked_indices.append(i)

        total = len(findings)
        pass_rate = round((total - bad_count) / total * 100, 1) if total else 0

        # Build recommendations
        recommendations = []
        if bad_count > 0:
            recommendations.append(
                f"{bad_count} items bị chặn (BAD) - không chuyển sang matching. "
                f"Indices: {blocked_indices}"
            )
        if warn_count > 0:
            recommendations.append(
                f"{warn_count} items có cảnh báo (FIXABLE) - nên review thủ công."
            )
        if good_count == total:
            recommendations.append("Tất cả items đạt chất lượng tốt, sẵn sàng matching.")

        # Human summary for MainAgent to relay
        human_summary = (
            f"Đã chuẩn hóa {total} mô tả. "
            f"Kết quả: {good_count} tốt, {warn_count} cần xem lại, {bad_count} bị chặn. "
            f"Tỷ lệ đạt: {pass_rate}%."
        )

        return AgentReport(
            agent_name=self.name,
            status=AgentStatus.COMPLETED,
            findings=findings,
            recommendations=recommendations,
            human_summary=human_summary,
            metrics={
                "total": total,
                "good": good_count,
                "fixable": warn_count,
                "bad": bad_count,
                "pass_rate": pass_rate,
                "blocked_indices": blocked_indices,
            },
        )

    def _review_item(self, original: str, result: Dict) -> Dict:
        """Expert per-item review of normalization quality."""
        normalized = result.get("normalized", "")
        confidence = result.get("confidence", 0.0)
        issues = []
        info_lost = []
        verdict = "GOOD"
        should_pass = True

        # Check 1: Empty output
        if not normalized or len(normalized.strip()) < 3:
            return {"verdict": "BAD", "issues": ["Output rỗng hoặc quá ngắn"], "info_lost": [], "pass": False}

        # Check 2: Confidence
        if confidence < _CONFIDENCE_BAD:
            issues.append(f"Confidence quá thấp: {confidence:.0f}%")
            verdict = "BAD"
            should_pass = False
        elif confidence < _CONFIDENCE_WARN:
            issues.append(f"Confidence thấp: {confidence:.0f}%")
            verdict = "FIXABLE"

        # Check 3: Structure (3-component)
        parts = normalized.split(" - ")
        if len(parts) == 1 and len(normalized) > 15:
            issues.append("Thiếu dấu ' - ' phân tách (OBJECT - VARIANT - SPECS)")
            verdict = "BAD"
            should_pass = False
        elif len(parts) > 3:
            issues.append(f"Quá {len(parts)} thành phần (tối đa 3)")
            if verdict == "GOOD":
                verdict = "FIXABLE"

        # Check 4: Information loss
        orig_specs = set(_SPEC_PATTERN.findall(original.upper()))
        norm_specs = set(_SPEC_PATTERN.findall(normalized.upper()))
        lost_specs = orig_specs - norm_specs
        for s in lost_specs:
            info_lost.append(f"spec: {s}")

        orig_mats = set(_MATERIAL_PATTERN.findall(original.lower()))
        norm_mats = set(_MATERIAL_PATTERN.findall(normalized.lower()))
        lost_mats = orig_mats - norm_mats
        for m in lost_mats:
            info_lost.append(f"material: {m}")

        if orig_specs and len(lost_specs) / max(len(orig_specs), 1) > _INFO_LOSS_CRITICAL:
            issues.append(f"Mất {len(lost_specs)}/{len(orig_specs)} specs quan trọng")
            verdict = "BAD"
            should_pass = False
        elif info_lost:
            issues.append(f"Mất thông tin nhẹ: {', '.join(info_lost[:3])}")
            if verdict == "GOOD":
                verdict = "FIXABLE"

        # Check 5: No normalization happened
        if normalized.strip().lower() == original.strip().lower() and confidence < _CONFIDENCE_WARN:
            issues.append("Output giống hệt input - có thể normalization thất bại")
            if verdict == "GOOD":
                verdict = "FIXABLE"

        return {"verdict": verdict, "issues": issues, "info_lost": info_lost, "pass": should_pass}
