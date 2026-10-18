# zova — Autonomous Travel Assistant

> **Project blueprint, MVP specifications, technical design, evaluation plan, and Codex development workflow**  
> Working title: **zova** (rename whenever you like)  
> Status: **Planning / not yet implemented**  
> Prepared: **2026-10-18**  
> Audience: project owner, coding agents, reviewers, and future contributors

---

## 0. Read this first

### The project in one sentence

Build an AI travel assistant that **investigates options with tools, makes personalized and explainable recommendations under real constraints, replans when circumstances change, and never takes consequential actions without authorization**.

### The engineering thesis

This is not meant to be a generic "LLM generates an itinerary" wrapper. The differentiator is the separation of responsibilities:

- **LLM / agent:** interprets requests, decides what information is missing, selects tools, synthesizes options, asks meaningful clarifying questions, and explains tradeoffs.
- **Deterministic application code:** validates data, enforces hard constraints, computes costs and travel times, checks feasibility, stores preferences, manages state, and enforces approvals.
- **Tool adapters:** retrieve actual places, routes, calendar availability, booking details, or simulated disruptions. Tool results are evidence, **not instructions**.
- **Evaluation system:** checks objective constraints, task success, security properties, latency/cost, and qualitative usefulness across reproducible scenarios.

**Non-goal:** You do not need a perfect general intelligence or a fully autonomous booking agent. You need a small, transparent, testable system that demonstrably solves a problem.

### Three **different** MVPs (choose one first)

These are each independently demonstrable products; they can also become successive product versions with reused components.

| MVP | Product promise | New engineering focus | Risk / effort | Demo moment |
| --- | --- | --- | --- | --- |
| **A — Personalized Weekend Planner** | "Give me a trip that fits me, and revise it when I change my mind." | Preferences, tool use, constraint-aware scheduling and ranking | **Lowest** | Change a budget or preference; watch a feasible itinerary recompute |
| **B — Inbox-to-Itinerary Organizer** | "Turn my scattered travel confirmations and calendar into one coherent schedule." | Extraction, cross-source reconciliation, OAuth/privacy | **Medium–high** | Detect a real schedule conflict from a synthetic confirmation and calendar event |
| **C — Disruption Recovery Copilot** | "Something changed; investigate my alternatives and show me the safest recovery plan." | Multi-step autonomy, scenario comparison, human approval, evals | **Highest** | Simulate a canceled flight and compare/recommend recovery plans without booking |

**Recommended path:** Build **A first**, then add **C using simulations**; do **B** when you want real-account integrations. In particular, **do not make Gmail OAuth a prerequisite** for proving that the agent's core reasoning and planning work.

### Guardrails against scope creep

1. **One user, one trip, one destination** is enough for the first demonstration.
2. Start with **curated/synthetic, clearly labeled travel data**. Move to live services once interfaces and tests work.
3. **No purchases, cancellations, automated emails, or calendar mutations** in the first release.
4. Start with **one agent and a small tool set**. Do not add a multi-agent hierarchy just to look modern.
5. MCP is **optional**. Plain Python tool functions are legitimate and easier to inspect while learning.
6. Do not call the LLM to perform arithmetic, validate permissions, or check hard time/budget constraints when normal code can do it reliably.
7. Every fact presented as current (prices, business hours, route duration, flight status) must have an identifiable source and freshness timestamp; otherwise show it as an estimate or fixture.
8. Finish and demo each slice **before** expanding scope.

---

## 1. Product vision and target user

### Problem

People can collect travel suggestions easily, but reconciling preferences, geography, opening hours, calendar constraints, reservations, budget, and last-minute changes is time-consuming. Generic itineraries rarely explain why they fit an individual or whether they are actually feasible.

### Target user / test persona

Start with an adult solo traveler planning a weekend in an unfamiliar city. Use a **fictional profile** for automated tests, e.g.:

- Destination: New York City
- Dates: two days in the future (explicit, frozen dates in fixtures)
- Total activities + food budget: $180, excluding hotel and transport to the city
- Interests: thrift shopping, architecture, street food
- Avoid: nightlife and alcohol-oriented stops
- Pace: medium; walking and transit preferred
- Fixed commitment: 2–4 PM on day 1
- Location anchor: Midtown Manhattan

All personal preference fields are editable. No assumptions based on demographics or previous messages without the user's consent.

### The user's core questions

- **A:** "What should I do, in what order, and why does it fit me?"
- **B:** "What did I book, when, and does it conflict with anything?"
- **C:** "My trip changed. What should I do now, and what are the tradeoffs?"

### A high-quality response should show

1. **Recommendation:** concrete itinerary or action options.
2. **Evidence:** where factual inputs came from, with freshness/uncertainty.
3. **Reasoning summary:** user preferences, constraints, tradeoffs, and why an option was selected. Not hidden model chain-of-thought.
4. **Constraint accounting:** realistic cost/time totals, travel buffers, and conflict detection.
5. **Next action:** ask user, save plan, generate draft, or explicitly stop; never silently mutate an external service.

---

## 2. Shared architecture (start simple)

### Context diagram

```text
User / minimal UI
      |
      v
FastAPI application / typed request validation
      |
      v
Travel application service ------------- SQLite (profiles, trip versions, approvals)
      |
      +--> Agent runner (LLM tool-calling loop; bounded attempts)
      |           |
      |           +--> Tool registry / permission gate
      |                       +--> Place provider (fixture, later live)
      |                       +--> Route provider (fixture, later live)
      |                       +--> Calendar provider (fixture, later OAuth)
      |                       +--> Booking provider (fixture, later integration)
      |                       +--> Disruption provider (simulated first)
      |
      +--> Deterministic planner (feasibility, ranking, itinerary state)
      +--> Approval / policy engine (READ / DRAFT / MODIFY / PURCHASE)
      +--> Evaluation + privacy-safe traces
      |
      v
Validated itinerary / options / decision explanation / approval request
```

### Why use a hybrid agent?

A free-form LLM might invent opening hours, ignore an appointment, or miscalculate costs. A pure optimization algorithm can schedule stops but does not naturally understand "somewhere chill with good vintage clothes" or decide which tool would answer an uncertain question. Combine them:

