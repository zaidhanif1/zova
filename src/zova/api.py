"""Local API for generating synthetic itineraries; no persistence."""

import os
from datetime import date
from pathlib import Path
from typing import Annotated

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query

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
async def get_ticketmaster_events(
    city: str,
    keyword: str | None = None,
    state_code: Annotated[str | None, Query(alias="stateCode")] = None,
    country_code: Annotated[str | None, Query(alias="countryCode")] = None,
    postal_code: Annotated[str | None, Query(alias="postalCode")] = None,
    radius: Annotated[float | None, Query(ge=0, allow_inf_nan=False)] = None,
    size: Annotated[int | None, Query(gt=0)] = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    city = city.strip()
    if not city:
        raise HTTPException(status_code=400, detail="City parameter is required")

    if start_date is not None and end_date is not None and start_date > end_date:
        raise HTTPException(status_code=422, detail="End date must be on or after start date")

    api_key = os.environ.get("TICKETMASTER_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=503, detail="Ticketmaster API key is not configured")

    try:
        filters = {
            "state_code": state_code,
            "country_code": country_code,
            "postal_code": postal_code,
            "radius": radius,
            "size": size,
            "start_date": start_date,
            "end_date": end_date,
        }
        results = await fetch_ticketmaster_events(
            city,
            api_key=api_key,
            keyword=keyword,
            **{name: value for name, value in filters.items() if value is not None},
        )

        # Local development diagnostic: inspect the first provider event.
        events = results.get("_embedded", {}).get("events", [])
        first_event = events[:1]

        print(first_event)
        return results
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Failed to fetch Ticketmaster events") from None
    except ValueError:
        raise HTTPException(status_code=502, detail="Invalid Ticketmaster response") from None
