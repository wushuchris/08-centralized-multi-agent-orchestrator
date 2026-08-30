"""Tests for structured orchestrator workflow state."""

from src.schemas import ResearchFinding, ResearchResult
from src.state import OrchestratorState


def test_orchestrator_state_stores_structured_specialist_result() -> None:
    research_result = ResearchResult(
        summary="Demand is growing, but execution risk remains.",
        findings=[
            ResearchFinding(
                claim="Target-market demand increased year over year.",
                evidence="The supplied market brief reports 18% annual demand growth.",
                source_ids=["market-brief"],
                confidence="high",
            )
        ],
        open_questions=[
            "Can the company support the required service footprint?"
        ],
    )

    state = OrchestratorState(
        mission="Evaluate whether Acme Robotics should enter the target market.",
        research_result=research_result,
    )
    state.record_step(
        agent="research",
        action="produce research handoff",
        status="completed",
    )

    assert state.research_result == research_result
    assert state.research_result.findings[0].source_ids == ["market-brief"]
    assert state.history[0].agent == "research"
    assert state.history[0].status == "completed"
