"""Bounded specialist agent for producing the final evidence-linked response."""

from collections import Counter
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

Your job is narrow: select verified conclusions and draft a user-facing response from validated upstream handoffs.

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
- Select key points only from verification checks whose verdict is supported.
- For each selected key point, copy only its analysis_point_id. Do not reproduce or rewrite the claim text; application code will publish the canonical verified Analysis statement.
- Do not select partially_supported, unsupported, or conflicted analysis IDs as established conclusions.
- Preserve material corrections, cautions, and unresolved questions from verification in your draft response.
- If verification reports needs_revision, clearly reflect that limitation instead of masking it.
- The response field is an audit draft only. Application code, not your prose, owns the publishable final answer.
- Return valid JSON only.

Return exactly this shape:
{{
  "response": "draft user-facing answer for audit",
  "key_points": [
    {{
      "analysis_point_id": "analysis-1"
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

        supported_ids = {
            check.analysis_point_id
            for check in verification_result.checks
            if check.verdict == "supported"
        }
        selected_ids = [
            point.analysis_point_id
            for point in result.key_points
        ]

        unknown_ids = set(selected_ids) - supported_ids
        if unknown_ids:
            raise ValueError(
                "synthesis selected analysis IDs that were not verified as supported: "
                + ", ".join(sorted(unknown_ids))
            )

        duplicates = [
            point_id
            for point_id, count in Counter(selected_ids).items()
            if count > 1
        ]
        if duplicates:
            raise ValueError(
                "synthesis selected duplicate analysis IDs: "
                + ", ".join(sorted(duplicates))
            )

        return result
