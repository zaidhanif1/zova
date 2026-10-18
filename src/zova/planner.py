"""Greedy selection with an independent hard-constraint validation boundary."""

from collections.abc import Sequence

from zova.models import Activity, Itinerary, TimeWindow, TravelerProfile


class PlanViolation(ValueError):
    """A proposed itinerary violates a hard constraint."""


def overlaps(left: TimeWindow, right: TimeWindow) -> bool:
    """Half-open intervals allow one session to start when another ends."""
    return left.start < right.end and right.start < left.end


def validate_plan(profile: TravelerProfile, plan: Itinerary) -> None:
    if plan.total_cost > profile.budget:
        raise PlanViolation("Plan exceeds budget")
    seen: set[str] = set()
    ordered = sorted(plan.activities, key=lambda activity: activity.schedule.start)
    for index, activity in enumerate(ordered):
        if activity.id in seen:
            raise PlanViolation("Duplicate activity")
        seen.add(activity.id)
        if activity.destination != profile.destination or activity.currency != profile.currency:
            raise PlanViolation("Destination or currency mismatch")
        if activity.schedule.start < profile.trip.start or activity.schedule.end > profile.trip.end:
            raise PlanViolation("Activity outside trip window")
        if any(overlaps(activity.schedule, block) for block in profile.unavailable):
            raise PlanViolation("Activity overlaps unavailable time")
        if index and overlaps(ordered[index - 1].schedule, activity.schedule):
            raise PlanViolation("Activities overlap")


def build_itinerary(profile: TravelerProfile, activities: Sequence[Activity]) -> Itinerary:
    """Prefer more matching interests, then earlier sessions, then stable IDs.

    Skip infeasible additions. This heuristic does not promise an optimal plan.
    """
    preferences = {value.casefold() for value in profile.preferences}
    ranked = sorted(
        activities,
        key=lambda activity: (
            -len(preferences & {value.casefold() for value in activity.categories}),
            activity.schedule.start,
            activity.id,
        ),
    )
    plan = Itinerary(activities=())
    for activity in ranked:
        proposal = Itinerary(activities=(*plan.activities, activity))
        try:
            validate_plan(profile, proposal)
        except PlanViolation:
            continue
        plan = proposal
    plan = Itinerary(activities=tuple(sorted(plan.activities, key=lambda a: a.schedule.start)))
    validate_plan(profile, plan)
    return plan
