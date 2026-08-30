---
title: Centralized Multi-Agent Orchestrator
emoji: 🧭
colorFrom: indigo
colorTo: blue
sdk: gradio
sdk_version: 5.50.0
app_file: app.py
pinned: false
license: mit
---

# 08. Centralized Multi-Agent Orchestrator

A supervisor-agent system that coordinates specialized **Research**, **Analysis**, **Verification**, and **Synthesis** agents through one central workflow controller.

**Live Demo:** https://huggingface.co/spaces/FlyingNunchucks/08-centralized-multi-agent-orchestrator

## Goal

Build a multi-agent system in which a central orchestrator owns routing, shared state, handoffs, failure handling, and publication while specialist agents remain bounded to their assigned reasoning roles.

The core design principle is:

> **The orchestrator controls the workflow. Specialists control their assigned reasoning. Sources establish facts. Agents interpret. The orchestrator controls what gets published.**

## Why This Project

Adding more agents does not automatically create a reliable multi-agent system. Once several model-driven components collaborate, the system must answer engineering questions such as:

- Who decides which agent runs next?
- What information is allowed to cross each handoff?
- How is shared state synchronized?
- What happens when one agent fails or returns malformed output?
- How are unsupported interpretations prevented from becoming published facts?
- How can a reviewer reconstruct what happened after the request completes?

This project implements those controls explicitly in a centralized supervisor architecture.

## Architecture

```text
User Mission + Approved Source Packet
                |
                v
      Central Orchestrator
                |
                v
        Research Agent
                |
                v
        Analysis Agent
                |
                v
      Verification Agent
          |             |
          | pass        | needs_revision
          v             v
      Synthesis      Bounded Stop
        Agent        + Audit State
          |
          v
 Central Publication Boundary
          |
          v
       Final Result
```

### Specialist Responsibilities

| Component | Responsibility | Explicit Boundary |
| --- | --- | --- |
| **Research Agent** | Extract evidence from the approved source packet | No outside sources or invented source IDs |
| **Analysis Agent** | Interpret validated research and identify opportunities, risks, constraints, and uncertainties | Cannot perform new research or present assumptions as facts |
| **Verification Agent** | Audit each analysis point against research evidence | Does not control routing or publish the answer |
| **Synthesis Agent** | Select supported analysis IDs and provide confidence / draft synthesis | Free-form prose is not blindly published |
| **Central Orchestrator** | Own routing, state, stable handoff IDs, failure containment, and final rendering | Specialists cannot change the broader workflow |

## Structured Handoffs

Pydantic schemas define the contracts passed between agents. Important controls include:

- approved `source_id` validation;
- deterministic application-owned IDs such as `analysis-1` and `analysis-2`;
- one Verification audit per retained Analysis point;
- Synthesis selection only from Analysis IDs verified as `supported`;
- quarantine of Analysis points with empty or unapproved source IDs;
- narrow normalization for known safe Verification schema drift;
- auditable shared `OrchestratorState` and step history.

The system deliberately avoids using exact generated prose as the identity of an inter-agent handoff.

## Publication Boundary

A key production lesson from live testing was that a model-verified interpretation is still not the same thing as a literal source fact.

The user-facing Final Result therefore separates epistemic layers:

### Source-Backed Evidence
Rendered directly from the approved source packet.

### Orchestrator Assessment
Reports whether the specialist workflow passed verification cleanly or with cautions.

### Analytical Cautions
Shows interpretations that Verification did not fully support, explicitly labeled as analysis rather than evidence.

### Unresolved Questions
Combines evidence gaps identified by Research and Verification.

### Confidence
Comes from the Synthesis handoff.

This design prevents an Analysis phrase such as "competitors dominate" from being promoted into the factual section when the approved source merely says that competitors exist and compete on certain dimensions.

## Demo Scenario

The public Gradio demo uses a fictional **Acme Robotics** market-entry case with three editable synthetic briefs:

- `market-brief` — demand growth and customer interest in warehouse automation;
- `operations-brief` — two regional service teams and unresolved geographic scalability;
- `competition-brief` — two established competitors competing on implementation speed and post-sale service coverage.

The scenario is intentionally small and synthetic so a reviewer can compare every displayed source-backed fact with the original approved inputs.

The interface exposes the Final Result plus the individual Research, Analysis, Verification, Synthesis, and Audit History handoffs.

## Failure Handling and Resilience

The supervisor contains failures rather than allowing downstream agents to continue on invalid state.