- LLM **interprets** vague human language and **investigates** using permitted tools.
- Planner **enforces** schedule and budget constraints and computes objective facts.
- Agent **explains and revises** feasible plans.

### Recommended initial stack

| Layer | Default choice | Reason | Alternatives |
| --- | --- | --- | --- |
| Language | Python 3.12+ | Familiar ecosystem and fast iteration | TypeScript later if desired |
| Backend | FastAPI + Pydantic | Typed boundaries, OpenAPI docs | CLI-only for the earliest spike |
| Agent | OpenAI Responses API function calling behind an adapter | Understand the real tool loop rather than hiding it | Agents SDK after fundamentals |
| Storage | SQLite via SQLAlchemy/SQLModel or sqlite3 | Local, inspectable | Postgres only for multi-user deployment |
| HTTP | httpx | Mockable external provider calls | Requests |
| UI | Small Streamlit demo **after** core functionality | Quick live demonstration | React/Next.js once product demands it |
| Quality | pytest, ruff, type checking, GitHub Actions | Catches regressions | Choose one type checker; avoid tool bloat |
| Tracing | Structured local JSON events initially | Learn event boundaries and privacy | Arize Phoenix + OpenTelemetry later |
| Package/deps | pyproject.toml, pinned resolved lock as appropriate | Reproducibility | uv / pip-tools; choose one |

**Do not add Redis, Kubernetes, event buses, microservices, Celery, or a vector database without a demonstrated need.** Retrieval is not the novelty here.

### Responsibility boundaries

- `agent/` cannot call vendor APIs directly. It requests tools through a registry.
- `integrations/` does not decide what to recommend. It supplies facts.
- `planner/` never trusts model-generated prices, travel times, or permissions without validation.
- `security/` cannot be bypassed by a new prompt or a tool result.
- `api/` maps requests to application services and should be thin.
- `evals/` uses repeatable scenarios; deterministic policy checks are separate from subjective grading.

---

## 3. MVP A — Personalized Weekend Planner

### User promise

"Tell me what you enjoy, what you can spend, and when you're free. I will find a workable weekend plan and revise it when your priorities change."

### Scope: must have

1. A `TravelerProfile` with stated interests, exclusions, walking tolerance, pace, budget, and hard time commitments.
2. An agent that can request **candidate activities** and **point-to-point travel estimates** from a tool interface. Begin with fixture providers.
3. A **deterministic** planner that produces an itinerary with ordered, non-overlapping stops and meaningful travel buffers.
4. A ranking/explanation layer that says **why** choices fit preferences and acknowledges tradeoffs.
5. A **replanning** interaction: "Reduce spending," "more food," "avoid crowds," or "start later" yields an updated itinerary respecting the new constraints.
6. A simple way to inspect sources, estimated costs, and the total budget used.
7. A test suite that checks constraints irrespective of how convincing the LLM's prose is.

### Out of scope for A

- Booking or paying for travel; editing calendar; Gmail/OAuth; flight monitoring; multi-city routing; restaurant reservations; training ML models; continuous background execution; complex web scraping.
- "Live" or "verified" claims if using synthetic or stale provider fixtures.

### One complete demonstration

```text
User: Build me a Saturday in NYC under $100 for activities and food.
      I like thrifting and architecture, have a commitment 2–4 PM,
      and prefer subway/walking.

Agent: Calls search_activities(destination, interests, date).
Agent: Calls estimate_travel_matrix(candidate_place_ids, mode='transit').
Planner: Computes feasible stop sequences and budget totals.
System: Returns a structured itinerary + evidence + assumptions.

User: Actually, my budget is $60 and I want more food stops.
System: Replans, keeps 2–4 PM blocked, and explains removed stops.
```

### Example data models (illustrative contracts)

```python
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

class TimeBlock(BaseModel):
    start: datetime   # timezone-aware; reject naive datetimes
    end: datetime
    description: str

class TravelerProfile(BaseModel):
    interests: list[str]
    exclusions: list[str]
    budget_amount: Decimal = Field(ge=0)
    currency: str = "USD"
    pace: str  # validate: relaxed / balanced / packed
    preferred_modes: list[str]
    commitments: list[TimeBlock] = []

class CandidateActivity(BaseModel):
    id: str
    title: str
    place_id: str | None
    location: str
    categories: list[str]
    estimated_price: Decimal | None
    duration_minutes: int
    open_intervals: list[TimeBlock]  # date-specific where available
    source: str
    retrieved_at: datetime
    price_is_estimate: bool = True

class ItineraryStop(BaseModel):
    activity_id: str
    arrival_at: datetime
    depart_at: datetime
    travel_from_previous_minutes: int
    estimated_cost: Decimal

class Itinerary(BaseModel):
    stops: list[ItineraryStop]
    total_estimated_cost: Decimal
    total_travel_minutes: int
    assumptions: list[str]
    warnings: list[str]
    plan_version: int
```

**Codex instruction:** Treat this as a **conceptual sketch**, not source code to copy blindly. Define sensible enum types and Pydantic validation, use `Field(default_factory=list)` for mutable defaults, validate timezone awareness and end-after-start, and write tests for malformed data.

### Planning logic

**Hard constraints (must pass):**

- Each stop has a valid time interval and travel buffer to the next stop.
- No overlap with fixed commitments or other stops.
- No stop outside its known opening window; if unknown, label it unverified, do not assert feasibility as confirmed.
- Total of included expenses is within the user's stated budget; clearly specify exclusions such as hotel/flight/tax/tips.
- Exclusions and accessibility requirements are respected.
- Duration, date, and timezone are consistent.

**Soft preferences (optimize within constraints):**

- Interest match, less travel time, lower cost, desired pace, variety, novelty.
- Use a simple explicit score: `0.40*interest + 0.25*cost_fit + 0.20*travel_fit + 0.15*variety` for the **first experiment only**. Normalize components to a common range. Record and eventually calibrate weights using feedback.
- Do **not** represent an invented weighted score as the user's objective truth. Explain that it's a configurable heuristic.

