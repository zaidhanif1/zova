"""Local API for generating synthetic itineraries; no persistence."""

import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from zova.clients.ticketmaster import fetch_ticketmaster_events
from zova.models import Activity, ItineraryResponse, TravelerProfile
from zova.planner import build_itinerary

# Local development only: read the launch directory, without replacing exported values.
load_dotenv(dotenv_path=Path.cwd() / ".env", override=False)

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


@app.get("/get_events")
async def get_ticketmaster_events(city: str, keyword: str | None = None) -> dict:
    city = city.strip()
    if not city:
        raise HTTPException(status_code=400, detail="City parameter is required")

    api_key = os.environ.get("TICKETMASTER_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=503, detail="Ticketmaster API key is not configured")

    try:
        return await fetch_ticketmaster_events(city, api_key=api_key, keyword=keyword)
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Failed to fetch Ticketmaster events") from None
    except ValueError:
        raise HTTPException(status_code=502, detail="Invalid Ticketmaster response") from None
