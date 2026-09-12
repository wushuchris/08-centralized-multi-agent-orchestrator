"""Tests for the Gradio application and business-first streaming demo."""

import gradio as gr

import app
from src.demo_presentation import APP_CSS, HERO_HTML, TEAM_HTML
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


def _completed_state(mission: str) -> OrchestratorState:
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
                point_id="analysis-1",
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
                analysis_point_id="analysis-1",
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
        key_points=[SynthesisPoint(analysis_point_id="analysis-1")],
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
        final_answer="The evidence supports further evaluation.",
    )
    state.record_step(
        agent="orchestrator",
        action="start workflow",
        status="started",
    )
    state.record_step(
        agent="research",
        action="produce research handoff",
        status="completed",
    )
    state.record_step(
        agent="analysis",
        action="interpret research handoff",
        status="completed",
    )
    state.record_step(
        agent="verification",
        action="audit analysis against research",
        status="completed",
        note="overall_status=pass",
    )
    state.record_step(
        agent="orchestrator",
        action="route after verification",
        status="completed",
        note="continue to synthesis",
    )
    state.record_step(
        agent="synthesis",
        action="produce final response",
        status="completed",
        note="orchestrator published source facts separately from analysis",
    )
    state.record_step(
        agent="orchestrator",
        action="complete workflow",
        status="completed",
    )
    return state


class FakeOrchestrator:
    """Return controlled states without making any model calls."""

    def run(self, mission, sources):
        assert mission == "Evaluate the synthetic opportunity."
        assert [source.source_id for source in sources] == [
            "market-brief",
            "operations-brief",
            "competition-brief",
        ]
        return _completed_state(mission)

    def run_iter(self, mission, sources):
        assert mission == "Evaluate the synthetic opportunity."
        assert [source.source_id for source in sources] == [
            "market-brief",
            "operations-brief",
            "competition-brief",
        ]

        running = OrchestratorState(mission=mission, status="researching")
        running.record_step(
            agent="orchestrator",
            action="start workflow",
            status="started",
        )
        running.record_step(
            agent="research",
            action="produce research handoff",
            status="started",
        )
        yield running
        yield _completed_state(mission)


def test_gradio_app_builds_as_centered_business_demo() -> None:
    assert isinstance(app.demo, gr.Blocks)
    assert "max-width:1080px" in APP_CSS
    assert "who keeps the team aligned" in HERO_HTML
    assert "Central Supervisor" in TEAM_HTML
    assert "Evidence Verifier" in TEAM_HTML


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
    assert analysis["points"][0]["point_id"] == "analysis-1"
    assert analysis["points"][0]["kind"] == "opportunity"
    assert verification["checks"][0]["analysis_point_id"] == "analysis-1"
    assert verification["overall_status"] == "pass"
    assert synthesis["key_points"][0]["analysis_point_id"] == "analysis-1"
    assert synthesis["confidence"] == "high"
    assert history[-1]["agent"] == "orchestrator"


def test_stream_request_exposes_real_running_and_completed_views(monkeypatch) -> None:
    monkeypatch.setattr(app, "ORCHESTRATOR", FakeOrchestrator())

    frames = list(
        app.stream_request_ui(
            "Evaluate the synthetic opportunity.",
            "Demand increased 18%.",
            "Service capacity is still being evaluated.",
            "Two competitors serve the market.",
        )
    )

    assert len(frames) == 2
    assert len(frames[0]) == app.UI_OUTPUT_COUNT
    assert "RUNNING" in frames[0][0]
    assert "Research Specialist" in frames[0][0]
    assert frames[0][5] == "researching"

    final = frames[-1]
    assert "COMPLETE" in final[0]
    assert "publication gate" in final[1]
    assert final[2] == "The evidence supports further evaluation."
    assert "1/1" in final[3]
    assert "RESEARCH HANDOFF" in final[4]
    assert "ANALYSIS HANDOFF" in final[4]
    assert "VERIFICATION HANDOFF" in final[4]
    assert "SYNTHESIS HANDOFF" in final[4]
    assert final[5] == "completed"
    assert final[-1][-1]["action"] == "complete workflow"
