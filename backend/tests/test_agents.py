"""
Tests for the isolated multi-agent system.

Tests:
- AgentReport protocol (findings, human_summary, serialization)
- Agent isolation (no shared state between calls)
- AgentRegistry (register CLASS, create NEW instance)
- NormalizationAgent per-item review
- MainAgent pipeline with report synthesis
- MainAgent parallel execution
- Data flows as serialized dicts only (no object references)
"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.agents.base_agent import (
    BaseAgent,
    AgentRegistry,
    AgentReport,
    AgentStatus,
)
from app.services.agents.main_agent import MainAgent


# ── Test Agent for isolation testing ──

class CounterAgent(BaseAgent):
    """Agent that proves isolation: each instance has its own counter."""
    name = "counter"
    description = "Counts calls to prove isolation"

    def __init__(self):
        self._call_count = 0  # Should always be 0 at start

    def execute(self, task):
        self._call_count += 1
        return AgentReport(
            agent_name=self.name,
            status=AgentStatus.COMPLETED,
            findings=[{"call_count": self._call_count}],
            human_summary=f"Called {self._call_count} time(s)",
            metrics={"call_count": self._call_count},
        )


class FailingAgent(BaseAgent):
    name = "failing"
    description = "Always fails"

    def execute(self, task):
        raise ValueError("Intentional failure")


# ── AgentReport Tests ──

class TestAgentReport:
    def test_report_has_all_fields(self):
        report = AgentReport(
            agent_name="test",
            status=AgentStatus.COMPLETED,
            findings=[{"item": "A", "verdict": "GOOD"}],
            recommendations=["Proceed to matching"],
            human_summary="Processed 1 item successfully",
            metrics={"total": 1, "good": 1},
        )
        assert report.success is True
        assert report.human_summary == "Processed 1 item successfully"
        assert len(report.findings) == 1
        assert len(report.recommendations) == 1

    def test_report_serialization_roundtrip(self):
        original = AgentReport(
            agent_name="test",
            status=AgentStatus.COMPLETED,
            findings=[{"x": 1}],
            recommendations=["Do this"],
            human_summary="Summary",
            metrics={"k": "v"},
        )
        as_dict = original.to_dict()

        # Verify it's a plain dict (no object references)
        assert isinstance(as_dict, dict)
        assert isinstance(as_dict["findings"], list)
        assert isinstance(as_dict["findings"][0], dict)

        # Roundtrip
        restored = AgentReport.from_dict(as_dict)
        assert restored.agent_name == "test"
        assert restored.findings == [{"x": 1}]
        assert restored.human_summary == "Summary"

    def test_fail_convenience(self):
        report = AgentReport.fail("my_agent", "Something broke")
        assert report.success is False
        assert report.error == "Something broke"
        assert "my_agent" in report.human_summary

    def test_success_property(self):
        assert AgentReport(agent_name="a", status=AgentStatus.COMPLETED).success is True
        assert AgentReport(agent_name="a", status=AgentStatus.FAILED).success is False


# ── AgentRegistry Tests ──

class TestAgentRegistry:
    def setup_method(self):
        AgentRegistry.reset()

    def test_register_class_not_instance(self):
        registry = AgentRegistry()
        registry.register(CounterAgent)  # CLASS, not instance
        assert registry.has("counter")

    def test_create_returns_new_instance(self):
        registry = AgentRegistry()
        registry.register(CounterAgent)
        a1 = registry.create("counter")
        a2 = registry.create("counter")
        assert a1 is not a2  # Different instances

    def test_create_nonexistent(self):
        registry = AgentRegistry()
        assert registry.create("nonexistent") is None

    def test_list_agents(self):
        registry = AgentRegistry()
        registry.register(CounterAgent)
        registry.register(FailingAgent)
        agents = registry.list_agents()
        names = [a["name"] for a in agents]
        assert "counter" in names
        assert "failing" in names

    def test_singleton(self):
        AgentRegistry.reset()
        r1 = AgentRegistry()
        r2 = AgentRegistry()
        assert r1 is r2


# ── Isolation Tests ──

class TestAgentIsolation:
    def test_no_shared_state_between_calls(self):
        """Each run() creates a fresh agent, so call_count is always 1."""
        AgentRegistry.reset()
        registry = AgentRegistry()
        registry.register(CounterAgent)

        # First call
        agent1 = registry.create("counter")
        report1 = agent1.run({"data": "first"})
        assert report1.metrics["call_count"] == 1

        # Second call - NEW instance, count resets
        agent2 = registry.create("counter")
        report2 = agent2.run({"data": "second"})
        assert report2.metrics["call_count"] == 1  # NOT 2

    def test_deep_copy_prevents_mutation(self):
        """Agent cannot mutate the caller's task dict."""
        agent = CounterAgent()
        task = {"data": [1, 2, 3], "nested": {"key": "value"}}
        original_data = task["data"].copy()

        agent.run(task)

        # Original task should be unchanged
        assert task["data"] == original_data

    def test_error_handling_in_isolation(self):
        agent = FailingAgent()
        report = agent.run({})
        assert report.success is False
        assert "Intentional failure" in report.error
        assert report.duration_ms > 0


