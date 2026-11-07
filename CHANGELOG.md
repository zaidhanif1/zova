# Changelog

All notable user-facing changes to Zova will be documented here.

Format inspired by [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions will use [Semantic Versioning](https://semver.org/) when releases begin.

## [Unreleased]

### Added
- Responsive Zova welcome landing page with an original city illustration,
  demo walkthrough, and direct links to the existing weekend planner.
- Local React/TypeScript/Vite weekend planner interface with editable budget,
  itinerary times and costs, and loading, error, and empty-result states.
- Local FastAPI health and input-validation endpoints, declared FastAPI/Uvicorn
  dependencies, API tests, and server setup instructions.
- Optional CLI profile/activity JSON paths and a validated budget override that
  leaves the source profile unchanged; invalid inputs produce command-line errors.
- Offline `zova` / `python -m zova` CLI with a fictional traveler and seven synthetic activities.
- Typed inputs and deterministic interest-based selection with budget, blocked-time,
  activity-overlap, trip-window, destination, and duplicate checks.
- Offline planner, malformed-input, timezone, and CLI tests.

### Changed
- Replace the validation-only `/upload` endpoint with `POST /itinerary`, returning
  selected synthetic activities and an exact estimated total without persistence.
- Adopted the official Zova identity and `zova` Python package name.
- Established the workspace root as the runnable project with setup and test instructions.

### Fixed
- Correct API model imports to use the installed `zova` package; remove input logging.
- Apply CLI budget overrides even without a name override, and preserve both together.
- Label CLI output as synthetic and omit temporary candidate-plan debug output.

### Documentation
- Established the three-MVP project blueprint, starter README, and Codex contribution instructions.

<!-- When user-facing functionality exists, use concise Added / Changed / Fixed / Security entries. -->
<!-- Example future release:
## [0.1.0] - YYYY-MM-DD
### Added
- Synthetic weekend planner with constraint checking and a local demo.
-->
