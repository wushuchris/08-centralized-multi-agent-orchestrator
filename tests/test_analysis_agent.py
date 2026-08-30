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
    assert "Questions must be neutral" in captured_prompt
    assert result.points[0].kind == "opportunity"
    assert result.points[0].source_ids == ["market-brief"]
    assert result.questions_for_verification
