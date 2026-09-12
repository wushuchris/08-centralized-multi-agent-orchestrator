"""Business-first Gradio demo for the centralized multi-agent orchestrator."""

from __future__ import annotations

import gradio as gr

from src.demo_presentation import (
    APP_CSS,
    ARCHITECTURE_HTML,
    EMPTY_ACTIVITY_HTML,
    EMPTY_BOUNDARY_HTML,
    EMPTY_OUTCOME_HTML,
    EMPTY_WORK_HTML,
    FLOW_HTML,
    HERO_HTML,
    TEAM_HTML,
    activity_html,
    business_outcome_html,
    publication_boundary_html,
    work_products_html,
)
from src.runtime import build_orchestrator
from src.schemas import ResearchSource
from src.state import OrchestratorState


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


UI_OUTPUT_COUNT = 12


def _dump(result):
    """Convert an optional Pydantic result into JSON-friendly data."""

    if result is None:
        return None
    return result.model_dump(mode="json")


def _build_sources(
    market_source: str,
    operations_source: str,
    competition_source: str,
) -> list[ResearchSource]:
    source_specs = [
        ("market-brief", "Synthetic Market Brief", market_source),
        ("operations-brief", "Synthetic Operations Brief", operations_source),
        ("competition-brief", "Synthetic Competition Brief", competition_source),
    ]
    return [
        ResearchSource(
            source_id=source_id,
            title=title,
            content=content.strip(),
        )
        for source_id, title, content in source_specs
        if content and content.strip()
    ]


def _technical_bundle(state: OrchestratorState):
    history = [step.model_dump(mode="json") for step in state.history]
    return (
        state.status,
        state.error or "",
        _dump(state.research_result),
        _dump(state.analysis_result),
        _dump(state.verification_result),
        _dump(state.synthesis_result),
        history,
    )


def _ui_bundle(state: OrchestratorState):
    complete = state.status in {"completed", "failed"}
    final_answer = state.final_answer or (
        "The supervisor has not published a final result. Review the business outcome, "
        "verification state, and engineering audit below."
    )
    return (
        activity_html(state, complete=complete),
        business_outcome_html(state),
        final_answer,
        publication_boundary_html(state),
        work_products_html(state),
        *_technical_bundle(state),
    )


def _empty_ui_bundle(message: str):
    return (
        EMPTY_ACTIVITY_HTML,
        f'<div class="outcome-card outcome-failed"><div class="panel-eyebrow">INPUT CHECK</div><div class="panel-title">Unable to start the supervised review</div><div class="panel-body">{message}</div></div>',
        "No final result was published.",
        EMPTY_BOUNDARY_HTML,
        EMPTY_WORK_HTML,
        "failed",
        message,
        None,
        None,
        None,
        None,
        [],
    )


def handle_request(
    mission: str,
    market_source: str,
    operations_source: str,
    competition_source: str,
):
    """Run once and preserve the original programmatic output contract."""

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

    sources = _build_sources(market_source, operations_source, competition_source)
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
    status, error, research, analysis, verification, synthesis, history = _technical_bundle(state)
    return (
        final_answer,
        status,
        error,
        research,
        analysis,
        verification,
        synthesis,
        history,
    )


def stream_request_ui(
    mission: str,
    market_source: str,
    operations_source: str,
    competition_source: str,
):
    """Stream real supervisor state snapshots into the public demo."""

    if not mission or not mission.strip():
        yield _empty_ui_bundle("Mission must not be empty.")
        return

    sources = _build_sources(market_source, operations_source, competition_source)
    if not sources:
        yield _empty_ui_bundle("At least one approved synthetic source is required.")
        return

    for state in ORCHESTRATOR.run_iter(
        mission=mission.strip(),
        sources=sources,
    ):
        yield _ui_bundle(state)


