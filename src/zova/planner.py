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

    # Convert the traveler's preferences into a set of lowercase strings
    # so comparisons are case-insensitive.
    preferences = {value.casefold() for value in profile.preferences}

    # Rank activities by:
    # 1. Number of matching preferences (more matches = higher priority)
    # 2. Earlier start time if preference matches are equal
    # 3. Activity ID as a deterministic tie-breaker
    ranked = sorted(
        activities,
        key=lambda activity: (
            -len(preferences & {value.casefold() for value in activity.categories}),
            activity.schedule.start,
            activity.id,
        ),
    )

    # Initialize an empty itinerary containing zero activities.
    plan = Itinerary(activities=())

    # Consider each activity in order of preference ranking.
    for activity in ranked:

        # Create a temporary itinerary containing all previously accepted
        # activities PLUS the new activity we're considering.
        #
        # *plan.activities unpacks the existing activities into a new tuple.
        # We do NOT modify the actual plan yet.
        proposal = Itinerary(activities=(*plan.activities, activity))

        try:
            # Check whether adding this activity violates any constraints
            # enforced by validate_plan (e.g., overlapping time slots or budget).
            validate_plan(profile, proposal)

        except PlanViolation:
            # If the proposal violates a constraint, reject this activity.
            # 'continue' skips the remaining code in this iteration
            # and moves to the next activity in ranked.
            continue

        # If validation succeeded, permanently accept the proposal.
        # The proposed itinerary becomes our new current itinerary.
        plan = proposal

    # The activities were originally processed by preference ranking,
    # so reorder the accepted activities chronologically by start time.
    # Convert the sorted list back into a tuple.
    plan = Itinerary(
        activities=tuple(
            sorted(plan.activities, key=lambda a: a.schedule.start)
        )
    )

    # Perform one final validation of the complete itinerary.
    validate_plan(profile, plan)

    # Return the completed itinerary containing all accepted activities.
    return plan
