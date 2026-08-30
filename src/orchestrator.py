"""Central supervisor for the multi-agent workflow."""

from .analysis_agent import AnalysisAgent
from .research_agent import ResearchAgent
from .schemas import ResearchSource, SynthesisResult, VerificationResult
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
    ) -> str:
        """Render the publishable answer from verified structured claims."""

        lines = ["## Evidence-Backed Conclusions"]
        for point in synthesis_result.key_points:
            source_label = ", ".join(point.source_ids)
            lines.append(f"- {point.statement} — sources: {source_label}")

        caution_checks = [
            check
            for check in verification_result.checks
            if check.verdict != "supported"
        ]
        if caution_checks or verification_result.corrections:
            lines.extend(["", "## Cautions"])
            for check in caution_checks:
                lines.append(
                    f"- {check.target} ({check.verdict}): {check.reasoning}"
                )
            for correction in verification_result.corrections:
                lines.append(f"- {correction}")

        if verification_result.unresolved_questions:
            lines.extend(["", "## Unresolved Questions"])
            for question in verification_result.unresolved_questions:
                lines.append(f"- {question}")

        lines.extend(
            ["", f"**Confidence:** {synthesis_result.confidence}"]
        )
        return "\n".join(lines)

    def run(
        self,
        mission: str,
        sources: list[ResearchSource],
    ) -> OrchestratorState:
        """Run the centralized workflow and return its auditable state."""

        state = OrchestratorState(mission=mission)
        active_agent: AgentName = "orchestrator"
        state.record_step(
            agent="orchestrator",
            action="start workflow",
            status="started",
        )

        try:
            active_agent = "research"
            state.status = "researching"
            state.record_step(
                agent="research",
                action="produce research handoff",
                status="started",
            )
            state.research_result = self.research_agent.run(
                mission=state.mission,
                sources=sources,
            )
            state.record_step(
                agent="research",
                action="produce research handoff",
                status="completed",
            )

            active_agent = "analysis"
            state.status = "analyzing"
            state.record_step(
                agent="analysis",
                action="interpret research handoff",
                status="started",
            )
            state.analysis_result = self.analysis_agent.run(
                mission=state.mission,
                research_result=state.research_result,
            )
            state.record_step(
                agent="analysis",
                action="interpret research handoff",
                status="completed",
            )

            active_agent = "verification"
            state.status = "verifying"
            state.record_step(
                agent="verification",
                action="audit analysis against research",
                status="started",
            )
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

            if state.verification_result.overall_status == "needs_revision":
                state.status = "failed"
                state.error = "verification requires revision before synthesis"
                state.record_step(
                    agent="orchestrator",
                    action="route after verification",
                    status="failed",
                    note=state.error,
                )
                return state

            state.record_step(
                agent="orchestrator",
                action="route after verification",
                status="completed",
                note="continue to synthesis",
            )

            active_agent = "synthesis"
            state.status = "synthesizing"
            state.record_step(
                agent="synthesis",
                action="produce final response",
                status="started",
            )
            state.synthesis_result = self.synthesis_agent.run(
                mission=state.mission,
                research_result=state.research_result,
                analysis_result=state.analysis_result,
                verification_result=state.verification_result,
            )
            state.final_answer = self._render_verified_answer(
                synthesis_result=state.synthesis_result,
                verification_result=state.verification_result,
            )
            state.record_step(
                agent="synthesis",
                action="produce final response",
                status="completed",
                note="orchestrator published verified structured output",
            )

            active_agent = "orchestrator"
            state.status = "completed"
            state.record_step(
                agent="orchestrator",
                action="complete workflow",
                status="completed",
            )
            return state

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
            return state
