# Zova

Zova is a learning project for a personalized AI travel assistant. The first
working slice of **MVP A: Personalized Weekend Planner** is an offline Python CLI
with deterministic planning, also exposed through a local FastAPI API.
A small React browser interface can generate and display plans with an editable budget.
Agents, integrations, and other MVPs are future work.

## Install and run

Requires Python 3.12+. From the repository root, in PowerShell:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
.venv/Scripts/python.exe -m zova
```

On macOS/Linux use `.venv/bin/python` instead of `.venv/Scripts/python.exe`.
For example, from the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m zova
```

The installed `zova` console command also runs the same demo.
Use `--budget` to override the budget for a single run without editing the profile:

```powershell
python -m zova --budget 30.00
python -m zova --profile profile.json --activities activities.json --budget 100
```

All three options are optional. Omitted file paths use packaged demo inputs;
an omitted budget keeps the loaded profile's budget. Custom JSON files must use
the same schema as the packaged fixtures. Budget amounts must be finite and
nonnegative, with at most two decimal places and ten digits before the decimal
point. Invalid arguments or input files print an error and exit with status 2.

Installation needs package-index access; the installed application and tests
require no network, API keys, or environment variables for the synthetic planner.

## Local FastAPI server

The installation above includes FastAPI and Uvicorn. On macOS/Linux run:

```bash
.venv/bin/python -m uvicorn zova.api:app --reload --host 127.0.0.1 --port 8000
```

On Windows use `.venv/Scripts/python.exe` with the same arguments.
Open http://127.0.0.1:8000/docs for interactive API documentation, or
http://127.0.0.1:8000/health for `{"status":"ok"}`.
`POST /itinerary` accepts a JSON object with `profile` and `activities`, using
the packaged fixture schemas, and builds a deterministic itinerary. The response
contains `message`, the input `profile` (including currency), selected `activities`,
and `total_cost` as a decimal string such as `"55.00"`. Costs are synthetic estimates.
No feasible activities returns HTTP 200 with an empty list and `"0.00"` total.
Invalid inputs return HTTP 422; nothing is saved or booked. This replaces `/upload`.

To try the fixture request while the server is running:

```bash
.venv/bin/python - <<'PYTHON'
import httpx
from zova.fixtures import load_demo

profile, activities = load_demo()
response = httpx.post("http://127.0.0.1:8000/itinerary", json={
    "profile": profile.model_dump(mode="json"),
    "activities": [activity.model_dump(mode="json") for activity in activities],
})
response.raise_for_status()
print(response.json())
PYTHON
```

The demo returns four stops and `"55.00"` estimated total in USD.
Use synthetic data only; the local development API has no authentication.

For the experimental Ticketmaster endpoint, set `TICKETMASTER_API_KEY` in a
local `.env` file and launch Uvicorn from that directory. Restart after changing
`.env`; exported environment variables take precedence. Keep `.env` out of Git.
The synthetic planner does not need a key. `GET /get_events?city=Boston`
returns provider JSON. Blank cities return 400, missing keys return 503, and
provider request failures or invalid JSON objects return 502.

The editable installation makes `zova` importable from
`src/zova`; use `zova.api:app`, without a `src` prefix or a custom `PYTHONPATH`.
Keep `--reload` for local development.

## Browser frontend (React + TypeScript + Vite)

Requires Node.js 22.12+ (or 20.19+) and npm, plus the Python installation above.
Run the backend from the repository root in one terminal:

