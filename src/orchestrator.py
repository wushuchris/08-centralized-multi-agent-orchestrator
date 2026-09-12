"""Central supervisor for the multi-agent workflow."""

from collections.abc import Iterator

from .analysis_agent import AnalysisAgent
from .research_agent import ResearchAgent
from .schemas import (
    AnalysisResult,
    ResearchResult,
    ResearchSource,
    SynthesisResult,
    VerificationResult,
)
from .state import AgentName, OrchestratorState
from .synthesis_agent import SynthesisAgent
from .verification_agent import VerificationAgent


class CentralOrchestrator:
    """Coordinate specialist agents through one centralized supervisor."""

    role = "orchestrator"

    def __init__(
        self,
        research_agent: ResearchAgent,
        analysis_agent: AnalysisAgent,
        verification_agent: VerificationAgent,
        synthesis_agent: SynthesisAgent,
    ) -> None:
        self.research_agent = research_agent
        self.analysis_agent = analysis_agent
        self.verification_agent = verification_agent
        self.synthesis_agent = synthesis_agent

    @staticmethod
    def _render_verified_answer(
        synthesis_result: SynthesisResult,
        verification_result: VerificationResult,
        analysis_result: AnalysisResult,
        research_result: ResearchResult,
        sources: list[ResearchSource],
    ) -> str:
        """Render publishable text while keeping source facts separate from inference."""

        analysis_by_id = {
            point.point_id: point
            for point in analysis_result.points
            if point.point_id is not None
        }

        lines = ["## Source-Backed Evidence"]
        for source in sources:
            lines.append(
                f"- **{source.source_id} — {source.title}:** {source.content}"
            )

        lines.extend(["", "## Orchestrator Assessment"])
        if verification_result.overall_status == "pass":
            lines.append(
                "- The specialist workflow found no material verification "
                "cautions in the analysis."
            )
        else:
            lines.append(
                "- The specialist workflow found usable analysis with cautions; "
                "unresolved issues should be addressed before a firm decision."
            )

        caution_checks = [
            check
            for check in verification_result.checks
            if check.verdict != "supported"
        ]
        if caution_checks or verification_result.corrections:
            lines.extend(["", "## Analytical Cautions"])
            for check in caution_checks:
                point = analysis_by_id[check.analysis_point_id]
                lines.append(
                    f"- Analysis interpretation: {point.statement} "
                    f"({check.verdict}). {check.reasoning}"
                )
            for correction in verification_result.corrections:
                lines.append(f"- Verification correction: {correction}")

        unresolved_questions = list(
            dict.fromkeys(
                research_result.open_questions
                + verification_result.unresolved_questions
            )
        )
        if unresolved_questions:
            lines.extend(["", "## Unresolved Questions"])
            for question in unresolved_questions:
                lines.append(f"- {question}")

        lines.extend(
            ["", f"**Confidence:** {synthesis_result.confidence}"]
        )
        return "\n".join(lines)

    @staticmethod
    def _snapshot(state: OrchestratorState) -> OrchestratorState:
        """Return an isolated deep copy suitable for UI streaming or auditing."""

        return state.model_copy(deep=True)

    def run_iter(
        self,
        mission: str,
        sources: list[ResearchSource],
    ) -> Iterator[OrchestratorState]:
        """Yield auditable state snapshots as each supervised stage changes state.

        The generator does not change the orchestration policy. It exposes the same
        application-owned routing and handoff boundaries incrementally so a caller
        can observe real progress without duplicating workflow logic in the UI.
        """

        state = OrchestratorState(mission=mission)
        active_agent: AgentName = "orchestrator"
        state.record_step(
            agent="orchestrator",
            action="start workflow",
            status="started",
        )
        yield self._snapshot(state)

        try:
            active_agent = "research"
            state.status = "researching"
            state.record_step(
                agent="research",
                action="produce research handoff",
                status="started",
            )
            yield self._snapshot(state)
            state.research_result = self.research_agent.run(
                mission=state.mission,
                sources=sources,
            )
            state.record_step(
                agent="research",
                action="produce research handoff",
                status="completed",
            )
            yield self._snapshot(state)

            active_agent = "analysis"
            state.status = "analyzing"
            state.record_step(
                agent="analysis",
                action="interpret research handoff",
                status="started",
            )
            yield self._snapshot(state)
            state.analysis_result = self.analysis_agent.run(
                mission=state.mission,
                research_result=state.research_result,
            )
            state.record_step(
                agent="analysis",
                action="interpret research handoff",
                status="completed",
            )
            yield self._snapshot(state)

            active_agent = "verification"
            state.status = "verifying"
            state.record_step(
                agent="verification",
                action="audit analysis against research",
                status="started",
            )
            yield self._snapshot(state)
            state.verification_result = self.verification_agent.run(
                mission=state.mission,
                research_result=state.research_result,
                analysis_result=state.analysis_result,
            )
            state.record_step(
                agent="verification",
                action="audit analysis against research",
                status="completed",
                note=f"overall_status={state.verification_result.overall_status}",
            )
            yield self._snapshot(state)

            if state.verification_result.overall_status == "needs_revision":
                state.status = "failed"
                state.error = "verification requires revision before synthesis"
                state.record_step(
                    agent="orchestrator",
                    action="route after verification",
                    status="failed",
                    note=state.error,
                )
                yield self._snapshot(state)
                return

            state.record_step(
                agent="orchestrator",
                action="route after verification",
                status="completed",
                note="continue to synthesis",
            )
            yield self._snapshot(state)

            active_agent = "synthesis"
            state.status = "synthesizing"
            state.record_step(
                agent="synthesis",
                action="produce final response",
                status="started",
            )
            yield self._snapshot(state)
            state.synthesis_result = self.synthesis_agent.run(
                mission=state.mission,
                research_result=state.research_result,
                analysis_result=state.analysis_result,
                verification_result=state.verification_result,
            )
            state.final_answer = self._render_verified_answer(
                synthesis_result=state.synthesis_result,
                verification_result=state.verification_result,
                analysis_result=state.analysis_result,
                research_result=state.research_result,
                sources=sources,
            )
            state.record_step(
                agent="synthesis",
                action="produce final response",
                status="completed",
                note="orchestrator published source facts separately from analysis",
            )
            yield self._snapshot(state)

            active_agent = "orchestrator"
            state.status = "completed"
            state.record_step(
                agent="orchestrator",
                action="complete workflow",
                status="completed",
            )
            yield self._snapshot(state)

        except Exception as exc:
            state.status = "failed"
            state.error = str(exc)
            state.record_step(
                agent=active_agent,
                action="execute assigned step",
                status="failed",
                note=state.error,
            )
            state.record_step(
                agent="orchestrator",
                action="fail workflow",
                status="failed",
                note=f"failed during {active_agent}",
            )
            yield self._snapshot(state)

    def run(
        self,
        mission: str,
        sources: list[ResearchSource],
    ) -> OrchestratorState:
        """Run the centralized workflow and return its final auditable state."""

        final_state: OrchestratorState | None = None
        for snapshot in self.run_iter(mission=mission, sources=sources):
            final_state = snapshot

        if final_state is None:  # pragma: no cover - defensive contract guard
            raise RuntimeError("orchestrator produced no state")
        return final_state