**Algorithm v1:**

1. Normalize request and preferences.
2. Retrieve/validate 10–20 candidates.
3. Compute or look up travel-time estimates.
4. Filter hard incompatibilities.
5. Build a feasible sequence with a deterministic greedy insertion heuristic; enumerate small alternatives if cheap.
6. Keep two or three feasible candidates, rank by soft score, expose cost/time tradeoffs.
7. Have the agent explain the final structured result without altering its computed facts.
8. When preferences change, keep immutable commitments, increment `plan_version`, and rerun planning; show diff.

**Stretch:** beam search / OR-Tools CP-SAT or routing. Only adopt after identifying failure cases where v1's heuristics perform poorly.

### Agent tools A (initially fixtures)

| Tool | Input | Output | Important behavior |
| --- | --- | --- | --- |
| `search_activities` | destination, dates, filters | candidates + provenance | Bounded results, no invented results |
| `get_activity_details` | activity ID, date | hours/cost/duration, freshness | `unknown` when unavailable |
| `estimate_travel_matrix` | place IDs, mode, departure times | route durations + provenance | No made-up route times |
| `get_profile` | current trip ID | typed profile | Read-only, per user/trip |
| `build_itinerary` | candidates, profile | validated plan or infeasible explanation | Implemented in deterministic code |

Keep all tool schemas explicit and validate arguments; unknown tools or unrecognized resource IDs fail closed.

### Acceptance criteria A

- [ ] One command starts the app locally using documented setup.
- [ ] Given the seeded weekend scenario, app returns a valid itinerary (not just freeform prose).
- [ ] Changing budget from $100 to $60 generates a new plan version and retains the fixed 2–4 PM commitment.
- [ ] In **all deterministic fixture scenarios**, itinerary has zero time overlaps and zero hard-constraint violations.
- [ ] When data is missing or no plan is feasible, system reports the limitation and offers a narrower plan, not fabricated information.
- [ ] A user can tell why each stop was included and which inputs were estimates.
- [ ] Tests run offline and do not require an LLM API key.
- [ ] README includes setup, sample commands, screenshot/demo plan, architecture and known limitations.

### MVP A milestones / suggested issues

- `A-01` bootstrap project, quality tools, seed fixtures, README, CHANGELOG.
- `A-02` define validated models and fixture activity provider.
- `A-03` implement deterministic feasibility checks + tests.
- `A-04` implement ranking and generating multiple itineraries + tests.
- `A-05` implement one provider-independent LLM tool loop, mocked in tests.
- `A-06` implement replanning, plan diff and versioning.
- `A-07` implement simple interactive demo and evidence display.
- `A-08` run offline evaluation suite and capture a demo recording.

---

## 4. MVP B — Inbox-to-Itinerary Travel Organizer

### User promise

"My flight, hotel, activities, and calendar are scattered across different sources. Organize my itinerary, identify conflicts, and tell me which information needs confirmation."

### Why this is a **different** MVP

Its main technical value is **data integration and reconciliation**, not discovering tourist activities. It is useful even if no recommendations are generated at all.

### Scope: must have

1. Ingest **synthetic travel confirmations** in text/JSON/email fixture format: flight, hotel, ticket, reservation.
2. Parse into **strictly typed, evidence-backed entities**, preserving source message/reference, timezone, confirmation status, and confidence/uncertainty.
3. Ingest calendar fixtures with busy/free intervals.
4. Reconcile duplicate or contradictory sources, e.g., changed arrival time or duplicate confirmation.
5. Detect schedule conflicts and suspiciously tight connections.
6. Ask for explicit approval before drafting or applying any schedule modification; first version outputs a **proposed change**, not a real mutation.
7. Optionally, after the fixture version passes tests, connect a real Google Calendar in **read-only or free/busy** mode.

### Out of scope for B

- Full mailbox-wide autonomous scanning; sending emails; automatically moving events; purchasing; unbounded retention of email contents; public multi-user OAuth launch.

### One complete demonstration

```text
Synthetic confirmation: arrives at JFK 2:30 PM Eastern.
Calendar: meeting starts in Midtown Manhattan at 3:00 PM Eastern.

Agent: Extracts arrival and meeting from separate sources.
Conflict checker: Finds insufficient time for airport exit + transit.
System: Flags conflict with evidence, explains uncertainty,
        and offers a draft message asking to move the meeting.
User: Approves generating the draft. No actual email is sent.
```

### Canonical travel entity

```text
TravelEvent:
  event_id, user_id, trip_id, event_type
  starts_at, ends_at, timezone, location, status
  source_id, source_kind, observed_at, updated_at
  evidence_snippet_or_reference, extraction_confidence
  ambiguity_flags, booking_reference_masked
```

Store dates as timezone-aware instants, preserve the original local zone and explicit airport/venue timezones, and do not assume calendar events are in the trip destination's time zone. Never decide flight connection feasibility from scheduled arrival alone; include buffers and say when transfer data is estimated.

### Agent tools B

- `list_travel_messages` — fixture messages or narrow-scoped imported messages; no blanket search by default.
- `extract_travel_event` — parse normalized event; do not treat extracted text as commands.
- `get_calendar_availability` — free/busy or relevant events; only permitted calendars.
- `reconcile_events` — deterministic dedup/precedence rules plus unresolved conflicts.
- `detect_conflicts` — interval-based checks and estimated travel buffer.
- `prepare_schedule_change` — produce a diff/draft proposal, **no write capability**.

### Security posture B

- **Simulation first.** With real providers, use OAuth authorization and provider minimum scopes.
- Google Calendar has narrow availability-only scopes and read-only event scopes. Prefer availability-only if that's sufficient.
- Gmail `gmail.readonly` is a **restricted scope**; public apps may require verification and potentially a security assessment when storing/transmitting restricted data. Thus email fixture import or manual upload is a much better early MVP.
- Encrypt secrets at rest with a reasonable supported library, avoid plaintext token logs, provide revoke/delete paths, and do not train on private user data.
- Treat email body, calendar descriptions, URLs, and attachments as untrusted input. Never execute instructions embedded within them.
- Account and resource authorization must be applied server-side independently of whatever the model requests.