# ── NormalizationAgent Tests ──

class TestNormalizationAgent:
    @patch("app.services.normalization_orchestrator.NormalizationOrchestrator")
    def test_per_item_review_good(self, MockOrch):
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "original": "Đào đất hố móng",
            "normalized": "Đào đất - máy đào 0.8 - đất cấp 3",
            "confidence": 85.0,
            "work_category": "earthworks_piling",
            "normalizer_used": "description",
            "specs": {},
        }
        MockOrch.return_value.normalize.return_value = mock_result

        from app.services.agents.normalization_agent import NormalizationAgent
        agent = NormalizationAgent()
        report = agent.execute({"descriptions": ["Đào đất hố móng"]})

        assert report.success is True
        assert len(report.findings) == 1
        assert report.findings[0]["verdict"] == "GOOD"
        assert report.findings[0]["pass"] is True
        assert report.metrics["good"] == 1
        assert "1 tốt" in report.human_summary

    @patch("app.services.normalization_orchestrator.NormalizationOrchestrator")
    def test_per_item_review_bad_empty(self, MockOrch):
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "original": "???",
            "normalized": "",
            "confidence": 10.0,
            "work_category": "general",
            "normalizer_used": "description",
            "specs": {},
        }
        MockOrch.return_value.normalize.return_value = mock_result

        from app.services.agents.normalization_agent import NormalizationAgent
        agent = NormalizationAgent()
        report = agent.execute({"descriptions": ["???"]})

        assert report.findings[0]["verdict"] == "BAD"
        assert report.findings[0]["pass"] is False
        assert report.metrics["bad"] == 1

    @patch("app.services.normalization_orchestrator.NormalizationOrchestrator")
    def test_per_item_review_info_loss(self, MockOrch):
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "original": "Ống HDPE D110 PN16 6m",
            "normalized": "Ống - HDPE",
            "confidence": 75.0,
            "work_category": "steel_mep",
            "normalizer_used": "mep",
            "specs": {},
        }
        MockOrch.return_value.normalize.return_value = mock_result

        from app.services.agents.normalization_agent import NormalizationAgent
        agent = NormalizationAgent()
        report = agent.execute({"descriptions": ["Ống HDPE D110 PN16 6m"]})

        finding = report.findings[0]
        assert len(finding["info_lost"]) >= 2  # D110, PN16, 6m
        assert finding["verdict"] == "BAD"  # Significant loss

    @patch("app.services.normalization_orchestrator.NormalizationOrchestrator")
    def test_batch_with_mixed_verdicts(self, MockOrch):
        results = [
            {"original": "A", "normalized": "A - B - C", "confidence": 90.0,
             "work_category": "general", "normalizer_used": "description", "specs": {}},
            {"original": "B", "normalized": "", "confidence": 10.0,
             "work_category": "general", "normalizer_used": "description", "specs": {}},
            {"original": "C", "normalized": "C - D", "confidence": 60.0,
             "work_category": "general", "normalizer_used": "description", "specs": {}},
        ]
        mock_orch = MagicMock()
        mock_orch.normalize.side_effect = [
            MagicMock(to_dict=MagicMock(return_value=r)) for r in results
        ]
        MockOrch.return_value = mock_orch

        from app.services.agents.normalization_agent import NormalizationAgent
        agent = NormalizationAgent()
        report = agent.execute({"descriptions": ["A", "B", "C"]})

        assert report.metrics["good"] == 1
        assert report.metrics["bad"] == 1
        assert report.metrics["fixable"] == 1
        assert 1 in report.metrics["blocked_indices"]  # index 1 blocked
        assert len(report.recommendations) >= 1

    @patch("app.services.normalization_orchestrator.NormalizationOrchestrator")
    def test_human_summary_readable(self, MockOrch):
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "original": "X", "normalized": "X - Y", "confidence": 80.0,
            "work_category": "general", "normalizer_used": "description", "specs": {},
        }
        MockOrch.return_value.normalize.return_value = mock_result

        from app.services.agents.normalization_agent import NormalizationAgent
        agent = NormalizationAgent()
        report = agent.execute({"descriptions": ["X"]})

        # Human summary should be understandable Vietnamese
        assert "chuẩn hóa" in report.human_summary
        assert "1" in report.human_summary
        assert "%" in report.human_summary

    def test_missing_descriptions(self):
        from app.services.agents.normalization_agent import NormalizationAgent
        agent = NormalizationAgent()
        report = agent.execute({})
        assert report.success is False


