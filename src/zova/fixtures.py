"""Load packaged, fictional demo inputs without network access."""

from importlib.resources import files

from pydantic import TypeAdapter

from zova.models import Activity, TravelerProfile


def load_demo() -> tuple[TravelerProfile, list[Activity]]:
    data = files("zova").joinpath("data")
    profile = TravelerProfile.model_validate_json(data.joinpath("profile.json").read_text("utf-8"))
    activities = TypeAdapter(list[Activity]).validate_json(
        data.joinpath("activities.json").read_text("utf-8")
    )
    return profile, activities