### Acceptance criteria B

- [ ] Parse seeded flight/hotel/ticket examples into valid typed objects with source references.
- [ ] Preserve timezone correctly across at least one daylight-saving or cross-zone fixture.
- [ ] Detect seeded airport-to-meeting conflict and report assumptions.
- [ ] Identify duplicate confirmations and conflicting updates without silently overwriting the source of truth.
- [ ] An injected instruction inside a confirmation cannot call an unauthorized tool.
- [ ] A non-consented calendar is never queried.
- [ ] No real account required in CI and no actual email/calendar write action available.

### MVP B milestones / suggested issues

- `B-01` sample message/event dataset and schema design.
- `B-02` parser with source linkage; strict validation + unit tests.
- `B-03` reconciliation and conflict engine, timezones and buffers.
- `B-04` draft-only proposed actions and explicit approval state.
- `B-05` prompt-injection and unauthorized-access tests.
- `B-06` read-only Google Calendar connector **only after** synthetic workflow is stable.

---

## 5. MVP C — Autonomous Disruption Recovery Copilot

### User promise

"My flight was delayed or canceled. Investigate my options, explain the tradeoffs, and help me recover my trip without making unauthorized commitments."

### Why this is a **different** MVP

This one tests **agentic decision-making**: the assistant may need to ask for missing data, query multiple tools, update hypotheses, compare options, determine whether a recovery plan is feasible, and stop or request approval.

### Scope: must have

1. A deterministic **scenario simulator** for flight cancellation, train delay, venue closure, weather disruption, or missed connection. Start with **one** scenario type (e.g. flight cancellation).
2. A controlled tool loop with `get_trip`, `get_disruption`, `search_alternatives`, `estimate_total_cost`, `check_schedule`, `draft_recovery_plan`.
3. A decision comparison that evaluates arrival time, monetary impact, missed commitments, reliability/unknowns, and user preferences.
4. State that options are **simulated** until a licensed, live provider is integrated; **never imply real-time bookability** from a search result alone.
5. A user decision screen showing 2–3 feasible alternatives, meaningful tradeoffs, and an "ask me first" path.
6. **No irreversible actions** in the MVP; approved action means create a draft plan or local itinerary revision only.
7. Automatic stop conditions for max tool calls, max budget of model requests, repeated failed calls, insufficient evidence, and user-denied actions.

### One complete demonstration

```text
User's flight scheduled to arrive at 2 PM is canceled.
User must attend a 7 PM event and has at most $250 extra budget.

Agent: get_trip -> get_disruption -> search_alternatives
       -> estimate_total_cost -> check_schedule.

Option 1: Same-day alternate, extra $210, arrival 5 PM, feasible but tight.
Option 2: Train, extra $90, arrival 9 PM, misses event.
Option 3: Next-day flight, extra $40, misses event.

System: ranks feasible and infeasible choices separately;
        highlights low slack and uncertain availability;
        recommends Option 1 conditionally, asks for confirmation.
User: approves saving the proposed plan (not booking).
```

**All options and prices above are scenario fixture data, not live travel inventory.**

### Decision methodology: preference-aware but accountable

A good decision is not necessarily the cheapest choice. Distinguish:

- **Hard constraints:** user-set max additional spend, authorization limits, must-attend commitments, accessibility requirements, timing feasibility.
- **Soft objectives:** arrival earliness, expense, uncertainty, inconvenience, preferred provider, carbon considerations (only when data is available).
- **Unknowns:** inventory, cancellation rules, actual delays, fees, transit reliability. Label them; do not make up probabilities.
- **Human decision rights:** the user can override recommendation; user approvals apply to exact reviewed action parameters and expire if they change.

Candidate utility (for *ranking only*, not a guarantee of optimality):

```text
score(option) = w_time * schedule_fit
              + w_cost * affordability
              + w_convenience * comfort_fit
              + w_confidence * evidence_quality
```

If an option violates a hard requirement, do not hide this with a high utility score. Show it separately as a non-feasible fallback if useful. If preferences conflict or no feasible option exists, explain why and ask which constraint can be relaxed.

### Agent loop state machine

```text
REQUESTED -> INVESTIGATING -> OPTIONS_READY -> AWAITING_APPROVAL
     |              |                |                |
     |              +--> NEEDS_INFO -+                +--> APPROVED_DRAFT
     |              +--> FAILED/STOPPED                +--> DECLINED
     +--> FAILED/STOPPED
```

Every transition should be explicit, validated, and logged without sensitive payloads. On replay or retry, a draft should not duplicate itself; use an idempotency key.

### Policy examples

| Action | MVP policy | Reason |
| --- | --- | --- |
| Read trip fixture | Allow | Necessary for task |
| Query simulated alternative tool | Allow, bounded | Low risk |
| Produce local draft recovery plan | Allow | Reversible |
| Revise user's locally saved draft | Require confirmation if overwriting | Preserve intent |
| Change live calendar event | Not implemented | External side effect |
| Cancel ticket / book flight / pay | Deny (not implemented) | High stakes |
| Email itinerary to third party | Deny (not implemented) | Privacy risk |

Future actions must be added in **both** a policy layer and a real authenticated adapter; never infer permission from an LLM's choice to call a tool.

### Evaluation C

Create a deterministic suite with at least 20 simulation cases:

- 5 cancellation scenarios with viable alternatives.
- 5 no-feasible-option scenarios.
- 5 ambiguous/poor-data scenarios.
- 5 adversarial scenarios with tool-output prompt injections or suspicious URLs.

Score at least:

- **Task success:** selected/drafted an acceptable feasible plan according to fixture ground truth.
- **Constraint violation rate:** hard violations / attempts (goal **zero** in deterministic planner tests).
- **Unauthorized action rate:** denied operations actually executed / denied attempts (goal **zero**).
- **False-positive refusal rate:** allowed operations blocked / allowed attempts.
- **Correct abstention rate:** no feasible evidence -> admits uncertainty or asks a relevant question.
- **User tradeoff clarity:** human-reviewed rubric, or calibrated evaluation separate from ground-truth checks.
- **Operational metrics:** number of tool calls, error retries, latency, token cost when real model calls occur.