# ── MainAgent Tests ──

class TestMainAgent:
    def setup_method(self):
        AgentRegistry.reset()

    @patch("app.services.agents.main_agent.NormalizationAgent")
    @patch("app.services.agents.main_agent.MatchingAgent")
    @patch("app.services.agents.main_agent.ValidationAgent")
    def test_direct_dispatch_creates_new_instance(self, MockVal, MockMatch, MockNorm):
        """Each dispatch creates a NEW agent instance."""
        mock_agent = MagicMock()
        mock_agent.run.return_value = AgentReport(
            agent_name="normalization",
            status=AgentStatus.COMPLETED,
            findings=[],
            human_summary="Done",
        )
        MockNorm.name = "normalization"
        MockNorm.description = "test"
        MockMatch.name = "matching"
        MockMatch.description = "test"
        MockVal.name = "validation"
        MockVal.description = "test"

        # Registry.create() is called which instantiates class
        main = MainAgent()
        main._registry.clear()
        main._registry.register(MockNorm)
        main._registry.register(MockMatch)
        main._registry.register(MockVal)

        # Mock create to return our mock
        main._registry.create = MagicMock(return_value=mock_agent)

        report = main.execute({"command": "normalize", "descriptions": ["test"]})

        assert report.success is True
        main._registry.create.assert_called_once_with("normalization")

    def test_unknown_command(self):
        main = MainAgent()
        report = main.execute({"command": "unknown"})
        assert report.success is False

    def test_missing_command(self):
        main = MainAgent()
        report = main.execute({})
        assert report.success is False

    def test_pipeline_synthesizes_reports(self):
        """Pipeline runs agents sequentially and synthesizes their reports."""
        AgentRegistry.reset()
        main = MainAgent()

        # Mock registry to return controlled agents
        norm_report = AgentReport(
            agent_name="normalization",
            status=AgentStatus.COMPLETED,
            findings=[
                {"index": 0, "original": "A", "normalized": "A - B", "pass": True,
                 "confidence": 90, "verdict": "GOOD", "issues": [], "info_lost": [],
                 "work_category": "general", "normalizer_used": "description", "specs": {}},
            ],
            recommendations=["All good"],
            human_summary="Đã chuẩn hóa 1 mô tả. Kết quả: 1 tốt.",
            metrics={"total": 1, "good": 1, "bad": 0},
        )
        match_report = AgentReport(
            agent_name="matching",
            status=AgentStatus.COMPLETED,
            findings=[
                {"index": 0, "query": "A - B", "match_type": "new", "similarity_score": 0.3},
            ],
            recommendations=["1 item mới"],
            human_summary="Đối soát 1 mô tả. 1 mới.",
            metrics={"total": 1, "new": 1},
        )
        val_report = AgentReport(
            agent_name="validation",
            status=AgentStatus.COMPLETED,
            findings=[{"index": 0, "status": "APPROVED", "score": 80}],
            recommendations=["1 approved"],
            human_summary="Kiểm duyệt 1 item. 1 approved.",
            metrics={"approved": 1},
        )

        reports = [norm_report, match_report, val_report]
        call_idx = [0]

        def mock_create(name):
            agent = MagicMock()
            idx = call_idx[0]
            agent.run.return_value = reports[idx]
            call_idx[0] += 1
            return agent

        main._registry.create = mock_create

        report = main.execute({
            "command": "process",
            "descriptions": ["A"],
        })

        assert report.success is True
        assert report.metrics["steps_completed"] == 3
        # human_summary should chain all sub-summaries
        assert "[normalization]" in report.human_summary
        assert "[matching]" in report.human_summary
        assert "[validation]" in report.human_summary
        # Recommendations from all steps
        assert len(report.recommendations) >= 3

    def test_pipeline_stops_on_failure(self):
        AgentRegistry.reset()
        main = MainAgent()

        fail_report = AgentReport.fail("normalization", "Parse error")

        def mock_create(name):
            agent = MagicMock()
            agent.run.return_value = fail_report
            return agent

        main._registry.create = mock_create

        report = main.execute({
            "command": "process",
            "descriptions": ["bad"],
        })

        assert report.success is False
        assert "normalization" in report.metrics["failed_at"]
        assert "Parse error" in report.human_summary

    def test_pipeline_data_bridge_normalization_to_matching(self):
        """Verify MainAgent extracts only PASSED items for matching."""
        AgentRegistry.reset()
        main = MainAgent()

        norm_report = AgentReport(
            agent_name="normalization",
            status=AgentStatus.COMPLETED,
            findings=[
                {"index": 0, "normalized": "Good - item", "pass": True},
                {"index": 1, "normalized": "", "pass": False},  # BAD → blocked
            ],
            human_summary="2 items, 1 passed",
            metrics={},
        )
        match_report = AgentReport(
            agent_name="matching",
            status=AgentStatus.COMPLETED,
            findings=[],
            human_summary="Matched",
            metrics={},
        )

        captured_task = {}

        def mock_create(name):
            agent = MagicMock()
            if name == "normalization":
                agent.run.return_value = norm_report
            elif name == "matching":
                def capture_run(task):
                    captured_task.update(task)
                    return match_report
                agent.run.side_effect = capture_run
            return agent

        main._registry.create = mock_create

        main.execute({
            "command": "normalize_and_match",
            "descriptions": ["A", "B"],
        })

        # Matching should only receive the passed item
        assert captured_task["descriptions"] == ["Good - item"]

    def test_parallel_creates_separate_instances(self):
        AgentRegistry.reset()
        main = MainAgent()

        instances_created = []

        def mock_create(name):
            agent = MagicMock()
            agent.run.return_value = AgentReport(
                agent_name=name,
                status=AgentStatus.COMPLETED,
                findings=[],
                human_summary=f"Done {len(instances_created)}",
            )
            instances_created.append(agent)
            return agent

        main._registry.create = mock_create

        report = main.execute({
            "command": "parallel",
            "tasks": [
                {"agent": "normalization", "descriptions": ["A"]},
                {"agent": "normalization", "descriptions": ["B"]},
            ],
        })

        # Two separate instances should have been created
        assert len(instances_created) == 2
        assert instances_created[0] is not instances_created[1]

    def test_list_agents(self):
        main = MainAgent()
        agents = main.list_agents()
        names = [a["name"] for a in agents]
        assert "normalization" in names
        assert "matching" in names
        assert "validation" in names
