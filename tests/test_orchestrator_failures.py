"""Failure-containment tests for the centralized orchestrator."""

import json

from src.analysis_agent import AnalysisAgent
from src.orchestrator import CentralOrchestrator
from src.research_agent import ResearchAgent
from src.schemas import ResearchSource
from src.synthesis_agent import SynthesisAgent
from src.verification_agent import VerificationAgent


MISSION = "Evaluate whether Acme Robotics should enter the target market."
SOURCES = [
    ResearchSource(
        source_id="market-brief",
        title="Synthetic Market Brief",
        content="Annual demand in the target market increased 18%.",
    )
]


def test_orchestrator_contains_analysis_failure_and_stops_downstream_agents() -> None:
    verification_called = False
    synthesis_called = False

    def research_model(_: str) -> str:
        return json.dumps(
            {
                "summary": "Demand is growing.",
                "findings": [
                    {
                        "claim": "Target-market demand increased year over year.",
                        "evidence": "The supplied market brief reports 18% annual demand growth.",
                        "source_ids": ["market-brief"],
                        "confidence": "high",
                    }
                ],
                "open_questions": [],
            }
        )

    def failing_analysis_model(_: str) -> str:
        raise RuntimeError("analysis model unavailable")

    def verification_model(_: str) -> str:
        nonlocal verification_called
        verification_called = True
        raise AssertionError("verification should not run after analysis failure")

    def synthesis_model(_: str) -> str:
        nonlocal synthesis_called
        synthesis_called = True
        raise AssertionError("synthesis should not run after analysis failure")

    orchestrator = CentralOrchestrator(
        research_agent=ResearchAgent(model=research_model),
        analysis_agent=AnalysisAgent(model=failing_analysis_model),
        verification_agent=VerificationAgent(model=verification_model),
        synthesis_agent=SynthesisAgent(model=synthesis_model),
    )

    state = orchestrator.run(mission=MISSION, sources=SOURCES)

    assert state.status == "failed"
    assert state.error == "analysis model unavailable"
    assert state.research_result is not None
    assert state.analysis_result is None
    assert state.verification_result is None
    assert state.synthesis_result is None
    assert state.final_answer is None
    assert verification_called is False
    assert synthesis_called is False
    assert any(
        step.agent == "analysis"
        and step.action == "execute assigned step"
        and step.status == "failed"
        and step.note == "analysis model unavailable"
        for step in state.history
    )
    assert any(
        step.agent == "orchestrator"
        and step.action == "fail workflow"
        and step.status == "failed"
        and step.note == "failed during analysis"
        for step in state.history
    )