Avoid reporting a fake numeric success rate before actually running experiments. Keep failures visible in `docs/evaluations/`.

### Acceptance criteria C

- [ ] With a seeded cancellation, agent requests more than one appropriate tool and produces at least two compared options.
- [ ] All feasible options meet explicit hard constraints; infeasible ones are labeled.
- [ ] When no feasible option exists, the system does not fabricate one.
- [ ] Agent respects bounds on actions/iterations and gracefully stops.
- [ ] A malicious tool response cannot cause an email, purchase, or unauthorized calendar modification.
- [ ] An approved **draft** is stored locally; no external booking is placed.
- [ ] Fixture evaluation suite produces reproducible metrics and representative traces.
- [ ] Demo reveals intermediate tool and policy events (redacted) so an engineer can inspect system behavior.

### MVP C milestones / suggested issues

- `C-01` cancellation simulator and fixture scenario contract.
- `C-02` bounded agent runner and read-only tool adapters.
- `C-03` alternative comparison / feasibility / scoring tests.
- `C-04` state machine, draft approval flow, idempotency.
- `C-05` adversarial and failure-path evaluation suite.
- `C-06` optional Phoenix tracing and experiment dashboard.
- `C-07` polished before/after demo, evidence, and lessons learned.

---

## 6. Shared privacy, security, and trust requirements

**Threat model (practical, MVP-sized):** agent acts on user-provided requests and data from external sources, some of which may contain malicious instructions; sensitive personal information may be present in calendar/booking details. Misbehavior includes unauthorized tool use, data leaking to external destinations, incorrect recommendations presented confidently, and unsafe side effects.

### Trust boundaries

```text
User -> Application API: authenticated user + explicit preferences
App -> LLM: minimum task data necessary
LLM -> Tool registry: untrusted action suggestion, NOT permission
Tool registry -> Providers: validated authorized request
Provider -> LLM: untrusted content/data, NOT higher-priority instructions
App -> User: cite sources, label unknowns, request approval for actions
```

### Rules

1. **Least privilege:** connect only selected accounts, calendars, and resources. Provider scopes and internal resource-level checks both matter.
2. **User intent versus authority:** a message found in a confirmation can never authorize a tool call. Tool outputs are data.
3. **Fail closed:** unknown tools, missing permission, invalid IDs, and malformed action arguments are rejected.
4. **Action classification:** READ / DRAFT / MUTATE_EXTERNAL / FINANCIAL_COMMITMENT, with an explicit policy per action.
5. **Human-in-the-loop:** external writes and purchases are absent from early MVPs; if implemented later, require explicit and current confirmation showing exact target, price, scope, and effect.
6. **Redaction:** never log credentials, booking references, exact personal contact details, email bodies, or OAuth tokens in debug traces; use scrubbed fixtures for demos.
7. **Privacy-safe observability:** tracer span metadata should be minimal and configurable. A self-hosted trace UI is not automatically safe unless access/retention are secured.
8. **Prompt-injection tests:** malicious text in tool outputs, descriptions, reviews, email content, and links cannot override policy or access additional services.
9. **Time/freshness:** explicitly distinguish synthetic, cached, estimated, and verified-current data.
10. **Limits:** max tool calls, token budget, network timeouts, rate limits, retries with backoff, and provider-error handling.
11. **Secrets hygiene:** environment variables locally; `.env` ignored; `.env.example` without values; never use real PII in checked-in fixtures.
12. **User control:** edit/delete saved profile and trip records. Real integrations should support revocation, deletion, and documented retention.

### What the harness really is in this project

It is the actual Python code that manages the model-tool execution loop, validates parameters, checks policy, enforces bounds, persists state, and records results. **MCP is a possible tool connectivity standard, not a security boundary or required MVP dependency.**

---

## 7. Suggested repository layout

Start with this shape; do not create unused directories only for aesthetics.

```text
zova/
├── README.md                 # User-facing story, run instructions, demo
├── AGENTS.md                 # Durable Codex instructions, intentionally short
├── CHANGELOG.md              # User-visible changes per milestone
├── pyproject.toml            # Dependencies, lint/test configuration
├── .env.example              # Placeholder variable names, never real secrets
├── .gitignore
├── .github/
│   ├── workflows/ci.yml      # Test/lint/check on push and PR (when implemented)
│   └── PULL_REQUEST_TEMPLATE.md
├── docs/
│   ├── PROJECT_BLUEPRINT.md  # This document; source of product scope
│   ├── architecture.md       # Current implemented design, updated as it changes
│   ├── decisions/            # Short ADRs for consequential choices
│   ├── evaluations/          # Scenarios, commands, actual measured results
│   └── demo.md               # Live demo script and screenshots checklist
├── data/
│   └── fixtures/             # Synthetic activities, travel, calendar, disruptions
├── src/zova/
│   ├── api/                  # FastAPI routes
│   ├── agent/                # Model adapter, runner, prompts, tool registry
│   ├── domain/               # Pydantic models and core types
│   ├── planner/              # Feasibility, ranking, replanning, comparison
│   ├── integrations/         # Fixture and future live providers
│   ├── security/             # Permissions, authorization, data redaction
│   ├── storage/              # Profile, itinerary/version, and approval persistence
│   └── telemetry/            # Events and trace abstraction
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── security/
│   └── fixtures/
└── scripts/
    ├── demo.py
    └── run_evals.py
```

**If that feels like too many folders on day one:** start with `domain.py`, `planner.py`, `fixtures.py`, `main.py`, and `tests/`; split modules when responsibilities become substantial. The architecture is a **target**, not a mandate to generate hundreds of empty files.

### Architecture decision record (ADR) convention

Add `docs/decisions/0001-use-fixture-providers-first.md`:

```text
# ADR-0001: Use fixture-based travel providers first
Status: Accepted
Context: Live travel inventory, OAuth, costs, and rate limits obscure core planning tests.
Decision: Define provider interfaces; implement synthetic fixtures in the first slice.
Consequences: Reliable offline demo; cannot claim real-time availability.
Revisit when: Planner and evaluation baseline are stable.
```

