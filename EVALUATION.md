# Evaluation and Failure Analysis

This document records the evaluation strategy, observed failure modes, and hardening decisions for the Centralized Multi-Agent Orchestrator.

The goal of the evaluation is not only to confirm that the happy path works. It is to test whether the central supervisor keeps specialist behavior bounded, preserves evidence boundaries, contains failures, and leaves an auditable state when something goes wrong.

## Evaluation Goals

The system is evaluated against five core properties:

1. **Centralized control** — the orchestrator owns routing, sequence, shared state, completion, and failure handling.
2. **Bounded specialization** — Research, Analysis, Verification, and Synthesis operate only within their assigned roles.
3. **Grounding** — source-backed facts remain distinguishable from model interpretation.
4. **Resilience** — predictable LLM formatting drift does not unnecessarily crash an otherwise usable workflow.
5. **Auditability** — intermediate handoffs, routing decisions, omitted items, verification judgments, and workflow history remain inspectable.

## Test Coverage

The automated suite covers the following behaviors:

| Area | What is tested |
| --- | --- |
| Research | Structured research handoff, approved source IDs, evidence-linked findings |
| Analysis | Research-only reasoning, source validation, deterministic analysis IDs, quarantine of uncited or unapproved-source points |
| Verification | One audit per stable analysis ID, source-bound verification, verdict handling, safe schema normalization |
| Synthesis | Selection only from analysis IDs verified as supported, rejection of non-supported selections |
| Orchestration | Ordered routing, revision stop before synthesis, canonical final rendering, auditable history |
| Failure containment | A specialist exception stops downstream agents and leaves an inspectable failed state |
| Runtime | Shared model adapter construction without requiring live inference during tests |
| Application | Gradio handler exposes final answer, specialist handoffs, workflow status, error state, and audit history |

CI runs the test suite on every push and pull request. A push to `main` deploys to Hugging Face only after the test job succeeds.

## Live Evaluation Scenario

The public demo uses a fictional Acme Robotics market-entry scenario with three editable synthetic sources:

- `market-brief` — demand growth and customer interest in warehouse automation.
- `operations-brief` — two regional service teams and unresolved geographic scalability.
- `competition-brief` — two established competitors competing on implementation speed and post-sale service coverage.

The scenario is intentionally small enough for a human reviewer to compare the final result against every approved fact.

## Failure Analysis

### 1. Unsupported synthesis embellishment

**Observed behavior**

An early live run produced conclusions such as a competitive "speed gap" that were not established by the approved source packet.

**Root cause**

The orchestrator published the Synthesis Agent's free-form `response` directly. Structured fields were validated, but free-form prose could still add unsupported claims.

**Control added**

The model's free-form response became an audit draft rather than the authoritative published answer. The orchestrator now controls final rendering from structured upstream state.

**Lesson**

Validation of structured fields is not sufficient when an unchecked free-form field is still the user-facing output.

---

### 2. Brittle exact-text handoff validation

**Observed behavior**

Verification was initially required to reproduce Analysis statements character-for-character. A semantically harmless wording change could cause the workflow to fail.

**Root cause**

Agent handoff identity was coupled to generated prose.

**Control added**

Application code now assigns deterministic IDs such as `analysis-1`, `analysis-2`, and `analysis-3`. Verification audits those IDs, and Synthesis selects only IDs verified as supported.

**Lesson**

Stable machine-owned identifiers are safer handoff contracts than exact LLM-generated text matching.

---

### 3. Uncited analysis points caused whole-workflow failure

**Observed behavior**

A live Analysis response included valid evidence-linked points plus additional points whose `source_ids` arrays were empty. Strict Pydantic validation rejected the entire `AnalysisResult`.

**Root cause**

The system treated every malformed model item as fatal, even when other analysis points were usable.

**Control added**

The Analysis Agent now performs bounded normalization before final schema validation:

