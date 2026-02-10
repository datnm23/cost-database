"""
Main Agent - Central orchestrator that dispatches to isolated sub-agents
and synthesizes their reports into a coherent response for the user.

KEY DESIGN:
- Sub-agents run in ISOLATED sessions (no shared memory)
- Data between agents flows as SERIALIZED dicts only
- MainAgent READS each agent's report, UNDERSTANDS it, and RELAYS to user
- Each pipeline step extracts relevant data from the previous report's findings
"""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from app.services.agents.base_agent import (
    AgentRegistry,
    AgentReport,
    AgentStatus,
    BaseAgent,
)
from app.services.agents.normalization_agent import NormalizationAgent
from app.services.agents.matching_agent import MatchingAgent
from app.services.agents.validation_agent import ValidationAgent

logger = logging.getLogger(__name__)

# Pipeline definitions
PIPELINES = {
    "process": ["normalization", "matching", "validation"],
    "normalize_and_match": ["normalization", "matching"],
    "normalize_only": ["normalization"],
}


class MainAgent(BaseAgent):
    name = "main"
    description = "Tổng chỉ huy điều phối các sub-agent chuyên sâu"

    def __init__(self):
        self._registry = AgentRegistry()
        self._setup_agents()

    def _setup_agents(self):
        """Register agent CLASSES (not instances)."""
        self._registry.clear()
        self._registry.register(NormalizationAgent)
        self._registry.register(MatchingAgent)
        self._registry.register(ValidationAgent)

    def execute(self, task: Dict[str, Any]) -> AgentReport:
        """
        Task keys:
            command (str): 'process' | 'normalize' | 'match' | 'validate'
                           | 'normalize_and_match' | 'parallel'
            descriptions (list[str]): For normalization/process
            items (list[dict]): For validation
            method (str): For matching ('3_tier' or 'semantic_only')
        """
        command = task.get("command")
        if not command:
            return AgentReport.fail(
                self.name,
                "Thiếu 'command'. Dùng: process, normalize, match, validate, parallel"
            )

        # Pipeline commands
        if command in PIPELINES:
            return self._run_pipeline(PIPELINES[command], task)

        # Parallel execution
        if command == "parallel":
            return self._run_parallel(task)

        # Direct dispatch
        agent_map = {
            "normalize": "normalization",
            "match": "matching",
            "validate": "validation",
        }
        agent_name = agent_map.get(command)
        if agent_name and self._registry.has(agent_name):
            agent = self._registry.create(agent_name)
            return agent.run(task)

        return AgentReport.fail(self.name, f"Lệnh không hợp lệ: '{command}'")

    def _run_pipeline(
        self, agent_names: List[str], task: Dict[str, Any]
    ) -> AgentReport:
        """
        Run agents sequentially. Each agent runs in its own session.
        MainAgent extracts data from each report and builds the next task.
        """
        step_reports = []
        current_task = dict(task)  # Will be rebuilt for each step

        for agent_name in agent_names:
            if not self._registry.has(agent_name):
                return AgentReport.fail(
                    self.name,
                    f"Agent '{agent_name}' không tồn tại trong pipeline"
                )

            # Create FRESH agent instance for this step
            agent = self._registry.create(agent_name)

            # Run in isolated session (deep copy happens inside agent.run())
            report = agent.run(current_task)
            step_reports.append(report.to_dict())

            if not report.success:
                return self._build_failure_report(agent_name, report, step_reports, agent_names)

            # MainAgent reads the report and builds the NEXT task
            # This is the ONLY data bridge between agents
            current_task = self._build_next_task(agent_name, report, task)

        # Synthesize final report from all step reports
        return self._synthesize_reports(step_reports, agent_names)

    def _build_next_task(
        self, agent_name: str, report: AgentReport, original_task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        MainAgent reads the agent's report and builds the next agent's task.
        This is where MainAgent acts as the intelligent coordinator.
        NO object references are passed - only serialized data from findings.
        """
        if agent_name == "normalization":
            # Extract passed descriptions from normalization findings
            passed_descriptions = [
                f["normalized"]
                for f in report.findings
                if f.get("pass", True)
            ]
            return {
                "descriptions": passed_descriptions,
                "method": original_task.get("method", "3_tier"),
            }

        elif agent_name == "matching":
            # Extract new items (not matched) for validation
            new_items = [
                {"normalized_description": f["query"]}
                for f in report.findings
                if f.get("match_type") == "new"
            ]
            return {
                "items": new_items,
                "category": original_task.get("category"),
            }

        return original_task

    def _synthesize_reports(
        self, step_reports: List[Dict], agent_names: List[str]
    ) -> AgentReport:
        """
        MainAgent reads all sub-agent reports and creates a unified
        human-readable summary to relay to the user.
        """
        # Collect all summaries
        summaries = []
        all_recommendations = []
        all_metrics = {}

        for report_dict in step_reports:
            agent = report_dict["agent_name"]
            summaries.append(f"[{agent}] {report_dict['human_summary']}")
            all_recommendations.extend(report_dict.get("recommendations", []))
            all_metrics[agent] = report_dict.get("metrics", {})

        human_summary = " → ".join(summaries)

        return AgentReport(
            agent_name=self.name,
            status=AgentStatus.COMPLETED,
            findings=step_reports,  # Each step's full report as a finding
            recommendations=all_recommendations,
            human_summary=human_summary,
            metrics={
                "pipeline": agent_names,
                "steps_completed": len(step_reports),
                "per_step": all_metrics,
            },
        )

    def _build_failure_report(
        self, failed_agent: str, report: AgentReport,
        step_reports: List[Dict], pipeline: List[str]
    ) -> AgentReport:
        completed = [r["agent_name"] for r in step_reports[:-1]]
        return AgentReport(
            agent_name=self.name,
            status=AgentStatus.FAILED,
            findings=step_reports,
            error=f"Pipeline thất bại tại '{failed_agent}': {report.error}",
            human_summary=(
                f"Pipeline thất bại tại bước '{failed_agent}'. "
                f"Đã hoàn thành: {completed}. "
                f"Lỗi: {report.error}"
            ),
            metrics={
                "pipeline": pipeline,
                "failed_at": failed_agent,
                "completed_steps": completed,
            },
        )

    def _run_parallel(self, task: Dict[str, Any]) -> AgentReport:
        """
        Run multiple tasks in parallel. Each gets its own agent instance.

        Task keys:
            tasks (list[dict]): Each dict has 'agent' key + agent-specific keys.
        """
        tasks = task.get("tasks", [])
        if not tasks:
            return AgentReport.fail(self.name, "'parallel' cần 'tasks' list")

        results = [None] * len(tasks)

        with ThreadPoolExecutor(max_workers=min(len(tasks), 4)) as pool:
            futures = {}
            for i, t in enumerate(tasks):
                agent_name = t.get("agent")
                if self._registry.has(agent_name):
                    agent = self._registry.create(agent_name)
                    futures[pool.submit(agent.run, t)] = i
                else:
                    results[i] = AgentReport.fail(
                        "unknown", f"Agent '{agent_name}' không tồn tại"
                    ).to_dict()

            for future in as_completed(futures):
                idx = futures[future]
                try:
                    results[idx] = future.result().to_dict()
                except Exception as e:
                    results[idx] = AgentReport.fail("error", str(e)).to_dict()

        all_success = all(
            r.get("status") == "completed" if isinstance(r, dict) else False
            for r in results
        )

        summaries = [
            r.get("human_summary", "") for r in results if isinstance(r, dict)
        ]

        return AgentReport(
            agent_name=self.name,
            status=AgentStatus.COMPLETED if all_success else AgentStatus.FAILED,
            findings=results,
            human_summary=f"Chạy song song {len(tasks)} tasks. " + " | ".join(summaries),
            metrics={"total_tasks": len(tasks), "all_success": all_success},
        )

    def list_agents(self) -> List[Dict[str, str]]:
        return self._registry.list_agents()


def get_main_agent() -> MainAgent:
    return MainAgent()