def build_app() -> gr.Blocks:
    """Construct the public supervised multi-agent business demo."""

    with gr.Blocks(
        title="Agent 8 — Supervised AI Decision Team",
        css=APP_CSS,
    ) as demo:
        gr.HTML(HERO_HTML)

        gr.Markdown("## Meet the supervised AI team")
        gr.HTML(TEAM_HTML)

        with gr.Accordion("How the decision moves through the team", open=True):
            gr.HTML(FLOW_HTML)

        gr.Markdown("## Run the fictional market-entry review")
        gr.Markdown(
            "The default case is intentionally small enough to audit by eye. The supervisor will expose each real stage transition while four bounded specialists work from the same approved source packet."
        )

        mission_box = gr.Textbox(
            label="Executive question",
            value=DEFAULT_MISSION,
            lines=3,
        )

        with gr.Accordion("Approved synthetic evidence packet — 3 briefs", open=False):
            gr.Markdown(
                "Research may use only these sources. Editing the packet is allowed because the public demo is synthetic; outside retrieval is not part of Agent 8."
            )
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

        run_button = gr.Button("Run supervised market-entry review", variant="primary")

        activity = gr.HTML(EMPTY_ACTIVITY_HTML)
        business_outcome = gr.HTML(EMPTY_OUTCOME_HTML)

        gr.Markdown("## Published decision-support result")
        final_answer = gr.Markdown(
            "Run the supervised review to see what the central publication boundary allows through."
        )
        publication_boundary = gr.HTML(EMPTY_BOUNDARY_HTML)

        with gr.Tabs():
            with gr.Tab("Specialist Work Products"):
                gr.Markdown(
                    "### What each specialist contributed\nThese are readable views of the same typed handoffs used by the supervisor."
                )
                work_products = gr.HTML(EMPTY_WORK_HTML)

            with gr.Tab("Engineering Audit"):
                gr.Markdown(
                    "### Exact machine-readable state\nThe business story above is derived from these structured handoffs and the real supervisor history."
                )
                with gr.Row():
                    workflow_status = gr.Textbox(label="Workflow Status", interactive=False)
                    workflow_error = gr.Textbox(label="Workflow Error / Routing Stop", interactive=False)
                with gr.Accordion("ResearchResult", open=False):
                    research_output = gr.JSON(label="Research handoff")
                with gr.Accordion("AnalysisResult", open=False):
                    analysis_output = gr.JSON(label="Analysis handoff")
                with gr.Accordion("VerificationResult", open=False):
                    verification_output = gr.JSON(label="Verification handoff")
                with gr.Accordion("SynthesisResult", open=False):
                    synthesis_output = gr.JSON(label="Synthesis handoff")
                with gr.Accordion("OrchestratorState.history", open=True):
                    history_output = gr.JSON(label="Supervisor audit history")

            with gr.Tab("Architecture & Failure Modes"):
                gr.Markdown("### Why this agent uses a central supervisor")
                gr.HTML(ARCHITECTURE_HTML)
                gr.Markdown(
                    """
### What happens when something goes wrong

- A specialist exception stops downstream execution and remains visible in shared state.
- Verification is a routing gate: `needs_revision` stops the workflow before Synthesis.
- Uncited or unapproved Analysis items can be quarantined instead of crashing an otherwise usable handoff.
- Known safe schema drift is normalized narrowly; unknown IDs or unsupported selections still fail.
- The Synthesis model's free-form draft is **not** the authoritative published answer. The supervisor renders the final result from controlled structured state.

This centralized design is intentionally different from Agents 10 and 11: here, one supervisor owns coordination. Later agents explore what changes when coordination becomes peer-to-peer or distributed.
"""
                )

        outputs = [
            activity,
            business_outcome,
            final_answer,
            publication_boundary,
            work_products,
            workflow_status,
            workflow_error,
            research_output,
            analysis_output,
            verification_output,
            synthesis_output,
            history_output,
        ]

        run_button.click(
            fn=stream_request_ui,
            inputs=[
                mission_box,
                market_box,
                operations_box,
                competition_box,
            ],
            outputs=outputs,
            show_progress="hidden",
        )

    demo.queue()
    return demo


demo = build_app()


if __name__ == "__main__":
    demo.launch()
