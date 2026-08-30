"""Bounded specialist agent for auditing research-backed analysis."""

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
- Check whether each important analysis claim is actually supported by the research evidence it cites.
- Classify each checked claim as supported, partially_supported, unsupported, or conflicted.
- Every verification check must cite one or more source_id values already present in the research findings.
- Identify overstatement, unsupported inference, contradiction, or missing evidence.
- Put factual or analytical corrections in corrections.
- Preserve genuinely unresolved issues in unresolved_questions.
- Set overall_status to pass only when the analysis is materially supported without important cautions.
- Set overall_status to pass_with_cautions when the analysis is usable but contains limitations that synthesis must preserve.
- Set overall_status to needs_revision when a material claim is unsupported, conflicted, or substantially overstated.
- Do not decide whether the workflow continues; the central orchestrator owns routing decisions.
- Return valid JSON only.

Return exactly this shape:
{{
  "overall_status": "pass_with_cautions",
  "checks": [
    {{
      "target": "analysis claim being audited",
      "verdict": "supported",
      "reasoning": "why the research does or does not support the claim",
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

        return result