- points with at least one approved source ID are retained;
- points with empty or unapproved source IDs are quarantined in `omitted_points`;
- if no evidence-linked points remain, the handoff still fails.

**Lesson**

A production agent should distinguish a recoverable bad item from a fatal bad handoff.

---

### 4. Verification schema drift

**Observed behavior**

A live Verification response returned `partial_supported` instead of `partially_supported` and returned a correction as an object instead of a plain string.

**Root cause**

The model followed the intended semantics but drifted slightly from the exact response schema.

**Control added**

A conservative normalization layer now repairs only known safe variations before Pydantic validation:

- `partial_supported` is normalized to `partially_supported`;
- correction objects are converted to strings only when a recognized textual field is present;
- all remaining content must still pass the strict schema and ID/source validation.

**Lesson**

Schema normalization should be explicit and narrow. It should repair predictable formatting drift without turning validation into permissive parsing.

---

### 5. Analysis interpretation was being presented as source fact

**Observed behavior**

A later successful run still presented interpretations such as competitors "dominating" or service capacity being "insufficient" under an evidence-backed conclusions heading.

**Root cause**

Even after Verification, the final renderer still promoted validated Analysis prose into the factual section. Verification can judge an interpretation, but it cannot convert an inference into a literal source fact.

**Control added**

The final answer now separates epistemic layers:

- **Source-Backed Evidence** is rendered directly from the approved source packet.
- **Orchestrator Assessment** reports workflow-level verification status.
- **Analytical Cautions** are explicitly labeled as interpretations and include Verification reasoning.
- **Unresolved Questions** combine Research and Verification gaps without presenting them as facts.
- **Confidence** comes from the Synthesis handoff.

**Lesson**

Sources establish facts. Agents interpret. The orchestrator controls what gets published.

## Current Behavioral Result

The final live smoke test completed successfully and produced a final result whose source-backed section stayed within the three approved synthetic briefs. Unresolved questions remained clearly separated from evidence, and no unsupported dominance, product-fit, or proven-capacity claims were promoted into the factual section.

## Failure Containment

The orchestrator catches specialist exceptions and records the active failure in shared state. Downstream specialists are not called after an upstream failure.

Verification also acts as a routing gate. If it returns `needs_revision`, the supervisor stops before Synthesis and records the routing decision instead of allowing a questionable result to continue to publication.

The current baseline treats `needs_revision` as a bounded stop. A later production version could add a capped Analysis → Verification revision loop.

## Security and Data-Safety Evaluation

The public demo uses synthetic data only. It is not designed for confidential, personal, client, financial, or proprietary source material.

Runtime inference credentials are supplied through the Hugging Face Space secret `HF_TOKEN`. GitHub-to-Hugging-Face deployment uses the GitHub repository secret `HF_DEPLOY_TOKEN`. Secret values are never stored in source files, and `.env` is excluded from version control.

## Known Limitations

- The baseline uses synthetic user-supplied text rather than live retrieval or web research.
- Semantic verification is still model-based; deterministic controls govern handoffs and publication boundaries but do not make the underlying model infallible.
- The workflow is centralized and sequential rather than parallel or decentralized.
- `needs_revision` currently stops the workflow instead of executing an automatic bounded revision cycle.
- Live execution can require up to four model-provider calls for a completed Research → Analysis → Verification → Synthesis run.
- Hugging Face Inference Provider usage may be subject to the account's current credits, quotas, and provider pricing.

## Production Upgrade Path

A production version could extend the same supervisor contract with:

- retrieval-backed Research using a controlled knowledge source;
- tool execution through an explicit allowlisted tool router;
- richer deterministic evidence checks;
- capped revision loops after Verification;
- parallel specialist branches where tasks are independent;
- persistent workflow state and trace storage;
- latency, token, cost, and quality telemetry;
- model/provider fallback policies;
- human approval gates for high-impact actions.

The key reusable primitive is the central control boundary: specialist agents can reason within their roles, while the orchestrator owns routing, shared state, handoff validation, failure containment, and publication.