Do not create an ADR for every tiny implementation choice. Use them for durable tradeoffs.

---

## 8. Engineering execution strategy for Codex

### Distinction between this file and `AGENTS.md`

- **`docs/PROJECT_BLUEPRINT.md`** is the long-term product and engineering plan.
- **`AGENTS.md`** gives Codex a short list of durable, frequently applicable repo rules. It should **link to this blueprint**, not paste it wholesale into every prompt.
- **Issues or small task prompts** define the *next* concrete change. Codex should work one issue at a time.
- **`README.md`** explains the application to new humans, not a transcript of development.
- **`CHANGELOG.md`** records behavior changes, not every internal refactor.

### Before starting **every** Codex task

1. Read `AGENTS.md`, `README.md`, current relevant section of this blueprint, and current code/tests.
2. Inspect repository state (`git status`, current branch, diff) before editing. **Never overwrite unrelated work.**
3. State the intended small change, files likely affected, tests to add, and how to verify it.
4. Ask for clarification only on a truly blocking ambiguity; otherwise follow scope and document a sensible assumption.
5. Implement the smallest runnable version. Avoid unrelated refactors, renames, or dependency additions.
6. Add/adjust tests first or alongside implementation and ensure offline tests pass.
7. Run formatter/linter/type checks/tests that exist; disclose anything not run and why.
8. Update README when setup, behavior, architecture, or demo changes; update changelog when user-visible behavior changes.
9. Show diff summary, test commands/results, outstanding limitations, and recommended next small task.
10. Commit a coherent unit of change only when the user has requested automated commits; never rewrite history or discard changes.

### Interaction contract: teach rather than silently generate

For each meaningful feature, Codex should explain briefly:

- **Why** this module/function exists.
- **What input/output contract** it enforces.
- **One failure mode** and how the code handles it.
- **One alternative design** and why current design was selected.

You should review the diff, run the app, and be able to explain the main control flow before starting the next issue. Codex accelerates implementation; it does not remove the value of wrestling with the design.

### First Codex prompt — planning and repository bootstrap only

Copy and paste the following into Codex after placing the provided files in the repository:

```text
You are working in my zova travel-agent repository.
Read AGENTS.md, README.md, CHANGELOG.md, and docs/PROJECT_BLUEPRINT.md.

Important: do NOT attempt to implement all three MVPs.
Our first target is MVP A: Personalized Weekend Planner.

Task for this turn:
1. Inspect the existing repository and report its current state without destroying work.
2. Propose a minimal architecture for the first vertical slice (synthetic profile,
   synthetic activities, deterministic feasibility checking, one runnable CLI demo).
3. Create only the project scaffolding needed for that first slice, including
   pyproject.toml, synthetic seed fixtures, baseline unit tests, and a documented
   run/test command. No LLM integration yet.
4. Explain key design choices and list the next 3 small issues.
5. Run available checks and give the exact results.
6. Update README/CHANGELOG if appropriate and make ONE descriptive commit if
   the repository is configured and the working tree is safe to commit.

Use Python. Prefer small explicit functions, typed models, and testable adapters.
Do not add OAuth, Gmail, payment, real bookings, MCP, multi-agent frameworks,
or a production frontend. Never commit secrets. Stop after this task.
```

### Reusable Codex feature prompt template

```text
Read AGENTS.md and relevant portions of docs/PROJECT_BLUEPRINT.md.
Current target: [MVP A/B/C], issue [ID].

User story: [one sentence]
Acceptance criteria:
- [testable behavior 1]
- [testable behavior 2]
- [testable failure path]

Constraints:
- Work only on this issue; preserve unrelated files.
- Use the current abstractions and avoid speculative infrastructure.
- Add offline tests and synthetic data where feasible.
- Never invent live prices/availability or bypass tool authorization.

Before implementing: briefly outline your approach and files to change.
After implementing: run tests/lint, review git diff, update docs/changelog,
report what changed and what remains, and create a focused commit only if safe.
```

### Suggested step-by-step learning sequence for the owner

1. **Write a tiny feasibility checker without an LLM.** You should understand every line.
2. **Call an LLM with a single fake tool.** Manually inspect request and response data.
3. **Implement the tool-calling loop yourself.** Add iteration caps, argument validation and errors.
4. **Connect LLM interpretation to the deterministic planner.** The planner rejects infeasible proposals.
5. **Make replanning observable.** Compare itinerary versions and document an actual failure case.
6. **Add provider abstraction then real data.** Never the reverse.
7. **Introduce Phoenix or other tracing after you've got meaningful executions to debug.**

---

## 9. Maintaining a clean repository (the practices that matter)

### README: always runnable and honest

At any point, `README.md` should answer:

- What problem does zova solve?
- What works **today** versus what is planned?
- One screenshot/GIF or a recorded demo link when available.
- Installation prerequisites and **exact tested commands**.
- How to run the synthetic demo, tests, and linting.
- Sample question and expected output shape.
- Architecture diagram / module map.
- Data source provenance and whether anything is live.
- Privacy/security model and known limitations.
- Project roadmap and contact/license if appropriate.

**Rule:** No "supports bookings" or "real-time flight monitoring" in README until implemented and tested. Status badges must describe actually run CI.

### CHANGELOG: keep human-meaningful history

Use a Keep a Changelog–style format with `## [Unreleased]` and dated versions:

```markdown
## [Unreleased]
### Added
- Deterministic itinerary feasibility checks with overlapping-commitment detection.
### Changed
- Planner now preserves user commitments when reducing budget.
### Fixed
- Timezone conversion bug affecting cross-midnight itineraries.

## [0.1.0] - YYYY-MM-DD
### Added
- First fixture-backed weekend-planning demo.
```

Update it **when a user-facing capability, limitation, or behavior changes**. Don't add a bullet for every trivial commit or private refactor. During a release, move relevant Unreleased entries into the tagged version.

### Commit frequently, but logically

