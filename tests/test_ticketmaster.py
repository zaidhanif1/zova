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
            TICKETMASTER_URL, params={"apikey": "fixture-key", "city": "Boston", "size": 20}
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
        params = {"apikey": "fixture-key", "city": "Boston", "size": 20}
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
