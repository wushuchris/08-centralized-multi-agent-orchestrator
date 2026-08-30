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


class AnalysisPoint(BaseModel):
    """One evidence-linked implication derived from the research handoff."""

    kind: Literal["opportunity", "risk", "constraint", "uncertainty"]
    statement: str = Field(min_length=1)
    reasoning: str = Field(min_length=1)
    source_ids: list[str] = Field(min_length=1)
    confidence: Literal["high", "medium", "low"]


class AnalysisResult(BaseModel):
    """Validated handoff from the Analysis Agent to the orchestrator."""

    assessment: str = Field(min_length=1)
    points: list[AnalysisPoint] = Field(min_length=1)
    assumptions: list[str] = Field(default_factory=list)
    questions_for_verification: list[str] = Field(default_factory=list)


class VerificationCheck(BaseModel):
    """One audit judgment about an analysis claim."""

    target: str = Field(min_length=1)
    verdict: Literal[
        "supported",
        "partially_supported",
        "unsupported",
        "conflicted",
    ]
    reasoning: str = Field(min_length=1)
    source_ids: list[str] = Field(min_length=1)


class VerificationResult(BaseModel):
    """Validated audit handoff from the Verification Agent."""

    overall_status: Literal["pass", "pass_with_cautions", "needs_revision"]
    checks: list[VerificationCheck] = Field(min_length=1)
    corrections: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
