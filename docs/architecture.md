# First slice: deterministic planning

Data flows from packaged JSON through Pydantic models, into `build_itinerary`,
through `validate_plan`, and finally to the CLI. The planner never calls a
network service or changes the traveler profile.

`build_itinerary` sorts activities by interest-match count, start time, and ID.
Each addition creates a proposed itinerary. `validate_plan` either returns
normally or raises `PlanViolation`; rejected additions are skipped. The total
is computed from activities rather than accepted as a separate input.

The independent validator is the key learning point: selecting a desirable
activity and proving a plan is allowed are separate responsibilities. A future
agent can suggest activities without becoming the authority on feasibility.

Fixed sessions keep this first milestone small. Duration must exactly equal the
session length. There is no flexible opening-hour scheduling or route model.
Aware timestamps compare actual instants; Decimal represents money; half-open
intervals allow back-to-back stops. The interest-first greedy heuristic may
miss a better overall combination.

Next blocker: geographic feasibility needs synthetic transfer estimates and
tests before any claim that the schedule allows enough travel time.
