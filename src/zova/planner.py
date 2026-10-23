"""Greedy selection with an independent hard-constraint validation boundary."""

from collections.abc import Sequence
from datetime import datetime

from zova.models import Activity, Itinerary, TimeWindow, TravelerProfile


class PlanViolation(ValueError):
    """A proposed itinerary violates a hard constraint."""


def overlaps(left: TimeWindow, right: TimeWindow) -> bool:
    """Check whether two time windows share any time."""
    # A session ending exactly when another starts is allowed.
    if left.end <= right.start:
        return False

    if right.end <= left.start:
        return False

    return True


def validate_plan(profile: TravelerProfile, plan: Itinerary) -> None:
    """Raise PlanViolation when a plan breaks a rule; otherwise return normally."""
    # STEP 1: Check the total estimated cost.
    if plan.total_cost > profile.budget:
        raise PlanViolation("Plan exceeds budget")

    # STEP 2: Work through a chronological copy of the activities.
    def get_start_time(activity: Activity) -> datetime:
        return activity.schedule.start

    ordered_activities = sorted(plan.activities, key=get_start_time)
    seen_activity_ids: set[str] = set()
    previous_activity: Activity | None = None

    for activity in ordered_activities:
        # STEP 3: Reject repeated activities or a different destination/currency.
        if activity.id in seen_activity_ids:
            raise PlanViolation("Duplicate activity")
        seen_activity_ids.add(activity.id)

        if activity.destination != profile.destination or activity.currency != profile.currency:
            raise PlanViolation("Destination or currency mismatch")

        # STEP 4: Keep the session inside the trip's time window.
        if activity.schedule.start < profile.trip.start or activity.schedule.end > profile.trip.end:
            raise PlanViolation("Activity outside trip window")

        # STEP 5: Protect every unavailable time window.
        for unavailable_window in profile.unavailable:
            if overlaps(activity.schedule, unavailable_window):
                raise PlanViolation("Activity overlaps unavailable time")

        # STEP 6: Compare with the previous session in chronological order.
        # If an earlier pair overlapped, we would already have raised an error.
        if previous_activity is not None:
            if overlaps(previous_activity.schedule, activity.schedule):
                raise PlanViolation("Activities overlap")

        previous_activity = activity


def build_itinerary(profile: TravelerProfile, activities: Sequence[Activity]) -> Itinerary:
    """Try activities in preference order, keeping only valid additions.

    This greedy approach is repeatable, but may not find the best possible plan.
    """
    # STEP 1: Store the traveler's preferences in lowercase.
    traveler_preferences: set[str] = set()

    for preference in profile.preferences:
        traveler_preferences.add(preference.casefold())

    # STEP 2: Define how we count matching interests.
    def count_matches(activity: Activity) -> int:
        # A set counts each matching category once, even if it is repeated.
        matching_categories: set[str] = set()

        for category in activity.categories:
            category = category.casefold()

            if category in traveler_preferences:
                matching_categories.add(category)

        return len(matching_categories)

    # STEP 3: Define two simple sorting helpers.
    def get_start_time(activity: Activity) -> datetime:
        return activity.schedule.start

    def get_id(activity: Activity) -> str:
        return activity.id

    # STEP 4: Rank all activities.
    ranked_activities = list(activities)

    # Python keeps the previous order when sorting values that tie.
    # Sort the least important rule first and the most important rule last.
    # Sort by ID first (final tie-breaker).
    ranked_activities.sort(key=get_id)

    # Then sort by start time (earlier first).
    ranked_activities.sort(key=get_start_time)

    # Finally, prioritize activities matching more interests.
    ranked_activities.sort(key=count_matches, reverse=True)

    # STEP 5: Start with an empty list of accepted activities.
    accepted_activities: list[Activity] = []

    for activity in ranked_activities:
        # Make a copy of everything we have accepted.
        candidate_activities = accepted_activities.copy()

        # Try including the new activity.
        candidate_activities.append(activity)

        # Convert the list into an Itinerary.
        candidate_plan = Itinerary(activities=tuple(candidate_activities))

        # Check whether this itinerary is allowed.
        try:
            validate_plan(profile, candidate_plan)

        except PlanViolation:
            # Invalid activity. Skip it.
            continue

        # Valid activity. Keep it.
        accepted_activities.append(activity)

    # STEP 6: Put accepted activities in chronological order.
    accepted_activities.sort(key=get_start_time)

    # Create the final itinerary.
    final_plan = Itinerary(activities=tuple(accepted_activities))

    # Make sure the final itinerary is valid.
    validate_plan(profile, final_plan)

    return final_plan
