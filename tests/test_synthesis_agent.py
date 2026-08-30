"""Tests for the bounded Synthesis Agent."""

import json

import pytest

from src.schemas import (
    AnalysisPoint,
    AnalysisResult,
    ResearchFinding,
    ResearchResult,
    VerificationCheck,
    VerificationResult,
)
from src.synthesis_agent import SynthesisAgent


def _research_result() -> ResearchResult:
    return ResearchResult(
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


def _analysis_result() -> AnalysisResult:
    return AnalysisResult(
        assessment=(
            "The market opportunity is promising, but operational readiness "
            "remains uncertain."
        ),
        points=[
            AnalysisPoint(
                point_id="analysis-1",
                kind="opportunity",
                statement="Demand growth supports considering market entry.",
                reasoning=(
                    "The research finding reports 18% annual demand growth in "
                    "the target market."
                ),
                source_ids=["market-brief"],
                confidence="high",
            ),
            AnalysisPoint(
                point_id="analysis-2",
                kind="uncertainty",
                statement="Service capacity could limit successful expansion.",
                reasoning=(
                    "The research handoff identifies service-footprint "
                    "capability as an unresolved question."
                ),
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


def _verification_result() -> VerificationResult:
    return VerificationResult(
        overall_status="pass_with_cautions",
        checks=[
            VerificationCheck(
                analysis_point_id="analysis-1",
                verdict="supported",
                reasoning="The research handoff reports 18% annual demand growth.",
                source_ids=["market-brief"],
            ),
            VerificationCheck(
                analysis_point_id="analysis-2",
                verdict="partially_supported",
                reasoning=(
                    "Service capacity is an unresolved question, not an "
                    "established weakness."
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


def test_synthesis_agent_accepts_supported_analysis_id() -> None:
    captured_prompt = ""

    def fake_model(prompt: str) -> str:
        nonlocal captured_prompt
        captured_prompt = prompt
        return json.dumps(
            {
                "response": (
                    "Acme Robotics has evidence of attractive market demand, "
                    "but service capacity should be verified before a final "
                    "expansion decision."
                ),
                "key_points": [
                    {
                        "analysis_point_id": "analysis-1",
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

    agent = SynthesisAgent(model=fake_model)
    result = agent.run(
        mission="Evaluate whether Acme Robotics should enter the target market.",
        research_result=_research_result(),
        analysis_result=_analysis_result(),
        verification_result=_verification_result(),
    )

    assert "pass_with_cautions" in captured_prompt
    assert "copy only its analysis_point_id" in captured_prompt
    assert "Treat service-capacity risk as unresolved" in captured_prompt
    assert result.key_points[0].analysis_point_id == "analysis-1"
    assert result.confidence == "medium"


def test_synthesis_agent_rejects_non_supported_analysis_id() -> None:
    def fake_model(_: str) -> str:
        return json.dumps(
            {
                "response": "Service capacity is a proven weakness.",
                "key_points": [
                    {
                        "analysis_point_id": "analysis-2",
                    }
                ],
                "cautions": [],
                "unresolved_questions": [],
                "confidence": "medium",
            }
        )

    agent = SynthesisAgent(model=fake_model)

    with pytest.raises(
        ValueError,
        match="analysis IDs that were not verified as supported",
    ):
        agent.run(
            mission="Evaluate whether Acme Robotics should enter the target market.",
            research_result=_research_result(),
            analysis_result=_analysis_result(),
            verification_result=_verification_result(),
        )
