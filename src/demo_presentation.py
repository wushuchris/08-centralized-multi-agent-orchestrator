"""Business-first presentation helpers for the Agent 8 Gradio demo."""

from __future__ import annotations

import html

from .state import OrchestratorState


AGENT_LABELS = {
    "orchestrator": "Central Supervisor",
    "research": "Research Specialist",
    "analysis": "Strategy Analyst",
    "verification": "Evidence Verifier",
    "synthesis": "Executive Synthesizer",
}

AGENT_ICONS = {
    "orchestrator": "🧭",
    "research": "🔎",
    "analysis": "📈",
    "verification": "🛡️",
    "synthesis": "✍️",
}

ACTION_LABELS = {
    "start workflow": "Opened the supervised mission",
    "produce research handoff": "Built the source-grounded research handoff",
    "interpret research handoff": "Interpreted the research into opportunities, risks, and uncertainties",
    "audit analysis against research": "Checked each analysis point against the approved evidence",
    "route after verification": "Applied the verification gate",
    "produce final response": "Prepared the bounded synthesis handoff",
    "complete workflow": "Closed the supervised workflow",
    "execute assigned step": "Specialist execution failed",
    "fail workflow": "Stopped the workflow safely",
}

APP_CSS = """
.gradio-container { max-width:1080px !important; margin:0 auto !important; }
.agent-hero { padding:1.65rem 1.75rem; border:1px solid var(--border-color-primary,rgba(127,127,127,.24)); border-radius:22px; background:linear-gradient(135deg,rgba(79,70,229,.13),rgba(14,165,233,.08)); margin-bottom:1rem; }
.agent-eyebrow,.panel-eyebrow { font-size:.76rem; font-weight:850; letter-spacing:.12em; opacity:.72; margin-bottom:.35rem; }
.agent-hero h1 { margin:.2rem 0 .55rem; font-size:2.12rem; line-height:1.16; max-width:900px; }
.agent-hero p { margin:0; max-width:900px; font-size:1.06rem; line-height:1.58; }
.section-note { padding:.9rem 1rem; border-radius:13px; background:rgba(79,70,229,.07); border:1px solid rgba(79,70,229,.17); margin:.85rem 0; line-height:1.5; }
.supervisor-card { padding:1rem 1.1rem; border:1px solid rgba(79,70,229,.38); border-radius:15px; background:linear-gradient(135deg,rgba(79,70,229,.11),rgba(14,165,233,.05)); margin:.9rem 0 .7rem; }
.supervisor-card strong { font-size:1.05rem; display:block; margin-bottom:.25rem; }
.supervisor-card span { line-height:1.48; opacity:.82; }
.team-list { display:grid; grid-template-columns:1fr; gap:.62rem; margin:.7rem 0 1rem; }
.team-card { display:grid; grid-template-columns:42px minmax(0,1fr); gap:.75rem; padding:.85rem .95rem; border:1px solid var(--border-color-primary,rgba(127,127,127,.22)); border-radius:13px; background:var(--block-background-fill,rgba(127,127,127,.04)); }
.team-icon { font-size:1.35rem; line-height:1.3; text-align:center; }
.team-title { font-weight:800; font-size:1rem; margin-bottom:.15rem; }
.team-body { font-size:.94rem; opacity:.78; line-height:1.45; }
.flow-list { display:grid; grid-template-columns:1fr; gap:.48rem; margin:.9rem 0 1.15rem; }
.flow-step { padding:.78rem .9rem; border:1px solid var(--border-color-primary,rgba(127,127,127,.22)); border-radius:12px; background:var(--block-background-fill,rgba(127,127,127,.04)); }
.flow-step strong { display:block; margin-bottom:.18rem; }
.flow-step span { font-size:.92rem; opacity:.76; line-height:1.42; }
.flow-arrow { text-align:center; opacity:.45; font-weight:900; line-height:.8; }
.activity-card { border:1px solid rgba(79,70,229,.30); border-radius:18px; padding:17px 19px; margin:14px 0 18px; background:linear-gradient(135deg,rgba(79,70,229,.08),rgba(14,165,233,.035)); }
.activity-head { display:flex; align-items:center; gap:10px; margin-bottom:8px; }
.activity-spinner { width:24px; height:24px; box-sizing:border-box; border:4px solid rgba(79,70,229,.18); border-top-color:#4f46e5; border-right-color:#0ea5e9; border-radius:50%; animation:agent8-spin .78s linear infinite; flex:0 0 auto; }
.activity-badge { display:inline-block; border:1px solid rgba(79,70,229,.40); border-radius:999px; padding:4px 8px; font-size:.72rem; font-weight:850; letter-spacing:.09em; }
.activity-title { font-size:1.08rem; font-weight:800; }
.activity-sub { font-size:.92rem; opacity:.79; line-height:1.42; margin-bottom:10px; }
.activity-track { height:8px; background:rgba(148,163,184,.18); border-radius:999px; overflow:hidden; margin:10px 0 13px; }
.activity-fill { height:100%; background:linear-gradient(90deg,#4f46e5,#0ea5e9); transition:width .2s ease; }
.activity-feed { display:grid; gap:6px; }
.activity-feed.activity-scroll { max-height:390px; overflow-y:auto; padding-right:7px; scrollbar-gutter:stable; }
.activity-event { display:grid; grid-template-columns:32px minmax(0,1fr); gap:8px; padding-top:8px; border-top:1px solid rgba(148,163,184,.16); }
.activity-event:first-child { border-top:0; padding-top:0; }
.activity-icon { font-size:1rem; text-align:center; }
.activity-main { font-size:.94rem; line-height:1.42; }
.activity-main strong { font-weight:800; }
.activity-meta { font-size:.79rem; opacity:.66; margin-top:2px; }
.activity-complete { border-color:rgba(34,197,94,.35); background:linear-gradient(135deg,rgba(34,197,94,.08),rgba(14,165,233,.035)); }
.activity-failed { border-color:rgba(239,68,68,.35); background:linear-gradient(135deg,rgba(239,68,68,.07),rgba(79,70,229,.03)); }
.outcome-card,.boundary-card,.work-card { border-radius:16px; padding:1rem 1.1rem; border:1px solid var(--border-color-primary,rgba(127,127,127,.24)); margin:.8rem 0; background:var(--block-background-fill,rgba(127,127,127,.04)); }
.outcome-success { border-left:6px solid #22c55e; background:rgba(34,197,94,.07); }
.outcome-stop { border-left:6px solid #f59e0b; background:rgba(245,158,11,.07); }
.outcome-failed { border-left:6px solid #ef4444; background:rgba(239,68,68,.06); }
.panel-title { font-size:1.18rem; font-weight:820; margin-bottom:.35rem; }
.panel-body { line-height:1.5; margin-bottom:.45rem; }
.outcome-takeaway { font-weight:700; opacity:.84; }
.metric-row { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:.55rem; margin:.75rem 0; }
.metric { padding:.7rem .75rem; border-radius:11px; background:rgba(100,116,139,.08); border:1px solid rgba(100,116,139,.14); }
.metric strong { display:block; font-size:1.05rem; }
.metric span { font-size:.78rem; opacity:.68; }
.work-stack { display:grid; grid-template-columns:1fr; gap:.65rem; }
.work-card h3 { margin:.1rem 0 .45rem; font-size:1.02rem; }
.work-card ul { margin:.35rem 0 .1rem 1.15rem; }
.work-card li { margin:.35rem 0; line-height:1.42; }
.work-note { font-size:.84rem; opacity:.7; margin-top:.5rem; }
.verdict { display:inline-block; border-radius:999px; padding:.18rem .45rem; margin-left:.3rem; font-size:.72rem; font-weight:800; background:rgba(79,70,229,.10); }
.arch-grid { display:grid; grid-template-columns:1fr 1fr; gap:.7rem; margin:.8rem 0; }
.arch-card { padding:.9rem 1rem; border:1px solid var(--border-color-primary,rgba(127,127,127,.22)); border-radius:13px; background:var(--block-background-fill,rgba(127,127,127,.04)); }
.arch-card strong { display:block; margin-bottom:.3rem; }
.arch-card span { line-height:1.45; opacity:.78; }
@keyframes agent8-spin { to { transform:rotate(360deg); } }
@media (max-width:760px) { .gradio-container { max-width:100% !important; } .agent-hero { padding:1.3rem 1.1rem; } .agent-hero h1 { font-size:1.72rem; } .metric-row,.arch-grid { grid-template-columns:1fr; } }
"""

