"""Offline tests for the provider client and its HTTP route."""

import asyncio
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from zova.api import app
from zova.clients.ticketmaster import TICKETMASTER_URL, fetch_ticketmaster_events


def test_client_requests_events():
    payload = {"_embedded": {"events": [{"name": "Synthetic event"}]}}
    response = httpx.Response(200, json=payload, request=httpx.Request("GET", TICKETMASTER_URL))
    with patch("zova.clients.ticketmaster.httpx.AsyncClient") as factory:
        client = factory.return_value.__aenter__.return_value
        client.get = AsyncMock(return_value=response)
        assert asyncio.run(fetch_ticketmaster_events("Boston", api_key="fixture-key")) == payload
        factory.assert_called_once_with(timeout=10.0)
        client.get.assert_awaited_once_with(
            TICKETMASTER_URL, params={"apikey": "fixture-key", "city": "Boston"}
        )


@pytest.mark.parametrize("failure", ["timeout", "http", "json", "shape"])
def test_client_propagates_failures(failure):
    request = httpx.Request("GET", TICKETMASTER_URL)
    response = httpx.Response(
        503 if failure == "http" else 200,
        content=b"invalid" if failure == "json" else b"[]",
        request=request,
    )
    with patch("zova.clients.ticketmaster.httpx.AsyncClient") as factory:
        client = factory.return_value.__aenter__.return_value
        client.get = AsyncMock(return_value=response)
        if failure == "timeout":
            client.get.side_effect = httpx.ReadTimeout("Synthetic timeout")
        with pytest.raises(httpx.HTTPError if failure in ("timeout", "http") else ValueError):
            asyncio.run(fetch_ticketmaster_events("Boston", api_key="fixture-key"))


def get_events(params):
    async def request():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            return await client.get("/get_events", params=params)

    return asyncio.run(request())


def test_route_calls_client(monkeypatch):
    monkeypatch.setenv("TICKETMASTER_API_KEY", " fixture-key ")
    payload = {"_embedded": {"events": []}}
    with patch("zova.api.fetch_ticketmaster_events", new_callable=AsyncMock) as fetch:
        fetch.return_value = payload
        response = get_events({"city": " Boston "})
        assert response.status_code == 200
        assert response.json() == payload
        fetch.assert_awaited_once_with("Boston", api_key="fixture-key", keyword=None)


@pytest.mark.parametrize(
    ("params", "key", "status"),
    [
        ({}, "fixture-key", 422),
        ({"city": "   "}, "fixture-key", 400),
        ({"city": "Boston"}, "", 503),
    ],
)
def test_route_rejects_invalid_requests(monkeypatch, params, key, status):
    monkeypatch.setenv("TICKETMASTER_API_KEY", key)
    with patch("zova.api.fetch_ticketmaster_events", new_callable=AsyncMock) as fetch:
        assert get_events(params).status_code == status
        fetch.assert_not_awaited()


@pytest.mark.parametrize(
    "error", [httpx.ReadTimeout("Synthetic timeout"), ValueError("Synthetic invalid JSON")]
)
def test_route_maps_provider_failures(monkeypatch, error):
    monkeypatch.setenv("TICKETMASTER_API_KEY", "fixture-key")
    with patch("zova.api.fetch_ticketmaster_events", new_callable=AsyncMock) as fetch:
        fetch.side_effect = error
        response = get_events({"city": "Boston"})
        assert response.status_code == 502
        assert "fixture-key" not in response.text


@pytest.mark.parametrize("keyword", [None, "", "   ", "  jazz & blues  "])
def test_client_optional_keyword(keyword):
    response = httpx.Response(200, json={}, request=httpx.Request("GET", TICKETMASTER_URL))
    with patch("zova.clients.ticketmaster.httpx.AsyncClient") as factory:
        client = factory.return_value.__aenter__.return_value
        client.get = AsyncMock(return_value=response)
        asyncio.run(fetch_ticketmaster_events("Boston", api_key="fixture-key", keyword=keyword))
        params = {"apikey": "fixture-key", "city": "Boston"}
        if keyword and keyword.strip():
            params["keyword"] = "jazz & blues"
        client.get.assert_awaited_once_with(TICKETMASTER_URL, params=params)


def test_route_forwards_keyword(monkeypatch):
    monkeypatch.setenv("TICKETMASTER_API_KEY", "fixture-key")
    with patch("zova.api.fetch_ticketmaster_events", new_callable=AsyncMock) as fetch:
        fetch.return_value = {}
        response = get_events({"city": "Boston", "keyword": "jazz & blues"})
        assert response.status_code == 200
        fetch.assert_awaited_once_with("Boston", api_key="fixture-key", keyword="jazz & blues")