```bash
.venv/bin/python -m uvicorn zova.api:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open http://127.0.0.1:5173. The welcome page introduces Zova with an original
city illustration, explains the fixture demo, and links to the planner on the same
page. Click **Try the planner**, then **Generate Itinerary** for the $60 fixture
plan (four stops, $55 estimated total). Try $30 for fewer stops, or $0 for an
empty itinerary. The browser displays loading, validation, and server/network
errors; starting FastAPI and submitting again retries a failed request.

Use **Find events** in the navigation or scroll below the planner to search
Ticketmaster by city, with an optional keyword to narrow the results. Blank
keywords are omitted from provider requests. Configure `TICKETMASTER_API_KEY` in the backend's `.env`
and restart FastAPI first. The browser calls `GET /get_events?city=...` through
the Vite proxy; the key stays on the backend. Results show up to the first five
events in Ticketmaster's returned order, with no additional relevance scoring.
Cards show event names, venues, and event-local dates/times where provided;
missing details are labeled unavailable. Loading, empty-result, and request-error
states support retry. This live search is separate from the synthetic itinerary:
it does not check budget or schedule feasibility or add events to a plan.

The page imports the existing synthetic JSON directly from `src/zova/data/`.
Only the budget is editable. Times display in America/New_York regardless of
browser timezone; costs are estimates and nothing is saved or booked.

`src/components/App/App.tsx` composes the page layout, weekend planner, and event search.
`src/components/WeekendPlanner/WeekendPlanner.tsx` owns the budget form, results,
and budget, loading, error, and result state with `useState`.
The form handler uses `fetch('/itinerary')` to POST JSON; Vite forwards that
request to port 8000. No backend CORS change is needed. The returned activities
are rendered with `.map()`, and response money strings are formatted for display.
TypeScript describes the expected itinerary response shape; it does not validate
itinerary JSON at runtime. Event search checks the event-list structure and
provides fallbacks for missing display fields. Python remains responsible for
planner validation and planning.

Frontend source layout (inside `frontend/`):

```text
src/
  components/
    App/
      App.tsx
      App.css
    EventSearch/
      EventSearch.tsx
      EventSearch.css
    WeekendPlanner/
      WeekendPlanner.tsx
      WeekendPlanner.css
    shared/
      PlannerShared.css
  test/
    App.test.tsx
    EventSearch.test.tsx
    WeekendPlanner.test.tsx
  main.tsx
  styles.css
```

Each component has its own named folder under `src/components/`; UI tests live
separately in `src/test/`. Each component imports its matching CSS file.
`WeekendPlanner` and `EventSearch` also import `shared/PlannerShared.css` for
common forms, layouts, and result cards. `main.tsx` mounts the app and imports
the small global `styles.css` for typography, browser defaults, and shared text styles.

Frontend checks (from `frontend/`):

```bash
npm test
npm run build
```

Tests mock fetch and run offline. The build performs TypeScript checks and emits
`frontend/dist/`. The proxy is for local development only; a production host
would need its own API routing. No deployment is configured.

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
paths. API tests cover itinerary generation, fractional costs, empty/infeasible
results, and invalid inputs. No static type checker or CI is configured yet.

## Architecture

- `src/zova/models.py`: Pydantic validation, aware time windows, Decimal money,
  and typed profile/activity/itinerary models.
- `src/zova/fixtures.py` and `src/zova/data/`: packaged JSON loading independent
  of the current working directory.
- `src/zova/planner.py`: `overlaps`, `validate_plan`, and `build_itinerary`.
- `src/zova/cli.py`: display the resulting itinerary.
- `src/zova/api.py`: FastAPI routes, input checks, and HTTP error responses.
- `src/zova/clients/ticketmaster.py`: external event requests without FastAPI dependencies.
- `frontend/`: React page, plain CSS, Vite development proxy, and UI tests.
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

1. Add synthetic travel times and enforce transfer buffers with tests.
2. Explain skipped candidates and which preferences selected stops match.

MVP B (Inbox-to-Itinerary Organizer) and MVP C (Disruption Recovery Copilot)
remain planned. The experimental Ticketmaster fetch is separate from planning.
No LLM, MCP, OAuth, Calendar, Gmail,
storage, or deployment is included.

See [AGENTS.md](AGENTS.md) for ongoing engineering instructions,
[docs/PROJECT_BLUEPRINT.md](docs/PROJECT_BLUEPRINT.md) for long-term requirements,
and [CHANGELOG.md](CHANGELOG.md) for implemented changes.
The `zova_repo_starter` directory preserves starter documents; the root README
and `docs/` are authoritative for current development.
