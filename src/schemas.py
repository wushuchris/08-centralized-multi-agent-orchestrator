"""Structured contracts passed between specialist agents."""

from typing import Literal

from pydantic import BaseModel, Field


class ResearchSource(BaseModel):
    """One source supplied to the Research Agent."""

    source_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)


class ResearchFinding(BaseModel):
    """One evidence-backed finding produced by the Research Agent."""

    claim: str = Field(min_length=1)
    evidence: str = Field(min_length=1)
    source_ids: list[str] = Field(min_length=1)
    confidence: Literal["high", "medium", "low"]


class ResearchResult(BaseModel):
    """Validated handoff from the Research Agent to the orchestrator."""

    summary: str = Field(min_length=1)
    findings: list[ResearchFinding] = Field(min_length=1)
    open_questions: list[str] = Field(default_factory=list)
