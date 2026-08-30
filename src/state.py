"""Shared workflow state for the centralized multi-agent orchestrator."""

from typing import Literal

from pydantic import BaseModel, Field


AgentName = Literal[
    "orchestrator",
    "research",
    "analysis",
    "verification",
    "synthesis",
]

WorkflowStatus = Literal[
    "created",
    "researching",
    "analyzing",
    "verifying",
    "synthesizing",
    "completed",
    "failed",
]


class AgentStep(BaseModel):
    """One auditable step in the multi-agent workflow."""

    agent: AgentName
    action: str
    status: Literal["started", "completed", "failed"]
    note: str | None = None


class OrchestratorState(BaseModel):
    """Structured state shared across the supervisor and specialist agents."""

    mission: str = Field(min_length=1)
    status: WorkflowStatus = "created"

    research_result: str | None = None
    analysis_result: str | None = None
    verification_result: str | None = None
    synthesis_result: str | None = None

    history: list[AgentStep] = Field(default_factory=list)
    final_answer: str | None = None
    error: str | None = None

    def record_step(
        self,
        agent: AgentName,
        action: str,
        status: Literal["started", "completed", "failed"],
        note: str | None = None,
    ) -> None:
        """Append an auditable workflow event to the shared state."""

        self.history.append(
            AgentStep(
                agent=agent,
                action=action,
                status=status,
                note=note,
            )
        )
