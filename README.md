# Zova

Zova is a learning project for a personalized AI travel assistant. The first
working slice of **MVP A: Personalized Weekend Planner** is an offline Python CLI
with deterministic planning. Agents, integrations, and other MVPs are future work.

## Install and run

Requires Python 3.12+. From the repository root, in PowerShell:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
.venv/Scripts/python.exe -m zova
```

On macOS/Linux use `.venv/bin/python` instead of `.venv/Scripts/python.exe`.
The installed `zova` console command also runs the same demo.
Installation needs package-index access; the installed application and tests
require no network, API keys, or environment variables.

## Demo

Packaged JSON contains a fictional traveler in New York City on Saturday,
October 24, 2026, a $60 USD budget, architecture/thrift/food preferences,
a 2–4 PM commitment, and seven synthetic activities.

The planner ranks candidates by matching interests, then start time and ID.
It greedily accepts an addition only if the proposed plan passes validation,
then returns stops chronologically. It skips candidates exceeding budget,
overlapping commitments or activities, falling outside the trip, repeating IDs,
or targeting a different destination/currency.

Expected selected sessions (UTC−04:00):

- 09:00–10:30: Synthetic architecture walk, $20.
- 11:00–12:00: Synthetic thrift browsing session, $10.
- 12:00–13:00: Synthetic street food lunch, $15.
- 16:00–17:00: Synthetic design gallery, $10.

The CLI displays dated timestamps, unavailable windows, and
`Estimated total: 55.00 / 60.00 USD`. All data is synthetic and costs are estimates.
No reservation or real availability is implied. Budget excludes lodging,
transport, taxes, tips, and purchases outside the listed estimates.

## Tests and checks

```powershell
.venv/Scripts/python.exe -m pytest
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m ruff format --check .
```

Tests cover the exact demo, budget rejection, blocked-time and activity
conflicts, touching boundaries, reduced budgets, empty input, duplicates,
trip/destination constraints, malformed inputs, timezone offsets, and CLI entry
paths. No static type checker or CI is configured yet.

## Architecture

- `src/zova/models.py`: Pydantic validation, aware time windows, Decimal money,
  and typed profile/activity/itinerary models.
- `src/zova/fixtures.py` and `src/zova/data/`: packaged JSON loading independent
  of the current working directory.
- `src/zova/planner.py`: `overlaps`, `validate_plan`, and `build_itinerary`.
- `src/zova/cli.py`: display the resulting itinerary.
- `tests/`: offline regression and CLI tests.

Pydantic rejects malformed data. `validate_plan` checks whether well-formed
activities are feasible together. Keeping these jobs separate lets a future
agent propose plans while Python still enforces constraints. Decimal avoids
binary floating-point surprises. Intervals use `[start, end)`: ending at noon
and starting at noon do not overlap.

## Limits and next steps

Activities have fixed sessions whose duration must match their interval;
start times are not chosen within opening windows. Greedy selection is repeatable
but does not find a globally optimal plan. No routing or transfer buffer is
modeled, so schedule validity does not establish geographic feasibility.
Empty results are reported explicitly.

Next small tasks:

1. Add fixture-path options and a budget override to the CLI, with error handling.
2. Add synthetic travel times and enforce transfer buffers with tests.
3. Explain skipped candidates and which preferences selected stops match.

MVP B (Inbox-to-Itinerary Organizer) and MVP C (Disruption Recovery Copilot)
remain planned. No LLM, MCP, OAuth, Calendar, Gmail, real travel API, frontend,
storage, or deployment is included.

See [AGENTS.md](AGENTS.md) for ongoing engineering instructions,
[docs/PROJECT_BLUEPRINT.md](docs/PROJECT_BLUEPRINT.md) for long-term requirements,
and [CHANGELOG.md](CHANGELOG.md) for implemented changes.
The `zova_repo_starter` directory preserves starter documents; the root README
and `docs/` are authoritative for current development.
