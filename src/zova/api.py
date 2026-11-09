"""Local API for generating synthetic itineraries; no persistence."""

import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from zova.models import Activity, ItineraryResponse, TravelerProfile
from zova.planner import build_itinerary

# Local development only: read the launch directory, without replacing exported values.
load_dotenv(dotenv_path=Path.cwd() / ".env", override=False)

app = FastAPI(title="Zova API")


TICKETMASTER_URL = "https://app.ticketmaster.com/discovery/v2/events.json"


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


async def get_ticketmaster_events(city: str) -> dict:
    try:
        events = await fetch_ticketmaster_events(city)
        return events

    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Failed to fetch Ticketmaster events")


@app.get("/get_events")
async def fetch_ticketmaster_events(city: str) -> dict:
    api_key = os.environ.get("TICKETMASTER_API_KEY", "").strip()
    
    if not api_key:
        raise HTTPException(status_code=503, detail="Ticketmaster API key is not configured")

    params = {"apikey": api_key, "city": city, "size": 20}

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(TICKETMASTER_URL, params=params)

        # Raise for unsuccessful HTTP status codes (4xx or 5xx).
        response.raise_for_status()

        return response.json()  # parses the json response into a python object (dict)