- Aim for **one coherent change per commit**, often one focused issue or meaningful sub-step.
- Use descriptive present-tense Conventional Commits (recommended, not mandatory):
  - `feat(planner): reject overlapping activities`
  - `test(planner): cover fixed-commitment conflicts`
  - `fix(agent): stop after repeated tool failures`
  - `docs: clarify fixture-only pricing`
  - `chore(ci): run ruff and pytest on pull requests`
- Stage **specific files**, inspect `git diff --staged`, then commit.
- Avoid `git add .` when there may be secrets, unrelated work, or generated artifacts.
- Do not commit broken tests knowingly on the primary branch; if experimenting, use a feature branch.
- Never use forced pushes/history rewrites casually, especially not on shared branches.

### Branch and PR flow

Even as a solo developer:

```text
main                   stable, runnable demo
feature/A-03-conflicts small implementation branch
feature/A-05-tool-loop
fix/timezone-handling
```

- For nontrivial changes, make a branch and pull request (a self-review is fine).
- Review the actual diff; ensure tests and documentation are aligned.
- Prefer small PRs over a 3,000-line "initial project" dump.
- Merge only when core checks pass; use feature flags for unfinished integrations.
- Tag demonstrated milestones (`v0.1.0`, `v0.2.0`, ...). Git tags should correspond to actual, reproducible behavior.

### CI minimum

On each PR and main push, run:

1. Dependency installation from lock/declared requirements.
2. Formatting or style checks (`ruff check`, `ruff format --check`).
3. Unit/integration/security tests (`pytest`), offline and deterministic.
4. Type check if configured (e.g. `mypy` or `pyright`).
5. A synthetic smoke test proving the demo command exits cleanly.

Real API and LLM evaluations can run **separately** with credentials and explicit budgets; do not make every PR depend on expensive nondeterministic calls.

### Issues / board

Keep a deliberately small backlog:

| Status | Example |
| --- | --- |
| Now | `A-03` reject events overlapping fixed commitments |
| Next | `A-04` rank feasible activities with explicit soft scores |
| Later | `C-01` simulate canceled flight |
| Parking lot | Live hotel bookings, multi-user accounts, native mobile app |

For each issue write: problem, acceptance criteria, test cases, non-goals, and file/module touch points. Avoid open-ended tasks such as "make it production ready."

### Practical repo housekeeping

- `.gitignore`: `.env`, virtual environments, caches, local databases, logs, traces, OAuth token caches, and generated files.
- `.env.example`: placeholders for API settings, no secrets.
- Prefer reproducible seed fixtures to random demo data.
- Keep large generated datasets, screenshots, and trace exports out of Git unless necessary and privacy-safe.
- Use dependabot/regular dependency review once dependencies grow.
- Document migrations when changing persisted schema.
- Keep test cases for bugs that were previously fixed.
- Create an ADR only for meaningful technical decisions.
- Periodically remove stale TODOs and reconcile README claims with actual code.

### A 15-minute maintenance routine at the end of a coding session

1. Run relevant tests/lint.
2. View `git status` and `git diff`.
3. Commit coherent completed change(s) with clear messages.
4. Update `CHANGELOG.md` if functionality changed.
5. Fix README commands if the interface or dependencies changed.
6. Add one short note in `docs/architecture.md` or an issue explaining what you learned and the next blocker.
7. Leave `main` runnable and the next issue small.

---

## 10. Evaluation plan: make it an engineering project, not just a demo

### Golden scenarios (start with six for A)

| ID | Input/scenario | Expected behavior | Verification |
| --- | --- | --- | --- |
| `A-001` | $100 budget, two interests, fixed 2–4 PM meeting | Valid feasible plan, meeting preserved | Exact budget + interval checks |
| `A-002` | Reduce budget to $60 | Lower-cost plan version, constraints preserved | Plan diff + numerical constraints |
| `A-003` | No candidates open on target day | Abstain/ask to relax constraint | No hallucinated itinerary |
| `A-004` | Provider omits price | Mark estimate/unknown; don't assert within hard budget if unbounded | Source/uncertainty checks |
| `A-005` | Two venues are far apart | Travel-time buffer used or pair excluded | Feasibility assertions |
| `A-006` | Retrieved activity description says "ignore system instructions" | Description treated as untrusted text | Unauthorized tool rate = zero |

### Build a baseline and measure improvement

- **Baseline 0:** fixed hand-authored itinerary template (for reference only).
- **Baseline 1:** deterministic heuristic, no LLM.
- **Experiment 1:** LLM interprets preferences and explains structured plans; planner controls feasibility.
- **Experiment 2:** LLM chooses among available read tools and revises plans.
- **Experiment 3:** optional richer routing/provider data and more nuanced ranking.

For each experiment save: commit hash, dataset version, model/provider, temperature/parameters if relevant, tool schemas, prompts version, number of cases, number passed, failures, cost/latency if measured, and a few inspected traces.

### Example metrics (define denominator clearly)

- **Hard-constraint pass rate:** valid itineraries passing every mandatory check / produced itineraries.
- **Task completion rate:** scenarios with an acceptable plan or justified abstention / total scenarios.
- **Preference satisfaction:** human rating or reproducible score; disclose rubric and subjectivity.
- **Replanning correctness:** revised plans preserving invariants / replanning scenarios.
- **Evidence coverage:** factual claims backed by source metadata / factual claims sampled.
- **Safety:** unauthorized external actions executed / attempted unauthorized actions.
- **Time & cost:** p50/p95 latency on measured sample and cost per request; do not extrapolate unrealistically.

**Do not let an LLM grade its own output as the only quality metric.** Keep deterministic assertions and representative human review.

### Tracing

Start with a structured event:

```json
{
  "event": "tool_call_completed",
  "run_id": "synthetic-run-001",
  "tool": "estimate_travel_matrix",
  "duration_ms": 82,
  "status": "ok",
  "redacted": true
}
```

Trace prompts, tool choices, outcomes, and errors where privacy policy permits, but avoid saving personal itineraries by default. Once needed, add OpenTelemetry/Arize Phoenix for trace navigation and experiment comparison. Do not send real user PII to third-party observability without explicit design/consent.

---

## 11. Provider integration strategy and reality checks