HERO_HTML = """
<div class="agent-hero">
  <div class="agent-eyebrow">AGENT 8 • CENTRALIZED MULTI-AGENT ORCHESTRATION • SYNTHETIC DEMO</div>
  <h1>When four AI specialists advise on one decision, who keeps the team aligned?</h1>
  <p>A fictional executive team is evaluating whether Acme Robotics should enter a new market. Four bounded AI specialists contribute research, analysis, verification, and synthesis—but a central supervisor owns the workflow, evidence boundaries, routing, failure containment, and publication.</p>
</div>
"""

TEAM_HTML = """
<div class="supervisor-card"><strong>🧭 Central Supervisor — owns the process</strong><span>Controls sequence, shared state, stable handoff IDs, verification routing, failure containment, and the final publication boundary. Specialist agents cannot change the broader workflow.</span></div>
<div class="team-list">
  <div class="team-card"><div class="team-icon">🔎</div><div><div class="team-title">Research Specialist</div><div class="team-body">Extracts evidence only from the approved synthetic source packet. It cannot browse elsewhere or invent source IDs.</div></div></div>
  <div class="team-card"><div class="team-icon">📈</div><div><div class="team-title">Strategy Analyst</div><div class="team-body">Interprets validated research into opportunities, risks, constraints, and uncertainties. It cannot perform new research or promote assumptions into facts.</div></div></div>
  <div class="team-card"><div class="team-icon">🛡️</div><div><div class="team-title">Evidence Verifier</div><div class="team-body">Audits each application-owned analysis ID against the research handoff. A needs-revision result stops the workflow before synthesis.</div></div></div>
  <div class="team-card"><div class="team-icon">✍️</div><div><div class="team-title">Executive Synthesizer</div><div class="team-body">Selects only supported analysis IDs and prepares a bounded synthesis draft. Its free-form prose is not automatically published.</div></div></div>
</div>
<div class="section-note"><strong>The control model:</strong> Sources establish facts. Specialists interpret within bounded roles. The supervisor decides what may run next and what may be published.</div>
"""

