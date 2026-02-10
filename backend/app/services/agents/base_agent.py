"""
Base Agent Protocol for Isolated Multi-Agent Architecture.

Design principles:
1. ISOLATION: Agents do NOT share memory. Each agent creates its own
   service instances inside execute(). No singletons, no shared state.
2. SERIALIZED I/O: Agents receive plain dicts, return plain dicts.
   No passing object references between agents.
3. REPORT PROTOCOL: Every agent returns an AgentReport with:
   - findings: domain-specific results (list of dicts)
   - recommendations: actionable insights for the next step
   - human_summary: plain-language summary so MainAgent can relay to user
4. EXPERTISE: Each agent is a domain specialist, not a thin wrapper.
   The agent adds analysis, interpretation, and judgment on top of service calls.
"""
import copy
import json
import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentReport:
    """
    Structured report from a sub-agent back to MainAgent.

    This is the ONLY communication channel between agents.
    All fields are serializable (no object references).
    """
    agent_name: str
    status: AgentStatus

    # Domain-specific output (list of per-item results)
    findings: List[Dict[str, Any]] = field(default_factory=list)

    # Actionable next-step recommendations for MainAgent
    recommendations: List[str] = field(default_factory=list)

    # Plain-language summary for MainAgent to relay to user
    human_summary: str = ""

    # Aggregate metrics
    metrics: Dict[str, Any] = field(default_factory=dict)

    # Error info (only if status == FAILED)
    error: Optional[str] = None

    # Execution timing
    duration_ms: float = 0.0

    @property
    def success(self) -> bool:
        return self.status == AgentStatus.COMPLETED

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to plain dict. This is the ONLY way data leaves an agent."""
        return {
            "agent_name": self.agent_name,
            "status": self.status.value,
            "findings": self.findings,
            "recommendations": self.recommendations,
            "human_summary": self.human_summary,
            "metrics": self.metrics,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentReport":
        """Deserialize from plain dict. This is the ONLY way data enters an agent."""
        return cls(
            agent_name=data.get("agent_name", ""),
            status=AgentStatus(data.get("status", "completed")),
            findings=data.get("findings", []),
            recommendations=data.get("recommendations", []),
            human_summary=data.get("human_summary", ""),
            metrics=data.get("metrics", {}),
            error=data.get("error"),
            duration_ms=data.get("duration_ms", 0.0),
        )

    @classmethod
    def fail(cls, agent_name: str, error: str) -> "AgentReport":
        """Convenience: create a failed report."""
        return cls(
            agent_name=agent_name,
            status=AgentStatus.FAILED,
            error=error,
            human_summary=f"Agent '{agent_name}' thất bại: {error}",
        )


class BaseAgent(ABC):
    """
    Abstract base for all isolated agents.

    RULES:
    - execute() receives a deep-copied dict (no shared references)
    - execute() returns an AgentReport (serializable)
    - Agents must NOT store state between calls
    - Agents must create their own service instances inside execute()
    """

    name: str = "base_agent"
    description: str = "Base agent"

    @abstractmethod
    def execute(self, task: Dict[str, Any]) -> AgentReport:
        """
        Execute the agent's specialized task in an isolated session.

        Args:
            task: Deep-copied input data. Agent owns this dict completely.
                  No other agent has a reference to it.

        Returns:
            AgentReport with findings, recommendations, and human_summary.
        """
        ...

    def run(self, task: Dict[str, Any]) -> AgentReport:
        """
        Run agent in an isolated session with timing and error handling.
        Input is deep-copied to guarantee no shared memory.
        """
        # Deep copy input → agent gets its own isolated copy
        isolated_task = copy.deepcopy(task)

        start = time.time()
        try:
            report = self.execute(isolated_task)
            report.agent_name = self.name
            report.duration_ms = (time.time() - start) * 1000
            return report
        except Exception as e:
            logger.exception(f"Agent '{self.name}' failed: {e}")
            report = AgentReport.fail(self.name, str(e))
            report.duration_ms = (time.time() - start) * 1000
            return report


class AgentRegistry:
    """Registry for agent discovery. Agents are registered by class, not instance."""

    _instance: Optional["AgentRegistry"] = None
    _agent_classes: Dict[str, type]

    def __new__(cls) -> "AgentRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._agent_classes = {}
        return cls._instance

    def register(self, agent_class: type) -> None:
        """Register an agent CLASS (not instance). A new instance is created for each execution."""
        name = agent_class.name
        self._agent_classes[name] = agent_class
        logger.info(f"Registered agent class: {name}")

    def create(self, name: str) -> Optional[BaseAgent]:
        """Create a NEW instance of the agent. Each call = fresh isolated agent."""
        cls = self._agent_classes.get(name)
        if cls:
            return cls()
        return None

    def list_agents(self) -> List[Dict[str, str]]:
        return [
            {"name": cls.name, "description": cls.description}
            for cls in self._agent_classes.values()
        ]

    def has(self, name: str) -> bool:
        return name in self._agent_classes

    def clear(self) -> None:
        self._agent_classes.clear()

    @classmethod
    def reset(cls) -> None:
        cls._instance = None
