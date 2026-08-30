"""Bounded specialist agent for auditing research-backed analysis."""

from collections import Counter
from collections.abc import Callable
import json

from .schemas import AnalysisResult, ResearchResult, VerificationResult


VerificationModel = Callable[[str], str]


class VerificationAgent:
    """Audit whether analysis claims are supported by validated research."""

    role = "verification"

    def __init__(self, model: VerificationModel) -> None:
        self.model = model

    def build_prompt(
        self,
        mission: str,
        research_result: ResearchResult,
        analysis_result: AnalysisResult,
    ) -> str:
        """Build the bounded prompt given to the verification model."""

        research_packet = research_result.model_dump_json(indent=2)
        analysis_packet = analysis_result.model_dump_json(indent=2)

        return f"""You are the Verification Agent in a centralized multi-agent system.

Your job is narrow: audit the validated analysis against the validated research handoff.

MISSION:
{mission}

VALIDATED RESEARCH HANDOFF:
{research_packet}

VALIDATED ANALYSIS HANDOFF:
{analysis_packet}

Rules:
- Use only the research and analysis handoffs provided above.
- Do not perform new research or introduce outside facts.
- Audit every analysis point exactly once.
- For each check, copy the analysis point's point_id exactly into analysis_point_id. The ID is the stable handoff reference; do not invent or change IDs.
- Judge the exact analysis statement associated with that ID, not merely its general topic.
- Mark a claim supported only when the cited research explicitly establishes every material assertion in that statement. Related evidence is not enough.
- If a statement adds dominance, superiority, alignment, product fit, inadequacy, causation, certainty, guarantees, comparative gaps, or other stronger relationships not explicitly established by the research, mark it partially_supported or unsupported as appropriate.
- If the research establishes only uncertainty, do not approve a statement that converts the uncertainty into an established weakness or fact.
- Classify each checked claim as supported, partially_supported, unsupported, or conflicted.
- Every verification check must cite one or more source_id values already cited by the analysis point being audited.
- Identify overstatement, unsupported inference, contradiction, or missing evidence.
- Put factual or analytical corrections in corrections.
- Preserve genuinely unresolved issues in unresolved_questions.
- Unresolved questions must be neutral and must not embed an unsupported premise. Ask what evidence is missing rather than assuming a gap or deficiency exists.
- Set overall_status to pass only when the analysis is materially supported without important cautions.
- Set overall_status to pass_with_cautions when the analysis is usable but contains non-material limitations that synthesis must preserve.
- Set overall_status to needs_revision when a material claim is unsupported, conflicted, or substantially overstated.
- Do not decide whether the workflow continues; the central orchestrator owns routing decisions.
- Return valid JSON only.

Return exactly this shape:
{{
  "overall_status": "pass_with_cautions",
  "checks": [
    {{
      "analysis_point_id": "analysis-1",
      "verdict": "supported",
      "reasoning": "why the research does or does not support that analysis point",
      "source_ids": ["source-1"]
    }}
  ],
  "corrections": [],
  "unresolved_questions": []
}}
"""

    def run(
        self,
        mission: str,
        research_result: ResearchResult,
        analysis_result: AnalysisResult,
    ) -> VerificationResult:
        """Run the verification model and validate its audit handoff."""

        if not mission.strip():
            raise ValueError("mission must not be empty")

        prompt = self.build_prompt(
            mission=mission,
            research_result=research_result,
            analysis_result=analysis_result,
        )
        raw_response = self.model(prompt)

        try:
            payload = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise ValueError("verification model returned invalid JSON") from exc

        result = VerificationResult.model_validate(payload)

        approved_ids = {
            source_id
            for finding in research_result.findings
            for source_id in finding.source_ids
        }
        cited_ids = {
            source_id
            for check in result.checks
            for source_id in check.source_ids
        }
        unknown_ids = cited_ids - approved_ids

        if unknown_ids:
            raise ValueError(
                "verification model cited unknown source IDs: "
                + ", ".join(sorted(unknown_ids))
            )

        analysis_ids = [
            point.point_id
            for point in analysis_result.points
            if point.point_id is not None
        ]
        if len(analysis_ids) != len(analysis_result.points):
            raise ValueError("analysis handoff contains a point without a stable ID")

        verification_ids = [
            check.analysis_point_id
            for check in result.checks
        ]
        if Counter(verification_ids) != Counter(analysis_ids):
            missing = list((Counter(analysis_ids) - Counter(verification_ids)).elements())
            unexpected = list((Counter(verification_ids) - Counter(analysis_ids)).elements())
            details = []
            if missing:
                details.append("missing IDs: " + ", ".join(missing))
            if unexpected:
                details.append("unexpected IDs: " + ", ".join(unexpected))
            raise ValueError(
                "verification checks must audit every analysis point ID exactly once"
                + (": " + " | ".join(details) if details else "")
            )

        analysis_by_id = {
            point.point_id: point
            for point in analysis_result.points
        }
        for check in result.checks:
            point = analysis_by_id[check.analysis_point_id]
            if not set(check.source_ids).issubset(set(point.source_ids)):
                raise ValueError(
                    "verification check cited sources outside its analysis point: "
                    + check.analysis_point_id
                )

        return result
