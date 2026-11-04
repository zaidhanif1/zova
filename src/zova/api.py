"""Local API for validating synthetic planner inputs; no persistence."""

from fastapi import FastAPI

from zova.models import Activity, Model, TravelerProfile

app = FastAPI(title="Zova API")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


class UploadResponse(Model):
    message: str
    profile: TravelerProfile
    activities: list[Activity]


@app.post("/upload")
def upload_preferences(profile: TravelerProfile, activities: list[Activity]) -> UploadResponse:
    return UploadResponse(
        message="Preferences validated successfully; not stored",
        profile=profile,
        activities=activities,
    )