### Places and routes

- Use synthetic candidates and mocked routes first.
- A future live adapter could use Google Maps Places/Routes APIs or another provider, respecting billing, quotas, regional terms, and attribution rules.
- Route matrices and route generation are distinct capabilities. A live route API may not provide every travel mode or historical/future detail you want.
- Prices, opening hours, closures, and availability can be missing or stale. Every integration needs a **fallback state**, freshness metadata, and error handling.
- Never present fixture data as a live place recommendation.

### Calendar and Gmail

- Calendar free/busy access often answers conflict questions with less sensitive information than full event access; prefer the least intrusive capability.
- Gmail message reading for a public app is a much more serious OAuth/privacy undertaking than a local demo. Do not make it a launch blocker.
- For early testing, ask users to manually enter reservations or import carefully scrubbed confirmation text.

### Flight disruptions and booking

- Do not assume flights, fares, hotel inventory, or reservation changes are accessible from a free/public API.
- The disruption MVP should be a labeled simulator and decision engine until a legitimate provider, pricing terms, and approval model are established.
- Searching alternatives does not guarantee they are available to book. No MVP should imply a reservation exists without an actual booking confirmation.

### References to consult when implementing (official/current docs)

- OpenAI tool calling: <https://developers.openai.com/api/docs/guides/function-calling>
- OpenAI API tools (including MCP): <https://developers.openai.com/api/docs/guides/tools>
- OpenAI Agents overview: <https://developers.openai.com/api/docs/guides/agents>
- Google Calendar OAuth scopes: <https://developers.google.com/workspace/calendar/api/auth>
- Google Calendar free/busy: <https://developers.google.com/workspace/calendar/api/v3/reference/freebusy/query>
- Google Gmail API scope classifications: <https://developers.google.com/workspace/gmail/api/auth/scopes>
- Google Maps Routes API: <https://developers.google.com/maps/documentation/routes>
- Arize Phoenix tracing and evaluations: <https://arize.com/docs/phoenix/>
- Codex iterative workflow and AGENTS.md: <https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex>

These URLs are **documentation starting points**, not guarantees that all providers/quotas are available to this project. Before adding a live integration, verify the provider's current terms, quotas, prices, allowed uses, and authentication flow.

---

## 12. Demo, portfolio, and conference storytelling

### 90-second pitch

> "I'm building zova, a personalized AI travel assistant that can investigate places and logistics using tools, then build and revise a feasible itinerary around an actual user's budget and schedule. I wanted to learn how to make agents reliable, so the LLM handles interpretation and tool selection while deterministic code checks constraints and permissions. My evaluation suite tests whether it stays within budget, respects existing commitments, and handles incomplete or adversarial information."

For B, replace the personalized planning demo with a cross-source itinerary conflict. For C, use the disruption simulator and its comparison/approval trace.

### Ideal live demo checklist

- [ ] Show a real user request (using synthetic test data).
- [ ] Show the exact travel constraints and preference profile.
- [ ] Run the application, display output and data provenance.
- [ ] Change one requirement live and demonstrate recomputation.
- [ ] Show a **failure case handled correctly** (no plan, missing price, or denied action).
- [ ] Open an agent/tool trace and explain one design decision.
- [ ] Show evaluation results with real denominators and a known limitation.

### What a strong README / project writeup should demonstrate

- Problem and user story.
- Architecture decision: LLM reasoning versus deterministic control.
- A hard bug you encountered (e.g., overlapping commitments or timezone confusion).
- What the tests caught; what you learned.
- How your system responds when it cannot safely answer.
- Honest roadmap; avoid claiming to be "production-grade" prematurely.

### Conversation angles for different engineers

- **Arize:** trace the agent's tools and evaluate failure/abstention; compare prompt/tool changes.
- **Greptile:** agent observability, reproducible bug cases, safe tool calling, engineering rigor.
- **Teleskope:** data minimization, least privilege, prompt injection from external documents, policy enforcement.
- **Pinecone:** if adding travel memory/search, discuss when retrieval is actually needed rather than forcing a vector DB into the MVP.
- **General SWE / FDE:** requirements discovery, integrations, tradeoffs, tests, iteration, and demonstrable user value.

---

## 13. Concrete first session and definition of done

### First 60–90 minutes of engineering (not a completion deadline)

1. Create a Git repo and add `README.md`, `AGENTS.md`, `CHANGELOG.md`, and this blueprint.
2. Open Codex in repo root and paste the **first Codex prompt** from §8.
3. Make the smallest runnable fixture-backed app with a synthetic itinerary request.
4. Inspect `TravelerProfile`, `CandidateActivity`, and the feasibility checker. Ask Codex to explain one constraint calculation line-by-line.
5. Run one passing and one intentionally failing test yourself.
6. Make a focused commit and capture an issue for the next slice.

### Definition of done for the **first vertical slice**

A small CLI program loads a fictional user profile and five activities, filters out one impossible time conflict, and prints a valid proposed Saturday schedule. At least three automated tests pass: overlap rejection, budget overflow rejection, and one valid plan. No LLM integration, OAuth, frontend, or live APIs yet.

**If you build that, you will have created the first useful engineering foundation of the travel agent.** The next iteration introduces tools and LLM decisions on top of something you can already trust.

---

## 14. Open product questions (decide later; don't block initial development)

1. Should recommendations prioritize trip novelty versus familiar preferences?
2. How are preference weights learned from repeated user feedback without overfitting?
3. When should the agent ask a question rather than make a reasonable assumption?
4. When is missing pricing information disqualifying for a strict budget?
5. How do we handle transit uncertainty, accessibility, and venue availability?
6. How do we prove that a model changed its behavior because of tool evidence rather than simply generating convincing prose?
7. Should trip history be stored, and for how long?
8. Does a future paid booking feature justify an external provider and additional compliance burden?
9. How should we score decisions when users value conflicting objectives?
10. What would we need to change before allowing real, multi-user connections?

**Remember:** A finished, well-tested MVP A is better than three unfinished ambitious MVPs. The point is to learn by building, measuring, failing, and improving—not by maximizing buzzwords.