Examples of controls implemented during live evaluation:

- specialist exceptions stop downstream execution and remain visible in workflow state;
- `needs_revision` from Verification stops the workflow before Synthesis;
- uncited Analysis points are quarantined rather than crashing an otherwise usable handoff;
- the known Verification alias `partial_supported` is safely normalized to `partially_supported`;
- recognized object-shaped correction text can be normalized before strict Pydantic validation;
- unknown source IDs, invalid handoff IDs, and unsupported Synthesis selections remain hard failures.

See [EVALUATION.md](EVALUATION.md) for the observed failure modes, root causes, regression tests, and lessons learned.

## Automated Evaluation

The test suite covers:

- Research grounding and source-ID validation;
- Analysis source boundaries and deterministic IDs;
- quarantine of uncited or unapproved-source Analysis points;
- Verification ID coverage and source constraints;
- safe Verification schema normalization;
- Synthesis selection boundaries;
- `needs_revision` routing;
- specialist failure containment;
- canonical final-answer rendering;
- runtime assembly and model-adapter behavior;
- Gradio application output exposure.

Run locally with:

```bash
python -m pytest -q
```

## Local Setup

Python 3.11 is used in CI.

```bash
git clone https://github.com/wushuchris/08-centralized-multi-agent-orchestrator.git
cd 08-centralized-multi-agent-orchestrator
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set your own Hugging Face inference token in the local `.env` file. Do not commit the real `.env` file.

Then run:

```bash
python app.py
```

The default runtime model is configurable through `MODEL_ID`. The repository currently defaults to:

```text
openai/gpt-oss-120b:cerebras
```

through the Hugging Face OpenAI-compatible router.

## Security and Data Safety

This public demo is built for **synthetic, public-safe inputs only**.

- No real credentials are stored in source control.
- `.env` is gitignored.
- `.env.example` contains placeholders only.
- The Hugging Face Space uses `HF_TOKEN` as its runtime inference secret.
- GitHub Actions uses the repository secret `HF_DEPLOY_TOKEN` only to sync GitHub to the Hugging Face Space.
- GitHub remains the source of truth for code.

Do not use the public demo for confidential, personal, client, financial, or proprietary source material.

## CI/CD

The repository uses a single **Tests and Deploy** GitHub Actions workflow:

```text
push to main
      |
      v
run pytest
      |
      | success
      v
sync repository to Hugging Face Space
      |
      v
Hugging Face rebuilds the Gradio app
```

Pull requests run tests but do not deploy.

The workflow uses a standard `ubuntu-latest` GitHub-hosted runner and keeps GitHub as the deployment source of truth.

## Technology

- Python 3.11
- Pydantic 2
- Gradio 5
- OpenAI-compatible Python client
- Hugging Face Inference Providers
- pytest
- GitHub Actions
- Hugging Face Spaces

## Repository Structure

```text
.
├── app.py
├── EVALUATION.md
├── requirements.txt
├── src/
│   ├── analysis_agent.py
│   ├── model_adapter.py
│   ├── orchestrator.py
│   ├── research_agent.py
│   ├── runtime.py
│   ├── schemas.py
│   ├── state.py
│   ├── synthesis_agent.py
│   └── verification_agent.py
└── tests/
    ├── test_analysis_agent.py
    ├── test_app.py
    ├── test_model_adapter.py
    ├── test_orchestrator.py
    ├── test_orchestrator_failures.py
    ├── test_research_agent.py
    ├── test_runtime.py
    ├── test_state.py
    ├── test_synthesis_agent.py
    └── test_verification_agent.py
```

## Production Upgrade Path

This baseline intentionally keeps Research limited to an approved synthetic packet so the project stays focused on orchestration rather than external integrations.

A production version could extend the same supervisor contract with:

- retrieval-backed Research over controlled knowledge sources;
- allowlisted tool execution;
- stronger deterministic evidence checks;
- capped Analysis → Verification revision loops;
- parallel specialist branches where tasks are independent;
- persistent workflow state and trace storage;
- latency, token, cost, and quality telemetry;
- model/provider fallback policies;
- human approval gates for high-impact actions.

## Reusable Agent Primitive

The reusable primitive demonstrated here is a **centralized supervisor boundary**:

```text
Central Orchestrator
= routing
+ shared state
+ stable handoff identity
+ validation
+ failure containment
+ publication control
```

Specialists remain replaceable. The orchestration contract stays stable.

## License

MIT License.