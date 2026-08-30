"""Tests for the bounded Research Agent."""

import json

from src.research_agent import ResearchAgent
from src.schemas import ResearchSource


def test_research_agent_returns_valid_structured_result() -> None:
    captured_prompt = ""

    def fake_model(prompt: str) -> str:
        nonlocal captured_prompt
        captured_prompt = prompt
        return json.dumps(
            {
                "summary": "Demand is growing, but execution risk remains.",
                "findings": [
                    {
                        "claim": "Target-market demand increased year over year.",
                        "evidence": "The supplied market brief reports 18% annual demand growth.",
                        "source_ids": ["market-brief"],
                        "confidence": "high",
                    }
                ],
                "open_questions": [
                    "Can the company support the required service footprint?"
                ],
            }
        )

    agent = ResearchAgent(model=fake_model)
    sources = [
        ResearchSource(
            source_id="market-brief",
            title="Synthetic Market Brief",
            content="Annual demand in the target market increased 18%.",
        )
    ]

    result = agent.run(
        mission="Evaluate whether Acme Robotics should enter the target market.",
        sources=sources,
    )

    assert "Acme Robotics" in captured_prompt
    assert "18%" in captured_prompt
    assert result.findings[0].source_ids == ["market-brief"]
    assert result.findings[0].confidence == "high"
    assert result.open_questions
