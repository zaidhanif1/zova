"""Console demo; no credentials or services required."""

from zova.fixtures import load_demo
from zova.planner import build_itinerary


def main() -> int:
    profile, activities = load_demo()
    plan = build_itinerary(profile, activities)
    print(f"Zova | {profile.destination} | fictional traveler: {profile.name}")
    print("SYNTHETIC DATA: fixed sessions and estimated costs; no live availability.")
    print("Times include UTC offsets. Travel times are not modeled.")
    for block in profile.unavailable:
        print(f"Unavailable: {block.start.isoformat()} to {block.end.isoformat()}")
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