FLOW_HTML = """
<div class="flow-list">
  <div class="flow-step"><strong>1 · Approved evidence enters the system</strong><span>Three editable synthetic briefs establish the only facts the Research Specialist may use.</span></div><div class="flow-arrow">↓</div>
  <div class="flow-step"><strong>2 · Research creates a grounded handoff</strong><span>Evidence-linked findings and open questions move to Analysis through a typed contract.</span></div><div class="flow-arrow">↓</div>
  <div class="flow-step"><strong>3 · Analysis interprets—not researches</strong><span>Application-owned analysis IDs keep the handoff stable even when model wording changes.</span></div><div class="flow-arrow">↓</div>
  <div class="flow-step"><strong>4 · Verification becomes a routing gate</strong><span>Supported work may continue. A needs-revision result stops downstream synthesis.</span></div><div class="flow-arrow">↓</div>
  <div class="flow-step"><strong>5 · Synthesis drafts; the supervisor publishes</strong><span>The supervisor renders source facts separately from analysis and unresolved questions.</span></div>
</div>
"""

ARCHITECTURE_HTML = """
<div class="arch-grid">
  <div class="arch-card"><strong>Why centralize?</strong><span>One supervisor gives the business a single place to enforce sequence, state, handoff rules, verification gates, and publication policy.</span></div>
  <div class="arch-card"><strong>What does centralization cost?</strong><span>The supervisor is a coordination bottleneck and single control point. Later portfolio agents explore peer-to-peer and distributed alternatives.</span></div>
  <div class="arch-card"><strong>What does the model control?</strong><span>Specialist reasoning inside typed roles and bounded structured outputs.</span></div>
  <div class="arch-card"><strong>What does application code control?</strong><span>Routing, identity, source allowlists, validation, failure containment, and final publication.</span></div>
</div>
"""

EMPTY_ACTIVITY_HTML = """<div class="activity-card"><div class="activity-title">Live supervisor activity</div><div class="activity-sub">Run the supervised market-entry review to watch real orchestrator state changes appear here as each specialist starts and finishes.</div></div>"""
EMPTY_OUTCOME_HTML = """<div class="outcome-card"><div class="panel-eyebrow">READY TO RUN</div><div class="panel-title">The supervised decision team is waiting</div><div class="panel-body">Run the default synthetic case to see how the supervisor coordinates four specialists and protects the publication boundary.</div></div>"""
EMPTY_BOUNDARY_HTML = """<div class="boundary-card"><div class="panel-eyebrow">PUBLICATION BOUNDARY</div><div class="panel-title">Nothing has been cleared for publication yet</div><div class="panel-body">Research, analysis, verification, and synthesis evidence will appear here after a run.</div></div>"""
EMPTY_WORK_HTML = """<div class="work-card"><div class="panel-eyebrow">SPECIALIST WORK PRODUCTS</div><div class="panel-title">Waiting for the team</div><div class="panel-body">Readable specialist handoffs will appear here. Raw JSON remains available in the engineering audit tab.</div></div>"""


