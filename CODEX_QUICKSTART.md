# Codex quickstart — first working slice

1. Create a new Git repository named `zova` (or use your existing chosen repo).
2. Copy these files into it, preserving locations: `AGENTS.md`, `README.md`, `CHANGELOG.md`, `docs/PROJECT_BLUEPRINT.md` and this file.
3. Open that repo in Codex. First read `AGENTS.md` and the relevant MVP A sections of the blueprint.
4. Paste the prompt below. Do **not** ask Codex to build all three MVPs at once.
5. Review what it creates, run tests, and make sure you can explain the planner's constraint checks before moving on.

## First prompt

```text
Read AGENTS.md, README.md, CHANGELOG.md, docs/PROJECT_BLUEPRINT.md,
and docs/CODEX_QUICKSTART.md.

Build ONLY the first vertical slice of MVP A (Personalized Weekend Planner).
Before editing, inspect git status, current code, and repository conventions.

Target deliverable:
- Python project with a clean pyproject.toml and runnable offline CLI demo.
- Synthetic profile and 5–10 synthetic activities in fixtures.
- Typed validation models for requests and activities.
- Deterministic itinerary feasibility checks (budget and blocked-time overlap).
- At least 3 offline tests: one valid itinerary, one budget failure,
  and one time conflict failure.
- Minimal README commands that you personally verify by running.
- Appropriate .gitignore and .env.example only if environment variables exist.
- Changelog update if user-visible functionality has been added.

Non-goals: NO LLM API, OAuth, live maps, Gmail, calendar sync, MCP, bookings,
complex frontend, automatic purchases, or speculative architecture.

Explain your approach before implementation. Use small modules, make changes
cohesively, run checks, and summarize the actual results. Make one focused
commit when safe and configured; do not overwrite unrelated work.
Stop after this vertical slice and list the next 3 granular tasks.
```

## Next prompts (separate Codex turns)

**Issue A-03 — Feasibility:**

```text
Implement MVP A's deterministic itinerary validator, following AGENTS.md and
docs/PROJECT_BLUEPRINT.md. Check every stop against budget, schedule conflicts,
known opening windows, and travel buffers. Write parameterized tests for both
valid and invalid plans. Change only relevant modules; run offline checks; keep
README accurate and changelog updated for user-visible differences. One focused
commit when safe. Explain two edge cases and stop.
```

**Issue A-05 — Agent tool calling (only after the planner passes):**

```text
Implement a minimal single-agent tool-calling loop behind a model adapter for
MVP A. Limit its tools to fixture-backed activity lookup, travel-time lookup,
and a deterministic build-itinerary call. Validate tool arguments, cap steps,
and handle errors. Add mocked agent loop tests so CI needs no paid API key.
Never let model text bypass hard constraints. Show one execution trace and the
request/response shape. Do not add OAuth or MCP. Stop after this task.
```

**Issue A-06 — Replanning:**

```text
Implement changes to an existing itinerary when the user revises budget or
interests, preserving fixed commitments and producing a versioned plan diff.
Use the deterministic planner for all feasibility checks. Test no-overlap,
budget, and infeasibility handling. Keep docs current and make one coherent
commit when safe. Stop after this task.
```

## How to ask Codex for help learning

- "Walk me line by line through how the itinerary validator rejects an overlap."
- "What is the exact control flow from model tool request to Python function and back?"
- "Write a failing test for a midnight or timezone edge case, and show me why."
- "What could go wrong if a tool returns malicious instructions in an activity description?"
- "Show me the smallest next change that would reveal a design flaw in this architecture."

Prefer finishing and understanding one behavior to generating several thousand lines at once.
