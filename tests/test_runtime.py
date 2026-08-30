"""Tests for runtime assembly of the centralized orchestrator."""

from src.orchestrator import CentralOrchestrator
from src.runtime import build_orchestrator


def test_build_orchestrator_wires_shared_model_into_all_specialists() -> None:
    def fake_model(_: str) -> str:
        return "{}"

    orchestrator = build_orchestrator(model=fake_model)

    assert isinstance(orchestrator, CentralOrchestrator)
    assert orchestrator.research_agent.model is fake_model
    assert orchestrator.analysis_agent.model is fake_model
    assert orchestrator.verification_agent.model is fake_model
    assert orchestrator.synthesis_agent.model is fake_model
