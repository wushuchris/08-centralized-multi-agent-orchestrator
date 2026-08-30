"""Tests for the bounded Verification Agent."""

import json

import pytest

from src.schemas import (
    AnalysisPoint,
    AnalysisResult,
    ResearchFinding,
    ResearchResult,
)
from src.verification_agent import VerificationAgent


def test_verification_agent_audits_research_backed_analysis() -> None:
    captured_prompt = ""

    def fake_model(prompt: str) -> str:
        nonlocal captured_prompt
        captured_prompt = prompt
        return json.dumps(
            {
                "overall_status": "pass_with_cautions",
                "checks": [
                    {
                        "analysis_point_id": "analysis-1",
                        "verdict": "supported",
                        "reasoning": "The research handoff reports 18% annual demand growth in the target market.",
                        "source_ids": ["market-brief"],
                    },
                    {
                        "analysis_point_id": "analysis-2",
                        "verdict": "partially_supported",
                        "reasoning": "The research identifies service capacity as an unresolved question, but does not establish that capacity is currently inadequate.",
                        "source_ids": ["market-brief"],
                    },
                ],
                "corrections": [
                    "Treat service-capacity risk as unresolved rather than established."
                ],
                "unresolved_questions": [
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

    analysis_result = AnalysisResult(
        assessment="The market opportunity is promising, but operational readiness remains uncertain.",
        points=[
            AnalysisPoint(
                point_id="analysis-1",
                kind="opportunity",
                statement="Demand growth supports considering market entry.",
                reasoning="The research finding reports 18% annual demand growth in the target market.",
                source_ids=["market-brief"],
                confidence="high",
            ),
            AnalysisPoint(
                point_id="analysis-2",
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

    agent = VerificationAgent(model=fake_model)
    result = agent.run(
        mission="Evaluate whether Acme Robotics should enter the target market.",
        research_result=research_result,
        analysis_result=analysis_result,
    )

    assert "18%" in captured_prompt
    assert '"point_id": "analysis-1"' in captured_prompt
    assert "copy the analysis point's point_id exactly" in captured_prompt
    assert "Related evidence is not enough" in captured_prompt
    assert "dominance, superiority, alignment" in captured_prompt
    assert result.overall_status == "pass_with_cautions"
    assert result.checks[0].analysis_point_id == "analysis-1"
    assert result.checks[0].verdict == "supported"
    assert result.checks[1].verdict == "partially_supported"
    assert result.checks[0].source_ids == ["market-brief"]
    assert result.corrections
    assert result.unresolved_questions


def test_verification_agent_rejects_unknown_analysis_point_id() -> None:
    research_result = ResearchResult(
        summary="Competition exists on implementation speed and service coverage.",
        findings=[
            ResearchFinding(
                claim="Two established competitors serve the target market.",
                evidence=(
                    "Both competitors compete on implementation speed and "
                    "post-sale service coverage."
                ),
                source_ids=["competition-brief"],
                confidence="high",
            )
        ],
    )

    analysis_result = AnalysisResult(
        assessment="Speed and service coverage are relevant competitive dimensions.",
        points=[
            AnalysisPoint(
                point_id="analysis-1",
                kind="constraint",
                statement=(
                    "Implementation speed and service coverage are competitive "
                    "dimensions in the target market."
                ),
                reasoning=(
                    "The research says both established competitors compete on "
                    "those dimensions."
                ),
                source_ids=["competition-brief"],
                confidence="high",
            )
        ],
    )

    def wrong_id_model(_: str) -> str:
        return json.dumps(
            {
                "overall_status": "pass",
                "checks": [
                    {
                        "analysis_point_id": "analysis-999",
                        "verdict": "supported",
                        "reasoning": "The source discusses speed and service coverage.",
                        "source_ids": ["competition-brief"],
                    }
                ],
                "corrections": [],
                "unresolved_questions": [],
            }
        )

    agent = VerificationAgent(model=wrong_id_model)

    with pytest.raises(
        ValueError,
        match="verification checks must audit every analysis point ID exactly once",
    ):
        agent.run(
            mission="Evaluate market-entry conditions.",
            research_result=research_result,
            analysis_result=analysis_result,
        )