def test_optional_filters_flow_to_provider(monkeypatch):
    monkeypatch.setenv("TICKETMASTER_API_KEY", "fixture-key")
    response = httpx.Response(200, json={}, request=httpx.Request("GET", TICKETMASTER_URL))
    # Patch only the provider transport, leaving the ASGI route/client path real.
    with patch("zova.clients.ticketmaster.httpx.AsyncClient.get", new_callable=AsyncMock) as get:
        get.return_value = response

        # ASGI requests also use AsyncClient.get, so invoke the route via request instead.
        async def request():
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                return await client.request(
                    "GET",
                    "/get_events",
                    params={
                        "city": "Boston",
                        "stateCode": " NY ",
                        "countryCode": " US ",
                        "postalCode": " 10001 ",
                        "radius": "0",
                        "size": "7",
                    },
                )

        assert asyncio.run(request()).status_code == 200
        get.assert_awaited_once_with(
            TICKETMASTER_URL,
            params={
                "apikey": "fixture-key",
                "city": "Boston",
                "stateCode": "NY",
                "countryCode": "US",
                "postalCode": "10001",
                "radius": 0.0,
                "size": 7,
            },
        )


@pytest.mark.parametrize(
    "params",
    [
        {"radius": "-1"},
        {"radius": "nan"},
        {"radius": "inf"},
        {"radius": "bad"},
        {"size": "0"},
        {"size": "-1"},
        {"size": "1.5"},
    ],
)
def test_route_rejects_invalid_numeric_filters(params):
    with patch("zova.api.fetch_ticketmaster_events", new_callable=AsyncMock) as fetch:
        assert get_events({"city": "Boston", **params}).status_code == 422
        fetch.assert_not_awaited()


def test_client_omits_blank_location_filters():
    response = httpx.Response(200, json={}, request=httpx.Request("GET", TICKETMASTER_URL))
    with patch("zova.clients.ticketmaster.httpx.AsyncClient") as factory:
        client = factory.return_value.__aenter__.return_value
        client.get = AsyncMock(return_value=response)
        asyncio.run(
            fetch_ticketmaster_events(
                "Boston", api_key="fixture-key", state_code=" ", country_code="", postal_code="  "
            )
        )
        client.get.assert_awaited_once_with(
            TICKETMASTER_URL, params={"apikey": "fixture-key", "city": "Boston"}
        )


@pytest.mark.parametrize(
    ("dates", "expected_range"),
    [
        (
            {"start_date": "2026-12-01", "end_date": "2026-12-05"},
            "2026-12-01T00:00:00,2026-12-05T23:59:59",
        ),
        (
            {"start_date": "2026-12-01", "end_date": "2026-12-01"},
            "2026-12-01T00:00:00,2026-12-01T23:59:59",
        ),
        ({"start_date": "2026-12-01"}, "2026-12-01T00:00:00,*"),
        ({"end_date": "2026-12-05"}, "*,2026-12-05T23:59:59"),
    ],
)
def test_route_forwards_event_local_dates(monkeypatch, dates, expected_range):
    monkeypatch.setenv("TICKETMASTER_API_KEY", "fixture-key")
    response = httpx.Response(200, json={}, request=httpx.Request("GET", TICKETMASTER_URL))
    with patch("zova.clients.ticketmaster.httpx.AsyncClient.get", new_callable=AsyncMock) as get:
        get.return_value = response

        async def request():
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                return await client.request(
                    "GET", "/get_events", params={"city": "Boston", **dates}
                )

        assert asyncio.run(request()).status_code == 200
        get.assert_awaited_once_with(
            TICKETMASTER_URL,
            params={
                "apikey": "fixture-key",
                "city": "Boston",
                "localStartDateTime": expected_range,
            },
        )


@pytest.mark.parametrize(
    "dates",
    [
        {"start_date": "invalid"},
        {"end_date": "2026-02-30"},
        {"start_date": "2026-12-05", "end_date": "2026-12-01"},
        {"start_date": ""},
    ],
)
def test_route_rejects_invalid_dates(dates):
    with patch("zova.api.fetch_ticketmaster_events", new_callable=AsyncMock) as fetch:
        response = get_events({"city": "Boston", **dates})
        assert response.status_code == 422
        fetch.assert_not_awaited()
