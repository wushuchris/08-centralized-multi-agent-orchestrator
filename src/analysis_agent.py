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
- Do not invent new facts, evidence, or source IDs.
- Do not perform new research.
- Every analysis point must cite one or more source_id values already present in the research findings.
- Distinguish opportunities, risks, constraints, and uncertainties.
- Explain the reasoning that connects the research evidence to each analysis point.
- Record any assumptions explicitly.
- Put claims that deserve independent checking in questions_for_verification.
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
