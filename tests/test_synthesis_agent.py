"""Tests for the bounded Synthesis Agent."""

import json

from src.schemas import (
    AnalysisPoint,
    AnalysisResult,
    ResearchFinding,
    ResearchResult,
    VerificationCheck,
    VerificationResult,
)
from src.synthesis_agent import SynthesisAgent


def test_synthesis_agent_preserves_verified_cautions() -> None:
    captured_prompt = ""

    def fake_model(prompt: str) -> str:
        nonlocal captured_prompt
        captured_prompt = prompt
        return json.dumps(
            {
                "response": (
                    "Acme Robotics has evidence of attractive market demand, "
                    "but service capacity should be verified before a final expansion decision."
                ),
                "key_points": [
                    {
                        "statement": "Target-market demand grew 18% year over year.",
                        "source_ids": ["market-brief"],
                    }
                ],
                "cautions": [
                    "Service capacity has not been established and should remain a caution."
                ],
                "unresolved_questions": [
                    "Can Acme Robotics support the required service footprint?"
                ],
                "confidence": "medium",
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

    analysis_result = AnalysisResult(
        assessment="The market opportunity is promising, but operational readiness remains uncertain.",
        points=[
            AnalysisPoint(
                kind="opportunity",
                statement="Demand growth supports considering market entry.",
                reasoning="The research finding reports 18% annual demand growth in the target market.",
                source_ids=["market-brief"],
                confidence="high",
            ),
            AnalysisPoint(
                kind="uncertainty",
                statement="Service capacity could limit successful expansion.",
                reasoning="The research handoff identifies service-footprint capability as an unresolved question.",
                source_ids=["market-brief"],
                confidence="medium",
            ),
        ],
        assumptions=[
            "Demand growth continues long enough to justify expansion planning."
        ],
        questions_for_verification=[
            "Can Acme Robotics support the required service footprint?"
        ],
    )

    verification_result = VerificationResult(
        overall_status="pass_with_cautions",
        checks=[
            VerificationCheck(
                target="Demand growth supports considering market entry.",
                verdict="supported",
                reasoning="The research handoff reports 18% annual demand growth.",
                source_ids=["market-brief"],
            ),
            VerificationCheck(
                target="Service capacity could limit successful expansion.",
                verdict="partially_supported",
                reasoning=(
                    "Service capacity is an unresolved question, not an established weakness."
                ),
                source_ids=["market-brief"],
            ),
        ],
        corrections=[
            "Treat service-capacity risk as unresolved rather than established."
        ],
        unresolved_questions=[
            "Can Acme Robotics support the required service footprint?"
        ],
    )

    agent = SynthesisAgent(model=fake_model)
    result = agent.run(
        mission="Evaluate whether Acme Robotics should enter the target market.",
        research_result=research_result,
        analysis_result=analysis_result,
        verification_result=verification_result,
    )

    assert "pass_with_cautions" in captured_prompt
    assert "Treat service-capacity risk as unresolved" in captured_prompt
    assert "18%" in captured_prompt
    assert result.key_points[0].source_ids == ["market-brief"]
    assert result.cautions
    assert result.unresolved_questions
    assert result.confidence == "medium"
