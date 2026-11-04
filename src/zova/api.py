"""Local API for generating synthetic itineraries; no persistence."""

from fastapi import FastAPI

from zova.models import Activity, ItineraryResponse, TravelerProfile
from zova.planner import build_itinerary

app = FastAPI(title="Zova API")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/itinerary")
def post_itinerary(profile: TravelerProfile, activities: list[Activity]) -> ItineraryResponse:
    plan = build_itinerary(profile, activities)
    return ItineraryResponse(
        message="Successfully generated itinerary tailored to user profile and given activities.",
        total_cost=plan.total_cost,
        profile=profile,
        activities=plan.activities,
    )