def _escape(value: object) -> str:
    return html.escape(str(value))


def activity_html(state: OrchestratorState, *, complete: bool | None = None) -> str:
    if complete is None:
        complete = state.status in {"completed", "failed"}

    total_expected = 11
    progress = 100 if complete else min(96, max(6, int(len(state.history) / total_expected * 100)))
    rows = state.history if complete else state.history[-8:]
    last = state.history[-1] if state.history else None

    if complete and state.status == "completed":
        badge, title, card_class, spinner = "COMPLETE", "Supervisor workflow complete", "activity-card activity-complete", ""
        sub = f"{len(state.history)} real supervisor events retained. Scroll inside the transcript to review the complete coordination trace."
        feed_class = "activity-feed activity-scroll"
    elif complete:
        badge, title, card_class, spinner = "STOPPED", "Supervisor stopped the workflow", "activity-card activity-failed", ""
        sub = state.error or "The supervisor contained a failure before unsafe downstream work continued."
        feed_class = "activity-feed activity-scroll"
    else:
        badge, title, card_class = "RUNNING", "Central supervisor is coordinating the team", "activity-card"
        spinner = '<span class="activity-spinner"></span>'
        if last is None:
            sub = "Preparing the supervised workflow."
        else:
            sub = f"{AGENT_LABELS[last.agent]} · {ACTION_LABELS.get(last.action, last.action)} · {last.status}"
        feed_class = "activity-feed"

    feed_rows = []
    for index, step in enumerate(rows, start=max(1, len(state.history) - len(rows) + 1)):
        label = AGENT_LABELS.get(step.agent, step.agent.title())
        action = ACTION_LABELS.get(step.action, step.action)
        note = f" · {_escape(step.note)}" if step.note else ""
        feed_rows.append(
            f'<div class="activity-event"><div class="activity-icon">{AGENT_ICONS.get(step.agent, "•")}</div><div class="activity-main"><strong>{_escape(label)}</strong><br>{_escape(action)}<div class="activity-meta">Event {index} · {_escape(step.status)}{note}</div></div></div>'
        )
    feed = "".join(feed_rows) or '<div class="activity-event"><div class="activity-icon">…</div><div class="activity-main">Waiting for the first supervisor event.</div></div>'

    return (
        f'<div class="{card_class}"><div class="activity-head">{spinner}<span class="activity-badge">{badge}</span><span class="activity-title">{_escape(title)}</span></div>'
        f'<div class="activity-sub">{_escape(sub)}</div><div class="activity-track"><div class="activity-fill" style="width:{progress}%"></div></div>'
        f'<div class="{feed_class}">{feed}</div></div>'
    )


def business_outcome_html(state: OrchestratorState) -> str:
    if state.status == "completed":
        verification = state.verification_result.overall_status if state.verification_result else "unknown"
        confidence = state.synthesis_result.confidence if state.synthesis_result else "unknown"
        caution_text = "with cautions" if verification == "pass_with_cautions" else "cleanly"
        return (
            '<div class="outcome-card outcome-success"><div class="panel-eyebrow">BUSINESS OUTCOME</div>'
            '<div class="panel-title">The decision-support packet cleared the publication gate</div>'
            f'<div class="panel-body">Research, analysis, and verification completed {caution_text}. The supervisor allowed synthesis and rendered the final result from controlled upstream state.</div>'
            f'<div class="outcome-takeaway">Verification: {_escape(verification)} · Synthesis confidence: {_escape(confidence)}</div></div>'
        )

    if state.verification_result and state.verification_result.overall_status == "needs_revision":
        return (
            '<div class="outcome-card outcome-stop"><div class="panel-eyebrow">BUSINESS OUTCOME</div>'
            '<div class="panel-title">The supervisor stopped before publication</div>'
            '<div class="panel-body">Verification found analysis that requires revision. The central controller prevented Synthesis from running rather than publishing questionable work.</div>'
            '<div class="outcome-takeaway">This is a successful control outcome even though the workflow did not publish a result.</div></div>'
        )

    if state.status == "failed":
        return (
            '<div class="outcome-card outcome-failed"><div class="panel-eyebrow">BUSINESS OUTCOME</div>'
            '<div class="panel-title">The workflow failed closed</div>'
            f'<div class="panel-body">{_escape(state.error or "A specialist failed and downstream work was contained.")}</div>'
            '<div class="outcome-takeaway">The supervisor preserved an auditable failure state instead of continuing on invalid inputs.</div></div>'
        )

    return EMPTY_OUTCOME_HTML


