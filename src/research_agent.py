"""Bounded specialist agent for evidence-focused research."""

from collections.abc import Callable
import json

from .schemas import ResearchResult, ResearchSource


ResearchModel = Callable[[str], str]


class ResearchAgent:
    """Analyze an approved research packet and return structured findings."""

    role = "research"

    def __init__(self, model: ResearchModel) -> None:
        self.model = model

    def build_prompt(
        self,
        mission: str,
        sources: list[ResearchSource],
    ) -> str:
        """Build the bounded prompt given to the research model."""

        source_packet = "\n\n".join(
            f"SOURCE {source.source_id}: {source.title}\n{source.content}"
            for source in sources
        )

        return f"""You are the Research Agent in a centralized multi-agent system.

Your job is narrow: examine only the approved source packet and identify evidence relevant to the mission.

MISSION:
{mission}

APPROVED SOURCE PACKET:
{source_packet}

Rules:
- Use only information contained in the approved source packet.
- Do not invent facts or outside sources.
- Every finding must cite one or more source_id values from the packet.
- Separate direct evidence from interpretation.
- Mark confidence as high, medium, or low.
- Record unresolved issues in open_questions.
- Return valid JSON only.

Return exactly this shape:
{{
  "summary": "short research summary",
  "findings": [
    {{
      "claim": "finding",
      "evidence": "supporting evidence from the packet",
      "source_ids": ["source-1"],
      "confidence": "high"
    }}
  ],
  "open_questions": []
}}
"""

    def run(
        self,
        mission: str,
        sources: list[ResearchSource],
    ) -> ResearchResult:
        """Run the specialist model and validate its handoff contract."""

        if not mission.strip():
            raise ValueError("mission must not be empty")
        if not sources:
            raise ValueError("at least one research source is required")

        prompt = self.build_prompt(mission, sources)
        raw_response = self.model(prompt)

        try:
            payload = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise ValueError("research model returned invalid JSON") from exc

        result = ResearchResult.model_validate(payload)

        approved_ids = {source.source_id for source in sources}
        cited_ids = {
            source_id
            for finding in result.findings
            for source_id in finding.source_ids
        }
        unknown_ids = cited_ids - approved_ids

        if unknown_ids:
            raise ValueError(
                "research model cited unknown source IDs: "
                + ", ".join(sorted(unknown_ids))
            )

        return result
