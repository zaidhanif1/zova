# Zova

> Archived starter snapshot. For implemented functionality and current commands,
> see the [project README](../README.md).

**A personalized, constraint-aware AI travel assistant — planned project, currently in bootstrap.**

Zova will explore how to build travel agents that use tools, make explainable recommendations, respect a user's actual constraints, and safely revise a plan when circumstances change.

> **Status:** Initial project plan. No application code or live travel integrations have been implemented yet. Examples in the design document are synthetic and illustrative.

## What we're building

The project investigates a central engineering question:

**Can an AI agent plan and adapt travel recommendations around real constraints while keeping factual checks, permissions, and consequential decisions under deterministic application control?**

Three possible independently demonstrable MVPs are detailed in [the project blueprint](docs/PROJECT_BLUEPRINT.md):

| MVP | User value | Engineering focus | Status |
| --- | --- | --- | --- |
| **A — Personalized Weekend Planner** | Tailored itinerary + revisions | Preferences, constraint-aware scheduling, tool use | **Selected first; not yet implemented** |
| **B — Inbox-to-Itinerary Organizer** | Booking timeline + conflict detection | Extraction, cross-source reconciliation, privacy | Planned |
| **C — Disruption Recovery Copilot** | Comparison of recovery options when plans change | Agent loops, tradeoffs, approval, evaluations | Planned |

## Planned user experience (MVP A)

Example *synthetic* request:

> "Plan a Saturday in NYC for under $100. I like thrift stores and architecture, have a 2–4 PM meeting, and prefer walking/transit."

Expected capabilities once implemented:

1. Interpret preferences and fixed constraints.
2. Retrieve activities and estimated route times from a fixture provider.
3. Generate a feasible, costed itinerary.
4. Explain why each stop was chosen and what assumptions were used.
5. Replan when the user changes a preference or budget, preserving commitments.

## Getting started

**Not available yet:** This starter bundle intentionally contains only planning and contribution documents, not runnable code. Codex's initial task is to scaffold the project and replace this paragraph with **actual tested commands**.

Proposed stack: Python 3.12+, FastAPI/Pydantic, SQLite, pytest, ruff, a lightweight user interface after the core CLI works, and a model tool-calling adapter once deterministic planning is tested.

## Architecture approach

```text
User -> Request parser / agent -> authorized tool adapters (fixture first)
                            -> deterministic itinerary planner
                            -> validated recommendation + explanations
                            -> optional saved draft / approval state
```

- **Agent:** understand natural-language requests, select permitted tools, and explain tradeoffs.
- **Planner:** enforce budgets, schedules, travel-time buffers, exclusions, and validity.
- **Policy layer:** verify permissions and limit actions independently of the model.
- **Evaluation suite:** reproduce errors and measure correctness without requiring live paid APIs.

## Developer / Codex workflow

Start with [`AGENTS.md`](AGENTS.md) for durable development conventions and [`docs/PROJECT_BLUEPRINT.md`](docs/PROJECT_BLUEPRINT.md) for requirements, issue IDs, data contracts, sample scenarios, testing criteria, and the first Codex prompt.

Before each change: inspect Git state, choose one small acceptance-tested task, build it, test it, update documentation if behavior changes, and make a focused commit if authorized.

## Privacy, data, and limitations

- Initial examples, locations, confirmations, costs, and disruptions are **synthetic or estimated**.
- No actual travel availability, reservation, booking, cancellation, or purchase support is claimed.
- No real Gmail, Calendar, banking, or personal account data is part of this starter.
- A future real integration requires least-privilege credentials, permission enforcement, source-freshness metadata, redacted logs, and tested denial paths.
- This is a learning/portfolio project, **not a production travel booking service**.

## Roadmap

- [ ] Establish a working synthetic CLI demo, typed schema, and tests.
- [ ] Add deterministic feasibility and ranking.
- [ ] Add a bounded tool-calling agent with mocked/offline tests.
- [ ] Add replanning, versioning, and a minimal demo UI.
- [ ] Evaluate reliability, failure modes, and prompt-injection resistance.
- [ ] Decide whether to implement organizer or disruption MVP next.

See [CHANGELOG.md](CHANGELOG.md) for changes and the [blueprint](docs/PROJECT_BLUEPRINT.md) for concrete acceptance criteria.
