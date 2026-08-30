"""Gradio demo for the centralized multi-agent orchestrator."""

import gradio as gr

from src.runtime import build_orchestrator
from src.schemas import ResearchSource


ORCHESTRATOR = build_orchestrator()

DEFAULT_MISSION = (
    "Evaluate whether Acme Robotics should enter the target market and explain "
    "the strongest evidence, risks, and unresolved questions."
)

DEFAULT_MARKET = (
    "Annual demand in the target market increased 18% over the prior year. "
    "Customers report increasing interest in automation that reduces repetitive "
    "warehouse tasks."
)

DEFAULT_OPERATIONS = (
    "Acme Robotics currently supports customers through two regional service "
    "teams. Management has not yet established whether those teams can support "
    "a larger geographic footprint without additional hiring."
)

DEFAULT_COMPETITION = (
    "Two established competitors already serve the target market. Both compete "
    "on implementation speed and post-sale service coverage."
)


def _dump(result):
    """Convert an optional Pydantic result into JSON-friendly data."""

    if result is None:
        return None
    return result.model_dump(mode="json")


def handle_request(
    mission: str,
    market_source: str,
    operations_source: str,
    competition_source: str,
):
    """Run the orchestrator and expose its final answer and audit trail."""

    if not mission or not mission.strip():
        return (
            "Please enter a mission.",
            "failed",
            "mission must not be empty",
            None,
            None,
            None,
            None,
            [],
        )

    source_specs = [
        ("market-brief", "Synthetic Market Brief", market_source),
        ("operations-brief", "Synthetic Operations Brief", operations_source),
        ("competition-brief", "Synthetic Competition Brief", competition_source),
    ]

    sources = [
        ResearchSource(
            source_id=source_id,
            title=title,
            content=content.strip(),
        )
        for source_id, title, content in source_specs
        if content and content.strip()
    ]

    if not sources:
        return (
            "Please provide at least one approved source.",
            "failed",
            "at least one research source is required",
            None,
            None,
            None,
            None,
            [],
        )

    state = ORCHESTRATOR.run(
        mission=mission.strip(),
        sources=sources,
    )

    final_answer = state.final_answer or (
        "The workflow did not produce a final answer. Review the status, "
        "verification result, and audit history below."
    )

    history = [
        step.model_dump(mode="json")
        for step in state.history
    ]

    return (
        final_answer,
        state.status,
        state.error or "",
        _dump(state.research_result),
        _dump(state.analysis_result),
        _dump(state.verification_result),
        _dump(state.synthesis_result),
        history,
    )


APP_DESCRIPTION = """
# Centralized Multi-Agent Orchestrator

A supervisor-agent system that coordinates four bounded specialist agents:
**Research → Analysis → Verification → Synthesis**.

The central orchestrator owns routing, shared state, handoffs, completion, and
failure handling. Specialist agents control only the reasoning assigned to their
role.

This public demo uses an editable **synthetic source packet**. The Research Agent
may use only those approved sources. If Verification returns `needs_revision`,
the supervisor stops the workflow before Synthesis.
"""


with gr.Blocks(title="Centralized Multi-Agent Orchestrator") as demo:
    gr.Markdown(APP_DESCRIPTION)

    mission_box = gr.Textbox(
        label="Mission",
        value=DEFAULT_MISSION,
        lines=3,
    )

    with gr.Accordion("Approved Source Packet", open=True):
        market_box = gr.Textbox(
            label="market-brief — Synthetic Market Brief",
            value=DEFAULT_MARKET,
            lines=4,
        )
        operations_box = gr.Textbox(
            label="operations-brief — Synthetic Operations Brief",
            value=DEFAULT_OPERATIONS,
            lines=4,
        )
        competition_box = gr.Textbox(
            label="competition-brief — Synthetic Competition Brief",
            value=DEFAULT_COMPETITION,
            lines=4,
        )

    run_button = gr.Button("Run Multi-Agent Workflow", variant="primary")

    gr.Markdown("## Final Result")
    final_answer = gr.Markdown()

    with gr.Row():
        workflow_status = gr.Textbox(label="Workflow Status")
        workflow_error = gr.Textbox(label="Workflow Error / Routing Stop")

    with gr.Tabs():
        with gr.Tab("Research"):
            research_output = gr.JSON(label="ResearchResult")
        with gr.Tab("Analysis"):
            analysis_output = gr.JSON(label="AnalysisResult")
        with gr.Tab("Verification"):
            verification_output = gr.JSON(label="VerificationResult")
        with gr.Tab("Synthesis"):
            synthesis_output = gr.JSON(label="SynthesisResult")
        with gr.Tab("Audit History"):
            history_output = gr.JSON(label="OrchestratorState.history")

    run_button.click(
        fn=handle_request,
        inputs=[
            mission_box,
            market_box,
            operations_box,
            competition_box,
        ],
        outputs=[
            final_answer,
            workflow_status,
            workflow_error,
            research_output,
            analysis_output,
            verification_output,
            synthesis_output,
            history_output,
        ],
    )


if __name__ == "__main__":
    demo.launch()
