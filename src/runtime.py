"""Runtime assembly for the centralized multi-agent orchestrator."""

from collections.abc import Callable

from .analysis_agent import AnalysisAgent
from .model_adapter import HuggingFaceChatModel
from .orchestrator import CentralOrchestrator
from .research_agent import ResearchAgent
from .synthesis_agent import SynthesisAgent
from .verification_agent import VerificationAgent


TextModel = Callable[[str], str]


def build_orchestrator(model: TextModel | None = None) -> CentralOrchestrator:
    """Build a ready-to-run orchestrator with one shared model adapter."""

    shared_model = model or HuggingFaceChatModel()

    return CentralOrchestrator(
        research_agent=ResearchAgent(model=shared_model),
        analysis_agent=AnalysisAgent(model=shared_model),
        verification_agent=VerificationAgent(model=shared_model),
        synthesis_agent=SynthesisAgent(model=shared_model),
    )
