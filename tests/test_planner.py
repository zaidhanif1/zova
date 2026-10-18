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
    assert main() == 0
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
