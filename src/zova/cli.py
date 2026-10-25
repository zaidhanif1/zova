"""Console demo; no credentials or services required."""

import argparse
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from zova.fixtures import load_demo
from zova.models import Activity, TravelerProfile
from zova.planner import build_itinerary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a synthetic Zova itinerary.")
    parser.add_argument("--profile", type=Path, help="Path to a traveler profile JSON file.")
    parser.add_argument("--activities", type=Path, help="Path to an activities JSON file.")
    parser.add_argument("--budget", help="Override the profile budget (nonnegative USD amount).")
    parser.add_argument("--name", help="Override user's name.")
    arguments = parser.parse_args(argv)

    try:
        profile, activities = load_demo()
        if arguments.profile is not None:
            profile = TravelerProfile.model_validate_json(arguments.profile.read_text("utf-8"))
        if arguments.activities is not None:
            activities = TypeAdapter(list[Activity]).validate_json(
                arguments.activities.read_text("utf-8")
            )
    except (OSError, UnicodeError, ValidationError) as error:
        parser.error(f"Could not load planner inputs: {error}")

    if arguments.budget is not None:
        # Revalidate a new profile because the original is frozen. Pydantic converts
        # the text to Decimal and enforces the same money rules as JSON inputs.
        profile_values = profile.model_dump()
        profile_values["budget"] = arguments.budget

    if arguments.name:
        profile_values = profile.model_dump()
        profile_values["name"] = arguments.name

        try:
            profile = TravelerProfile.model_validate(profile_values)
        except ValidationError:
            parser.error(
                "--budget must be a finite, nonnegative amount with at most "
                "2 decimal places and at most 10 digits before the decimal point."
            )

    plan = build_itinerary(profile, activities)

    print(f"Zova | SYNTHETIC DATA | {profile.destination} | fictional traveler: {profile.name}")

    for block in profile.unavailable:
        print(f"Unavailable: {block.start} to {block.end}")

    for activity in plan.activities:
        print(
            f"{activity.schedule.start.isoformat()} to {activity.schedule.end.isoformat()}"
            f" | {activity.title} | {activity.cost:.2f} {activity.currency}"
        )

    if not plan.activities:
        print("No feasible activities found within the supplied constraints.")

    print(f"Estimated total: {plan.total_cost:.2f} / {profile.budget:.2f} {profile.currency}")
    print("Budget covers listed activities only; excludes lodging, transport, taxes, and tips.")

    return 0
