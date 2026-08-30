"""End-to-end routing tests for the centralized orchestrator."""

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


def research_model(_: str) -> str:
    return json.dumps(
        {
            "summary": "Demand is growing, but execution risk remains.",
            "findings": [
                {
                    "claim": "Target-market demand increased year over year.",
                    "evidence": "The supplied market brief reports 18% annual demand growth.",
                    "source_ids": ["market-brief"],
                    "confidence": "high",
                }
            ],
            "open_questions": [
                "Can the company support the required service footprint?"
            ],
        }
    )


def analysis_model(_: str) -> str:
    return json.dumps(
        {
            "assessment": (
                "The opportunity is promising, but operational readiness "
                "remains uncertain."
            ),
            "points": [
                {
                    "kind": "opportunity",
                    "statement": "Demand growth supports considering market entry.",
                    "reasoning": "The validated research reports 18% annual demand growth.",
                    "source_ids": ["market-brief"],
                    "confidence": "high",
                },
                {
                    "kind": "uncertainty",
                    "statement": "Service capacity remains unresolved.",
                    "reasoning": (
                        "The research handoff identifies service capacity as an "
                        "open question."
                    ),
                    "source_ids": ["market-brief"],
                    "confidence": "medium",
                },
            ],
            "assumptions": [],
            "questions_for_verification": [
                "Can Acme Robotics support the required service footprint?"
            ],
        }
    )


def test_orchestrator_completes_when_verification_allows_synthesis() -> None:
    raw_draft = (
        "The evidence supports considering market entry, but service capacity "
        "should be validated before committing."
    )

    def verification_model(_: str) -> str:
        return json.dumps(
            {
                "overall_status": "pass_with_cautions",
                "checks": [
                    {
                        "target": "Demand growth supports considering market entry.",
                        "verdict": "supported",
                        "reasoning": "The research directly reports 18% annual demand growth.",
                        "source_ids": ["market-brief"],
                    },
                    {
                        "target": "Service capacity remains unresolved.",
                        "verdict": "partially_supported",
                        "reasoning": (
                            "The research identifies capacity as an open question "
                            "rather than an established constraint."
                        ),
                        "source_ids": ["market-brief"],
                    },
                ],
                "corrections": [],
                "unresolved_questions": [
                    "Can Acme Robotics support the required service footprint?"
                ],
            }
        )

    def synthesis_model(_: str) -> str:
        return json.dumps(
            {
                "response": raw_draft,
                "key_points": [
                    {
                        "statement": "Demand growth supports considering market entry.",
                        "source_ids": ["market-brief"],
                    }
                ],
                "cautions": [
                    "Service capacity has not yet been established."
                ],
                "unresolved_questions": [
                    "Can Acme Robotics support the required service footprint?"
                ],
                "confidence": "medium",
            }
        )

    orchestrator = CentralOrchestrator(
        research_agent=ResearchAgent(model=research_model),
        analysis_agent=AnalysisAgent(model=analysis_model),
        verification_agent=VerificationAgent(model=verification_model),
        synthesis_agent=SynthesisAgent(model=synthesis_model),
    )

    state = orchestrator.run(mission=MISSION, sources=SOURCES)

    assert state.status == "completed"
    assert state.research_result is not None
    assert state.analysis_result is not None
    assert state.verification_result is not None
    assert state.verification_result.overall_status == "pass_with_cautions"
    assert state.synthesis_result is not None
    assert state.final_answer is not None
    assert raw_draft not in state.final_answer
    assert "Demand growth supports considering market entry." in state.final_answer
    assert "sources: market-brief" in state.final_answer
    assert "Service capacity remains unresolved." in state.final_answer
    assert "partially_supported" in state.final_answer
    assert "Can Acme Robotics support the required service footprint?" in (
        state.final_answer
    )
    assert "Confidence:** medium" in state.final_answer
    assert state.error is None
    assert any(
        step.agent == "orchestrator"
        and step.action == "route after verification"
        and step.status == "completed"
        for step in state.history
    )
    assert any(
        step.agent == "synthesis"
        and step.note == "orchestrator published verified structured output"
        for step in state.history
    )


def test_orchestrator_stops_before_synthesis_when_revision_is_required() -> None:
    synthesis_called = False

    def verification_model(_: str) -> str:
        return json.dumps(
            {
                "overall_status": "needs_revision",
                "checks": [
                    {
                        "target": "Demand growth guarantees successful market entry.",
                        "verdict": "unsupported",
                        "reasoning": (
                            "The research establishes demand growth but does not "
                            "establish guaranteed entry success."
                        ),
                        "source_ids": ["market-brief"],
                    }
                ],
                "corrections": [
                    "Replace the guarantee claim with a bounded statement about demand evidence."
                ],
                "unresolved_questions": [],
            }
        )

    def synthesis_model(_: str) -> str:
        nonlocal synthesis_called
        synthesis_called = True
        return json.dumps(
            {
                "response": "This response should never be produced.",
                "key_points": [
                    {
                        "statement": "Unused synthesis output.",
                        "source_ids": ["market-brief"],
                    }
                ],
                "cautions": [],
                "unresolved_questions": [],
                "confidence": "low",
            }
        )

    orchestrator = CentralOrchestrator(
        research_agent=ResearchAgent(model=research_model),
        analysis_agent=AnalysisAgent(model=analysis_model),
        verification_agent=VerificationAgent(model=verification_model),
        synthesis_agent=SynthesisAgent(model=synthesis_model),
    )

    state = orchestrator.run(mission=MISSION, sources=SOURCES)

    assert state.status == "failed"
    assert state.error == "verification requires revision before synthesis"
    assert state.verification_result is not None
    assert state.verification_result.overall_status == "needs_revision"
    assert state.synthesis_result is None
    assert state.final_answer is None
    assert synthesis_called is False
    assert any(
        step.agent == "orchestrator"
        and step.action == "route after verification"
        and step.status == "failed"
        for step in state.history
    )
