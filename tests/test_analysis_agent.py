"""Tests for the bounded Analysis Agent."""

import json

from src.analysis_agent import AnalysisAgent
from src.schemas import ResearchFinding, ResearchResult


def test_analysis_agent_consumes_validated_research_handoff() -> None:
    captured_prompt = ""

    def fake_model(prompt: str) -> str:
        nonlocal captured_prompt
        captured_prompt = prompt
        return json.dumps(
            {
                "assessment": "The market opportunity is promising, but operational readiness remains uncertain.",
                "points": [
                    {
                        "kind": "opportunity",
                        "statement": "Demand growth supports considering market entry.",
                        "reasoning": "The research finding reports 18% annual demand growth in the target market.",
                        "source_ids": ["market-brief"],
                        "confidence": "high",
                    },
                    {
                        "kind": "uncertainty",
                        "statement": "Service capacity could limit successful expansion.",
                        "reasoning": "The research handoff identifies service-footprint capability as an unresolved question.",
                        "source_ids": ["market-brief"],
                        "confidence": "medium",
                    },
                ],
                "assumptions": [
                    "Demand growth continues long enough to justify expansion planning."
                ],
                "questions_for_verification": [
                    "Can Acme Robotics support the required service footprint?"
                ],
            }
        )

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

    agent = AnalysisAgent(model=fake_model)
    result = agent.run(
        mission="Evaluate whether Acme Robotics should enter the target market.",
        research_result=research_result,
    )

    assert "Acme Robotics" in captured_prompt
    assert "18%" in captured_prompt
    assert "market-brief" in captured_prompt
    assert "do not say the competitors dominate" in captured_prompt
    assert "do not say that demand aligns with this company's offering" in captured_prompt
    assert "If you cannot cite at least one approved source_id" in captured_prompt
    assert "Questions must be neutral" in captured_prompt
    assert "Do not create point IDs" in captured_prompt
    assert result.points[0].point_id == "analysis-1"
    assert result.points[1].point_id == "analysis-2"
    assert result.points[0].kind == "opportunity"
    assert result.points[0].source_ids == ["market-brief"]
    assert result.omitted_points == []
    assert result.questions_for_verification


def test_analysis_agent_quarantines_points_without_approved_sources() -> None:
    def fake_model(_: str) -> str:
        return json.dumps(
            {
                "assessment": "Some implications are evidence-linked and others are not.",
                "points": [
                    {
                        "kind": "opportunity",
                        "statement": "Demand growth supports further market evaluation.",
                        "reasoning": "The market brief reports 18% annual demand growth.",
                        "source_ids": ["market-brief"],
                        "confidence": "high",
                    },
                    {
                        "kind": "risk",
                        "statement": "Uncited risk should not enter verification.",
                        "reasoning": "No approved source supports this point.",
                        "source_ids": [],
                        "confidence": "low",
                    },
                    {
                        "kind": "constraint",
                        "statement": "Hallucinated citation should also be quarantined.",
                        "reasoning": "The cited source ID is not approved.",
                        "source_ids": ["invented-source"],
                        "confidence": "low",
                    },
                ],
                "assumptions": [],
                "questions_for_verification": [],
            }
        )

    research_result = ResearchResult(
        summary="Demand increased.",
        findings=[
            ResearchFinding(
                claim="Target-market demand increased year over year.",
                evidence="The market brief reports 18% annual demand growth.",
                source_ids=["market-brief"],
                confidence="high",
            )
        ],
    )

    result = AnalysisAgent(model=fake_model).run(
        mission="Evaluate market entry.",
        research_result=research_result,
    )

    assert len(result.points) == 1
    assert result.points[0].point_id == "analysis-1"
    assert result.points[0].source_ids == ["market-brief"]
    assert result.omitted_points == [
        "Uncited risk should not enter verification.",
        "Hallucinated citation should also be quarantined.",
    ]
