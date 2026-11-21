"""Read-only Ticketmaster requests, independent of the web API."""

from datetime import date

import httpx

TICKETMASTER_URL = "https://app.ticketmaster.com/discovery/v2/events.json"


async def fetch_ticketmaster_events(
    city: str,
    **kwargs,
) -> dict:
    """Return a provider JSON object; propagate request and decoding failures."""

    params: dict[str, str | int | float] = {
        "apikey": kwargs.get("api_key"),
        "city": city
        }

    
    keyword = (kwargs.get("keyword") or "").strip()
    
    if keyword:
        params["keyword"] = keyword

    for name, value in {
        "stateCode": kwargs.get("state_code"),
        "countryCode": kwargs.get("country_code"),
        "postalCode": kwargs.get("postal_code"),
    }.items():
        
        if value and value.strip():
            params[name] = value.strip()

    if kwargs.get("radius") is not None:
        params["radius"] = kwargs.get("radius")

    if kwargs.get("size") is not None:
        params["size"] = kwargs.get("size")

    if kwargs.get("start_date") is not None or kwargs.get("end_date") is not None:
        if kwargs.get("start_date") is not None and kwargs.get("end_date") is not None and kwargs.get("start_date") > kwargs.get("end_date"):
            raise ValueError("End date must be on or after start date")

        # These are event-local calendar bounds, not UTC instants. Include the full end day.
        start = f"{kwargs.get('start_date').isoformat()}T00:00:00" if kwargs.get("start_date") is not None else "*"
        end = f"{kwargs.get('end_date').isoformat()}T23:59:59" if kwargs.get("end_date") is not None else "*"
        params["localStartDateTime"] = f"{start},{end}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(TICKETMASTER_URL, params=params)
        response.raise_for_status()
        payload = response.json()

    if not isinstance(payload, dict):
        raise ValueError("Ticketmaster response must be a JSON object")

    return payload
