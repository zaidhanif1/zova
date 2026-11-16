"""Read-only Ticketmaster requests, independent of the web API."""

from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import httpx

from zova.models import ActivityCandidate

TICKETMASTER_URL = "https://app.ticketmaster.com/discovery/v2/events.json"


async def fetch_ticketmaster_events(
    city: str,
    *,
    api_key: str,
    keyword: str | None = None,
    state_code: str | None = None,
    country_code: str | None = None,
    postal_code: str | None = None,
    radius: float | None = None,
    size: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    """Return a provider JSON object; propagate request and decoding failures."""

    params: dict[str, str | int | float] = {"apikey": api_key, "city": city}

    keyword = (keyword or "").strip()

    if keyword:
        params["keyword"] = keyword

    for name, value in {
        "stateCode": state_code,
        "countryCode": country_code,
        "postalCode": postal_code,
    }.items():
        if value and value.strip():
            params[name] = value.strip()

    if radius is not None:
        params["radius"] = radius

    if size is not None:
        params["size"] = size

    if start_date is not None or end_date is not None:
        if start_date is not None and end_date is not None and start_date > end_date:
            raise ValueError("End date must be on or after start date")

        # These are event-local calendar bounds, not UTC instants. Include the full end day.
        start = f"{start_date.isoformat()}T00:00:00" if start_date is not None else "*"
        end = f"{end_date.isoformat()}T23:59:59" if end_date is not None else "*"
        params["localStartDateTime"] = f"{start},{end}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(TICKETMASTER_URL, params=params)
        response.raise_for_status()
        payload = response.json()

    if not isinstance(payload, dict):
        raise ValueError("Ticketmaster response must be a JSON object")

    return payload


def normalize_ticketmaster_event(event: dict) -> ActivityCandidate:
    """Validate a provider event as a candidate; reject unschedulable events."""

    dates = event.get("dates") or {}
    start = dates.get("start") or {}

    # Reject events that cannot yet be scheduled.

    flags = ("dateTBD", "dateTBA", "timeTBA", "noSpecificTime")

    if any(start.get(flag) for flag in flags):
        raise ValueError("Event has no specific start date/time")

    utc_start = start.get("dateTime")

    venues = (event.get("_embedded") or {}).get("venues") or []
    venue = venues[0] if venues else {}

    timezone = dates.get("timezone") or venue.get("timezone")
    city = (venue.get("city") or {}).get("name")

    if not utc_start or not timezone or not city:
        raise ValueError("Event is missing required fields")

    starts_at = datetime.fromisoformat(utc_start.replace("Z", "+00:00"))
    if starts_at.tzinfo is None:
        raise ValueError("Event start must include a timezone offset")
    starts_at = starts_at.astimezone(ZoneInfo(timezone))

    classification = event.get("classifications") or []
    classification = next(
        (c for c in classification if c.get("primary")),
        classification[0] if classification else {},
    )

    categories = tuple(
        classification[key]["name"]
        for key in ("segment", "genre", "subGenre")
        if (classification.get(key) or {}).get("name") not in (None, "Undefined")
    )

    usd_prices = [
        Decimal(str(p["min"]))
        for p in (event.get("priceRanges") or [])
        if p.get("currency") == "USD" and p.get("min") is not None
    ]

    coords = venue.get("location") or {}

    return ActivityCandidate(
        id=f"ticketmaster:{event['id']}",
        title=event["name"],
        destination=city,
        categories=categories,
        starts_at=starts_at,
        venue_name=venue.get("name"),
        latitude=float(coords["latitude"]) if "latitude" in coords else None,
        longitude=float(coords["longitude"]) if "longitude" in coords else None,
        min_listed_price=min(usd_prices) if usd_prices else None,
        url=event.get("url"),
        status=(dates.get("status") or {}).get("code"),
    )
