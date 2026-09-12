"""Regression tests for incremental centralized-orchestrator observability."""

from src.orchestrator import CentralOrchestrator
from src.schemas import (
    AnalysisPoint,
    AnalysisResult,
    ResearchFinding,
    ResearchResult,
    ResearchSource,
    SynthesisPoint,
    SynthesisResult,
    VerificationCheck,
    VerificationResult,
)


class ResearchStub:
    def run(self, mission, sources):
        return ResearchResult(
            summary="Demand is growing.",
            findings=[
                ResearchFinding(
                    claim="Demand increased.",
                    evidence="The market brief reports 18% annual growth.",
                    source_ids=["market-brief"],
                    confidence="high",
                )
            ],
            open_questions=["Can service capacity scale?"],
        )


class AnalysisStub:
    def run(self, mission, research_result):
        return AnalysisResult(
            assessment="The opportunity merits further evaluation.",
            points=[
                AnalysisPoint(
                    point_id="analysis-1",
                    kind="opportunity",
                    statement="Demand supports further evaluation.",
                    reasoning="Research reports annual growth.",
                    source_ids=["market-brief"],
                    confidence="high",
                )
            ],
            assumptions=[],
            questions_for_verification=[],
        )


class VerificationStub:
    def run(self, mission, research_result, analysis_result):
        return VerificationResult(
            overall_status="pass",
            checks=[
                VerificationCheck(
                    analysis_point_id="analysis-1",
                    verdict="supported",
                    reasoning="The research supports the demand point.",
                    source_ids=["market-brief"],
                )
            ],
            corrections=[],
            unresolved_questions=[],
        )


class SynthesisStub:
    def run(self, mission, research_result, analysis_result, verification_result):
        return SynthesisResult(
            response="Draft synthesis.",
            key_points=[SynthesisPoint(analysis_point_id="analysis-1")],
            cautions=[],
            unresolved_questions=[],
            confidence="high",
        )


def test_run_iter_exposes_real_stage_progress_and_isolated_snapshots() -> None:
    orchestrator = CentralOrchestrator(
        research_agent=ResearchStub(),
        analysis_agent=AnalysisStub(),
        verification_agent=VerificationStub(),
        synthesis_agent=SynthesisStub(),
    )
    sources = [
        ResearchSource(
            source_id="market-brief",
            title="Synthetic Market Brief",
            content="Annual demand increased 18%.",
        )
    ]

    snapshots = list(
        orchestrator.run_iter(
            mission="Evaluate the synthetic market-entry opportunity.",
            sources=sources,
        )
    )

    assert snapshots[0].status == "created"
    assert snapshots[0].history[-1].agent == "orchestrator"
    assert snapshots[0].history[-1].action == "start workflow"
    assert len(snapshots[0].history) == 1

    assert any(
        snapshot.status == "researching"
        and snapshot.history[-1].agent == "research"
        and snapshot.history[-1].status == "started"
        for snapshot in snapshots
    )
    assert any(
        snapshot.status == "analyzing"
        and snapshot.history[-1].agent == "analysis"
        and snapshot.history[-1].status == "started"
        for snapshot in snapshots
    )
    assert any(
        snapshot.status == "verifying"
        and snapshot.history[-1].agent == "verification"
        and snapshot.history[-1].status == "started"
        for snapshot in snapshots
    )
    assert any(
        snapshot.status == "synthesizing"
        and snapshot.history[-1].agent == "synthesis"
        and snapshot.history[-1].status == "started"
        for snapshot in snapshots
    )

    final = snapshots[-1]
    assert final.status == "completed"
    assert final.final_answer is not None
    assert final.history[-1].agent == "orchestrator"
    assert final.history[-1].action == "complete workflow"
    assert len(final.history) > len(snapshots[0].history)

    # Earlier yielded snapshots must not mutate as later stages execute.
    assert snapshots[0].research_result is None
    assert snapshots[0].analysis_result is None
    assert snapshots[0].verification_result is None
    assert snapshots[0].synthesis_result is None
