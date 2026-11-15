"""Read-only Ticketmaster requests, independent of the web API."""

from datetime import date

import httpx

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
