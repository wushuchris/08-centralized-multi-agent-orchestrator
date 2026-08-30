"""Tests for the Gradio application handler."""

import app
from src.schemas import (
    AnalysisPoint,
    AnalysisResult,
    ResearchFinding,
    ResearchResult,
    SynthesisPoint,
    SynthesisResult,
    VerificationCheck,
    VerificationResult,
)
from src.state import OrchestratorState


class FakeOrchestrator:
    """Return a completed state without making any model calls."""

    def run(self, mission, sources):
        assert mission == "Evaluate the synthetic opportunity."
        assert [source.source_id for source in sources] == [
            "market-brief",
            "operations-brief",
            "competition-brief",
        ]

        research = ResearchResult(
            summary="Demand is growing.",
            findings=[
                ResearchFinding(
                    claim="Demand increased.",
                    evidence="The market brief reports 18% annual growth.",
                    source_ids=["market-brief"],
                    confidence="high",
                )
            ],
            open_questions=[],
        )
        analysis = AnalysisResult(
            assessment="The opportunity is promising.",
            points=[
                AnalysisPoint(
                    kind="opportunity",
                    statement="Demand supports further evaluation.",
                    reasoning="The research reports strong annual growth.",
                    source_ids=["market-brief"],
                    confidence="high",
                )
            ],
            assumptions=[],
            questions_for_verification=[],
        )
        verification = VerificationResult(
            overall_status="pass",
            checks=[
                VerificationCheck(
                    target="Demand supports further evaluation.",
                    verdict="supported",
                    reasoning="The research directly supports the demand claim.",
                    source_ids=["market-brief"],
                )
            ],
            corrections=[],
            unresolved_questions=[],
        )
        synthesis = SynthesisResult(
            response="The evidence supports further evaluation.",
            key_points=[
                SynthesisPoint(
                    statement="Demand increased 18% annually.",
                    source_ids=["market-brief"],
                )
            ],
            cautions=[],
            unresolved_questions=[],
            confidence="high",
        )

        state = OrchestratorState(
            mission=mission,
            status="completed",
            research_result=research,
            analysis_result=analysis,
            verification_result=verification,
            synthesis_result=synthesis,
            final_answer=synthesis.response,
        )
        state.record_step(
            agent="orchestrator",
            action="complete workflow",
            status="completed",
        )
        return state


def test_handle_request_exposes_structured_workflow(monkeypatch) -> None:
    monkeypatch.setattr(app, "ORCHESTRATOR", FakeOrchestrator())

    result = app.handle_request(
        "Evaluate the synthetic opportunity.",
        "Demand increased 18%.",
        "Service capacity is still being evaluated.",
        "Two competitors serve the market.",
    )

    (
        final_answer,
        status,
        error,
        research,
        analysis,
        verification,
        synthesis,
        history,
    ) = result

    assert final_answer == "The evidence supports further evaluation."
    assert status == "completed"
    assert error == ""
    assert research["findings"][0]["source_ids"] == ["market-brief"]
    assert analysis["points"][0]["kind"] == "opportunity"
    assert verification["overall_status"] == "pass"
    assert synthesis["confidence"] == "high"
    assert history[-1]["agent"] == "orchestrator"
