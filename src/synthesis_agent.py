"""Bounded specialist agent for producing the final evidence-linked response."""

from collections.abc import Callable
import json

from .schemas import (
    AnalysisResult,
    ResearchResult,
    SynthesisResult,
    VerificationResult,
)


SynthesisModel = Callable[[str], str]


class SynthesisAgent:
    """Synthesize validated specialist handoffs into a user-facing response."""

    role = "synthesis"

    def __init__(self, model: SynthesisModel) -> None:
        self.model = model

    def build_prompt(
        self,
        mission: str,
        research_result: ResearchResult,
        analysis_result: AnalysisResult,
        verification_result: VerificationResult,
    ) -> str:
        """Build the bounded prompt given to the synthesis model."""

        research_packet = research_result.model_dump_json(indent=2)
        analysis_packet = analysis_result.model_dump_json(indent=2)
        verification_packet = verification_result.model_dump_json(indent=2)

        return f"""You are the Synthesis Agent in a centralized multi-agent system.

Your job is narrow: produce the final user-facing response from validated upstream handoffs.

MISSION:
{mission}

VALIDATED RESEARCH HANDOFF:
{research_packet}

VALIDATED ANALYSIS HANDOFF:
{analysis_packet}

VALIDATED VERIFICATION HANDOFF:
{verification_packet}

Rules:
- Use only the validated handoffs provided above.
- Do not perform new research or introduce outside facts.
- Base key points on research evidence that survived analysis and verification.
- Every key point must cite one or more source_id values already present in the research findings.
- Preserve material corrections, cautions, and unresolved questions from verification.
- Do not present unsupported, conflicted, or partially supported claims as established facts.
- If verification reports needs_revision, clearly reflect that limitation instead of masking it.
- Keep the response useful, concise, and directly responsive to the mission.
- Return valid JSON only.

Return exactly this shape:
{{
  "response": "clear user-facing answer",
  "key_points": [
    {{
      "statement": "evidence-backed conclusion",
      "source_ids": ["source-1"]
    }}
  ],
  "cautions": [],
  "unresolved_questions": [],
  "confidence": "medium"
}}
"""

    def run(
        self,
        mission: str,
        research_result: ResearchResult,
        analysis_result: AnalysisResult,
        verification_result: VerificationResult,
    ) -> SynthesisResult:
        """Run the synthesis model and validate its final handoff."""

        if not mission.strip():
            raise ValueError("mission must not be empty")

        prompt = self.build_prompt(
            mission=mission,
            research_result=research_result,
            analysis_result=analysis_result,
            verification_result=verification_result,
        )
        raw_response = self.model(prompt)

        try:
            payload = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise ValueError("synthesis model returned invalid JSON") from exc

        result = SynthesisResult.model_validate(payload)

        approved_ids = {
            source_id
            for finding in research_result.findings
            for source_id in finding.source_ids
        }
        cited_ids = {
            source_id
            for point in result.key_points
            for source_id in point.source_ids
        }
        unknown_ids = cited_ids - approved_ids

        if unknown_ids:
            raise ValueError(
                "synthesis model cited unknown source IDs: "
                + ", ".join(sorted(unknown_ids))
            )

        return result
