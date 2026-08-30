"""Bounded specialist agent for evidence-linked analysis."""

from collections.abc import Callable
import json

from .schemas import AnalysisResult, ResearchResult


AnalysisModel = Callable[[str], str]


class AnalysisAgent:
    """Interpret validated research findings without introducing new facts."""

    role = "analysis"

    def __init__(self, model: AnalysisModel) -> None:
        self.model = model

    def build_prompt(
        self,
        mission: str,
        research_result: ResearchResult,
    ) -> str:
        """Build the bounded prompt given to the analysis model."""

        research_packet = research_result.model_dump_json(indent=2)

        return f"""You are the Analysis Agent in a centralized multi-agent system.

Your job is narrow: interpret the validated research handoff and identify implications relevant to the mission.

MISSION:
{mission}

VALIDATED RESEARCH HANDOFF:
{research_packet}

Rules:
- Use only information contained in the validated research handoff.
- Do not invent new facts, evidence, source IDs, entity relationships, or comparative claims.
- Do not perform new research.
- Every analysis point must cite one or more source_id values already present in the research findings.
- Preserve the epistemic strength of the research. Do not upgrade related evidence into a stronger claim.
- If the research says competitors compete on speed and service, you may say those are competitive dimensions; do not say the competitors dominate, outperform, or are superior unless the research explicitly establishes that.
- If the research says customers show interest in automation, you may say demand exists for automation; do not say that demand aligns with this company's offering unless the research explicitly describes that offering and establishes the fit.
- If a capability is unresolved, describe it as unresolved; do not call it inadequate, insufficient, or a proven weakness.
- When an implication requires interpretation rather than direct evidence, use bounded language such as may, could, or suggests and lower confidence appropriately.
- Distinguish opportunities, risks, constraints, and uncertainties.
- Explain the reasoning that connects the research evidence to each analysis point.
- Record any assumptions explicitly rather than presenting them as facts.
- Put claims that deserve independent checking in questions_for_verification.
- Questions must be neutral and must not embed an unsupported premise. Ask what must be learned, not what must be done to fix a problem that has not been established.
- Do not make the final recommendation; the Synthesis Agent will own the final answer.
- Return valid JSON only.

Return exactly this shape:
{{
  "assessment": "overall interpretation of the research",
  "points": [
    {{
      "kind": "opportunity",
      "statement": "analysis point",
      "reasoning": "why the research supports this interpretation",
      "source_ids": ["source-1"],
      "confidence": "high"
    }}
  ],
  "assumptions": [],
  "questions_for_verification": []
}}
"""

    def run(
        self,
        mission: str,
        research_result: ResearchResult,
    ) -> AnalysisResult:
        """Run the analysis model and validate its handoff contract."""

        if not mission.strip():
            raise ValueError("mission must not be empty")

        prompt = self.build_prompt(mission, research_result)
        raw_response = self.model(prompt)

        try:
            payload = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise ValueError("analysis model returned invalid JSON") from exc

        result = AnalysisResult.model_validate(payload)

        approved_ids = {
            source_id
            for finding in research_result.findings
            for source_id in finding.source_ids
        }
        cited_ids = {
            source_id
            for point in result.points
            for source_id in point.source_ids
        }
        unknown_ids = cited_ids - approved_ids

        if unknown_ids:
            raise ValueError(
                "analysis model cited unknown source IDs: "
                + ", ".join(sorted(unknown_ids))
            )

        return result
