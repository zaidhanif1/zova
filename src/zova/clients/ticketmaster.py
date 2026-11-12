"""Read-only Ticketmaster requests, independent of the web API."""

import httpx

TICKETMASTER_URL = "https://app.ticketmaster.com/discovery/v2/events.json"


async def fetch_ticketmaster_events(city: str, *, api_key: str) -> dict:
    """Return a provider JSON object; propagate request and decoding failures."""
    params = {"apikey": api_key, "city": city, "size": 20}

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(TICKETMASTER_URL, params=params)
        response.raise_for_status()
        payload = response.json()

    if not isinstance(payload, dict):
        raise ValueError("Ticketmaster response must be a JSON object")

    return payload