def publication_boundary_html(state: OrchestratorState) -> str:
    research_count = len(state.research_result.findings) if state.research_result else 0
    analysis_count = len(state.analysis_result.points) if state.analysis_result else 0
    verification_count = len(state.verification_result.checks) if state.verification_result else 0
    supported_count = (
        sum(1 for check in state.verification_result.checks if check.verdict == "supported")
        if state.verification_result
        else 0
    )
    omitted_count = len(state.analysis_result.omitted_points) if state.analysis_result else 0
    verification_status = state.verification_result.overall_status if state.verification_result else "pending"

    return (
        '<div class="boundary-card"><div class="panel-eyebrow">PUBLICATION BOUNDARY</div>'
        '<div class="panel-title">The supervisor keeps facts, interpretations, and publication separate</div>'
        '<div class="metric-row">'
        f'<div class="metric"><strong>{research_count}</strong><span>research findings</span></div>'
        f'<div class="metric"><strong>{analysis_count}</strong><span>analysis points</span></div>'
        f'<div class="metric"><strong>{supported_count}/{verification_count}</strong><span>fully supported checks</span></div>'
        f'<div class="metric"><strong>{omitted_count}</strong><span>quarantined analysis items</span></div>'
        '</div>'
        f'<div class="panel-body">Verification status: <strong>{_escape(verification_status)}</strong>. Source-backed facts are rendered from the approved source packet; model interpretations remain labeled as analysis or cautions.</div></div>'
    )


def work_products_html(state: OrchestratorState) -> str:
    cards: list[str] = []

    if state.research_result:
        findings = "".join(
            f'<li><strong>{_escape(item.claim)}</strong><br>{_escape(item.evidence)} <span class="verdict">sources: {_escape(", ".join(item.source_ids))}</span></li>'
            for item in state.research_result.findings
        )
        cards.append(
            '<div class="work-card"><div class="panel-eyebrow">🔎 RESEARCH HANDOFF</div><h3>Evidence extracted from approved sources</h3>'
            f'<div>{_escape(state.research_result.summary)}</div><ul>{findings}</ul></div>'
        )

    if state.analysis_result:
        points = "".join(
            f'<li><strong>{_escape(item.point_id or "unassigned")} · {_escape(item.kind)}</strong> — {_escape(item.statement)}<br><span class="work-note">{_escape(item.reasoning)}</span></li>'
            for item in state.analysis_result.points
        )
        omitted = ""
        if state.analysis_result.omitted_points:
            omitted = f'<div class="work-note"><strong>Quarantined:</strong> {_escape(" | ".join(state.analysis_result.omitted_points))}</div>'
        cards.append(
            '<div class="work-card"><div class="panel-eyebrow">📈 ANALYSIS HANDOFF</div><h3>Interpretations linked to stable application-owned IDs</h3>'
            f'<div>{_escape(state.analysis_result.assessment)}</div><ul>{points}</ul>{omitted}</div>'
        )

    if state.verification_result:
        checks = "".join(
            f'<li><strong>{_escape(item.analysis_point_id)}</strong><span class="verdict">{_escape(item.verdict)}</span><br>{_escape(item.reasoning)}</li>'
            for item in state.verification_result.checks
        )
        cards.append(
            '<div class="work-card"><div class="panel-eyebrow">🛡️ VERIFICATION HANDOFF</div><h3>Evidence audit and routing gate</h3>'
            f'<div>Overall status: <strong>{_escape(state.verification_result.overall_status)}</strong></div><ul>{checks}</ul></div>'
        )

    if state.synthesis_result:
        selected = ", ".join(point.analysis_point_id for point in state.synthesis_result.key_points) or "none"
        cards.append(
            '<div class="work-card"><div class="panel-eyebrow">✍️ SYNTHESIS HANDOFF</div><h3>Bounded executive draft</h3>'
            f'<div>{_escape(state.synthesis_result.response)}</div><div class="work-note"><strong>Selected verified IDs:</strong> {_escape(selected)} · <strong>confidence:</strong> {_escape(state.synthesis_result.confidence)}</div>'
            '<div class="work-note">The supervisor does not publish this free-form draft verbatim. Final publication is rendered from controlled structured state.</div></div>'
        )

    if not cards:
        return EMPTY_WORK_HTML
    return f'<div class="work-stack">{"".join(cards)}</div>'
