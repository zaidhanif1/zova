from decimal import Decimal

import pytest

from zova.cli import main
from zova.fixtures import load_demo
from zova.models import Itinerary, TravelerProfile
from zova.planner import validate_plan


@pytest.mark.parametrize("budget", [None, "100", "30.00", "0"])
def test_budget_with_custom_files(budget, tmp_path, capsys, monkeypatch):
    profile, activities = load_demo()
    profile_values = profile.model_dump()
    profile_values["budget"] = Decimal("40.00")
    profile = TravelerProfile.model_validate(profile_values)
    profile_path = tmp_path / "profile.json"
    activities_path = tmp_path / "activities.json"
    original_profile_json = profile.model_dump_json()
    profile_path.write_text(original_profile_json, encoding="utf-8")
    activities_path.write_text(
        "[" + ",".join(activity.model_dump_json() for activity in activities) + "]",
        encoding="utf-8",
    )
    arguments = ["--profile", str(profile_path), "--activities", str(activities_path)]
    if budget is not None:
        arguments.extend(["--budget", budget])

    # Capture the actual planner result while still running the real planner.
    from zova.planner import build_itinerary

    built_plans: list[Itinerary] = []

    def capture_plan(planner_profile, planner_activities):
        expected_budget = Decimal("40.00") if budget is None else Decimal(budget)
        assert planner_profile.budget == expected_budget
        plan = build_itinerary(planner_profile, planner_activities)
        validate_plan(planner_profile, plan)
        assert plan.total_cost <= expected_budget
        built_plans.append(plan)
        return plan

    monkeypatch.setattr("zova.cli.build_itinerary", capture_plan)
    assert main(arguments) == 0
    expected_budget = Decimal("40.00") if budget is None else Decimal(budget)
    assert f"/ {expected_budget:.2f} USD" in capsys.readouterr().out
    assert len(built_plans) == 1
    assert profile_path.read_text("utf-8") == original_profile_json


def test_budget_override_with_packaged_demo(capsys):
    assert main(["--budget", "30"]) == 0
    assert "Estimated total: 30.00 / 30.00 USD" in capsys.readouterr().out
    assert load_demo()[0].budget == Decimal("60.00")


@pytest.mark.parametrize("budget", ["-1", "invalid", "NaN", "inf", "1.001", "10000000000"])
def test_invalid_budget(budget, capsys):
    with pytest.raises(SystemExit) as error:
        main(["--budget", budget])
    assert error.value.code == 2
    assert "--budget must be a finite, nonnegative amount" in capsys.readouterr().err


@pytest.mark.parametrize("contents", [None, "not JSON", "{}"])
def test_invalid_profile_file(contents, tmp_path, capsys):
    profile_path = tmp_path / "profile.json"
    if contents is not None:
        profile_path.write_text(contents, encoding="utf-8")
    with pytest.raises(SystemExit) as error:
        main(["--profile", str(profile_path)])
    assert error.value.code == 2
    assert "Could not load planner inputs" in capsys.readouterr().err
