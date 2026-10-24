import subprocess
import sys
from decimal import Decimal

import pytest
from pydantic import ValidationError

from zova.cli import main
from zova.fixtures import load_demo
from zova.models import Activity, Itinerary, TimeWindow, TravelerProfile
from zova.planner import PlanViolation, build_itinerary, overlaps, validate_plan


def profile_with(**changes: object) -> TravelerProfile:
    profile, _ = load_demo()
    return TravelerProfile.model_validate(profile.model_dump() | changes)


def test_valid_demo_is_deterministic_and_filters_invalid_candidates():
    profile, activities = load_demo()
    plan = build_itinerary(profile, activities)
    validate_plan(profile, plan)
    assert [a.id for a in plan.activities] == [
        "architecture-walk",
        "thrift-session",
        "food-stop",
        "gallery",
    ]
    assert plan.total_cost == Decimal("55.00")
    assert build_itinerary(profile, list(reversed(activities))) == plan
    assert profile.unavailable == load_demo()[0].unavailable


def test_budget_violation_rejected():
    _, activities = load_demo()
    with pytest.raises(PlanViolation, match="budget"):
        validate_plan(profile_with(budget="19.99"), Itinerary(activities=(activities[0],)))


def test_blocked_time_rejected():
    profile, activities = load_demo()
    with pytest.raises(PlanViolation, match="unavailable"):
        validate_plan(profile, Itinerary(activities=(activities[3],)))


def test_activity_overlap_rejected():
    profile, activities = load_demo()
    with pytest.raises(PlanViolation, match="Activities overlap"):
        validate_plan(profile, Itinerary(activities=(activities[0], activities[6])))


def test_exact_budget_and_touching_boundaries_allowed():
    _, activities = load_demo()
    plan = Itinerary(activities=(activities[1], activities[2], activities[4]))
    validate_plan(profile_with(budget="35.00"), plan)


@pytest.mark.parametrize("budget", ["0.00", "10.00", "30.00", "60.00"])
def test_reduced_budgets_remain_valid(budget):
    _, activities = load_demo()
    profile = profile_with(budget=budget)
    plan = build_itinerary(profile, activities)
    validate_plan(profile, plan)
    assert plan.total_cost <= Decimal(budget)


def test_empty_candidates():
    profile, _ = load_demo()
    assert build_itinerary(profile, []).activities == ()


@pytest.mark.parametrize(
    "preferred_categories,preferred_start,preferred_end,preferred_id",
    [
        # More distinct interests win, even with a later start and a later ID.
        (("ARCHITECTURE", "thrift"), "10:00", "11:30", "z-preferred"),
        # With equal interest counts, an earlier start wins before ID is considered.
        (("architecture",), "08:00", "09:30", "z-preferred"),
        # With equal interests and start times, the smaller ID wins.
        (("architecture",), "09:00", "10:30", "a-preferred"),
    ],
)
def test_ranking_priorities(preferred_categories, preferred_start, preferred_end, preferred_id):
    _, demo_activities = load_demo()
    profile = profile_with(
        budget="20.00",
        preferences=["architecture", "THRIFT"],
        trip={"start": "2026-10-24T08:00:00-04:00", "end": "2026-10-24T18:00:00-04:00"},
    )

    # Both candidates cost $20, so only the higher-ranked one can fit.
    other_data = demo_activities[0].model_dump()
    other_data["id"] = "m-other"
    other_activity = Activity.model_validate(other_data)

    preferred_data = other_activity.model_dump()
    preferred_data["id"] = preferred_id
    preferred_data["categories"] = preferred_categories
    preferred_data["schedule"] = {
        "start": f"2026-10-24T{preferred_start}:00-04:00",
        "end": f"2026-10-24T{preferred_end}:00-04:00",
    }
    preferred_activity = Activity.model_validate(preferred_data)

    candidates = [other_activity, preferred_activity]
    plan = build_itinerary(profile, candidates)

    assert plan.activities == (preferred_activity,)
    assert plan.total_cost == Decimal("20.00")
    assert candidates == [other_activity, preferred_activity]
    assert build_itinerary(profile, list(reversed(candidates))) == plan


def test_duplicate_category_labels_do_not_increase_priority():
    _, demo_activities = load_demo()
    profile = profile_with(budget="20.00", preferences=["architecture"])

    ordinary_data = demo_activities[0].model_dump()
    ordinary_data["id"] = "a-ordinary"
    ordinary_activity = Activity.model_validate(ordinary_data)

    repeated_data = ordinary_activity.model_dump()
    repeated_data["id"] = "z-repeated"
    repeated_data["categories"] = ["architecture", "ARCHITECTURE", "architecture"]
    repeated_activity = Activity.model_validate(repeated_data)

    plan = build_itinerary(profile, [repeated_activity, ordinary_activity])

    assert plan.activities == (ordinary_activity,)


def test_empty_itinerary_cost_is_decimal_zero():
    plan = Itinerary(activities=())

    assert plan.total_cost == Decimal("0.00")
    assert isinstance(plan.total_cost, Decimal)


@pytest.mark.parametrize(
    "change, message",
    [
        ({"destination": "Boston"}, "Destination"),
        (
            {"trip": {"start": "2026-10-24T10:00:00-04:00", "end": "2026-10-24T18:00:00-04:00"}},
            "outside",
        ),
    ],
)
def test_destination_and_trip_constraints(change, message):
    _, activities = load_demo()
    with pytest.raises(PlanViolation, match=message):
        validate_plan(profile_with(**change), Itinerary(activities=(activities[0],)))


def test_duplicate_rejected():
    profile, activities = load_demo()
    with pytest.raises(PlanViolation, match="Duplicate"):
        validate_plan(profile, Itinerary(activities=(activities[0], activities[0])))


@pytest.mark.parametrize(
    "start,end",
    [
        ("2026-10-24T09:00:00", "2026-10-24T10:00:00"),
        ("2026-10-24T10:00:00-04:00", "2026-10-24T09:00:00-04:00"),
        ("2026-10-24T09:00:00-04:00", "2026-10-24T09:00:00-04:00"),
    ],
)
def test_invalid_windows(start, end):
    with pytest.raises(ValidationError):
        TimeWindow(start=start, end=end)


@pytest.mark.parametrize(
    "changes",
    [{"cost": "-1"}, {"duration_minutes": 0}, {"duration_minutes": 5}, {"currency": "EUR"}],
)
def test_malformed_activity_rejected(changes):
    _, activities = load_demo()
    with pytest.raises(ValidationError):
        Activity.model_validate(activities[0].model_dump() | changes)


def test_timezone_offsets_compare_as_instants():
    first = TimeWindow(start="2026-10-24T09:00:00-04:00", end="2026-10-24T10:00:00-04:00")
    same = TimeWindow(start="2026-10-24T13:00:00+00:00", end="2026-10-24T14:00:00+00:00")
    assert overlaps(first, same)


def test_cli(capsys):
    assert main([]) == 0
    output = capsys.readouterr().out
    assert "SYNTHETIC DATA" in output
    assert "55.00 / 60.00 USD" in output
    assert "Synthetic afternoon architecture tour" not in output


def test_module_entrypoint():
    result = subprocess.run([sys.executable, "-m", "zova"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "55.00 / 60.00 USD" in result.stdout


def test_invalid_profile_budget():
    with pytest.raises(ValidationError):
        profile_with(budget="-1")
