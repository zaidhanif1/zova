"""Load packaged, fictional demo inputs without network access."""

from importlib.resources import files

from pydantic import TypeAdapter

from zova.models import Activity, TravelerProfile


def load_demo() -> tuple[TravelerProfile, list[Activity]]:
    """Read the fictional demo files and validate them before planning."""
    # STEP 1: Find the data folder inside the installed zova package.
    data_folder = files("zova").joinpath("data")

    # STEP 2: Read the profile file, then turn its JSON text into a valid profile.
    profile_file = data_folder.joinpath("profile.json")
    profile_json = profile_file.read_text("utf-8")
    profile = TravelerProfile.model_validate_json(profile_json)

    # STEP 3: Read and validate the activities as a list of Activity models.
    activities_file = data_folder.joinpath("activities.json")
    activities_json = activities_file.read_text("utf-8")
    activity_list_validator = TypeAdapter(list[Activity])
    activities = activity_list_validator.validate_json(activities_json)

    return profile, activities
