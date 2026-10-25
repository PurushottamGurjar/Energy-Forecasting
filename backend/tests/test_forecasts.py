from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from app.core.dependencies import get_elexon_client
from app.core.exceptions import RateLimitError, UpstreamError, UpstreamTimeoutError
from app.main import create_app
from tests.conftest import forecast_params
from tests.synthetic_data import EXPECTED_AVERAGE, EXPECTED_FORECASTS, HOURS_PER_DAY


def _by_start(payload: dict[str, object]) -> dict[str, dict[str, object]]:
    rows = payload["data"]
    assert isinstance(rows, list)
    return {row["start_time"]: row for row in rows}


def test_selects_latest_forecast_before_cutoff(api_client: TestClient) -> None:
    response = api_client.get("/api/v1/forecasts", params=forecast_params())

    assert response.status_code == 200
    body = response.json()
    assert body["delivery_date"] == "2026-01-15"
    assert body["decision_time"] == "2026-01-14T13:00:00Z"
    assert body["timezone"] == "UTC"
    assert body["unit"] == "MW"
    assert body["summary"]["periods_expected"] == HOURS_PER_DAY
    assert body["summary"]["periods_with_forecast"] == EXPECTED_FORECASTS
    assert body["summary"]["missing_forecast_periods"] == HOURS_PER_DAY - EXPECTED_FORECASTS
    assert body["summary"]["average_forecast_mw"] == EXPECTED_AVERAGE
    assert len(body["data"]) == HOURS_PER_DAY

    rows = _by_start(body)
    selected = rows["2026-01-15T00:00:00Z"]
    assert selected["forecast_generation_mw"] == 100
    assert selected["publish_time"] == "2026-01-14T12:00:00Z"
    assert selected["actual_generation_mw"] is None
    assert "2026-01-15T00:30:00Z" not in rows
    assert rows["2026-01-15T01:00:00Z"]["forecast_generation_mw"] == 50
    assert "2026-01-16T00:00:00Z" not in rows


def test_include_actuals_matches_start_time_and_skips_other_fuels(
    api_client: TestClient,
    elexon: AsyncMock,
) -> None:
    response = api_client.get("/api/v1/forecasts", params=forecast_params(include_actuals=True))

    assert response.status_code == 200
    rows = _by_start(response.json())
    assert rows["2026-01-15T00:00:00Z"]["actual_generation_mw"] == 60
    assert rows["2026-01-15T01:00:00Z"]["actual_generation_mw"] == 100
    assert "2026-01-15T00:30:00Z" not in rows
    assert rows["2026-01-15T04:00:00Z"]["actual_generation_mw"] is None
    elexon.get_wind_actuals.assert_awaited()


def test_omitting_actuals_does_not_request_them(api_client: TestClient, elexon: AsyncMock) -> None:
    response = api_client.get("/api/v1/forecasts", params=forecast_params())

    assert response.status_code == 200
    elexon.get_wind_actuals.assert_not_awaited()


def test_normalizes_decision_time_to_utc(api_client: TestClient) -> None:
    response = api_client.get(
        "/api/v1/forecasts",
        params=forecast_params(decision_time="2026-01-14T14:00:00+01:00"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["decision_time"] == "2026-01-14T13:00:00Z"
    rows = _by_start(body)
    assert rows["2026-01-15T00:00:00Z"]["forecast_generation_mw"] == 100


def test_empty_upstream_payload_is_not_an_error(api_client: TestClient, elexon: AsyncMock) -> None:
    elexon.get_wind_forecast_versions.return_value = []

    response = api_client.get("/api/v1/forecasts", params=forecast_params())

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["periods_with_forecast"] == 0
    assert body["summary"]["missing_forecast_periods"] == HOURS_PER_DAY
    assert body["summary"]["average_forecast_mw"] is None
    assert all(row["forecast_generation_mw"] is None for row in body["data"])


def test_january_boundaries_are_accepted(api_client: TestClient) -> None:
    first = api_client.get(
        "/api/v1/forecasts",
        params=forecast_params(delivery_date="2026-01-01", decision_time="2025-12-31T13:00:00Z"),
    )
    last = api_client.get(
        "/api/v1/forecasts",
        params=forecast_params(delivery_date="2026-01-31", decision_time="2026-01-30T13:00:00Z"),
    )

    assert first.status_code == 200
    assert last.status_code == 200
    assert first.json()["data"][0]["start_time"] == "2026-01-01T00:00:00Z"
    assert last.json()["data"][-1]["start_time"] == "2026-01-31T23:00:00Z"


@pytest.mark.parametrize(
    ("params", "fragment"),
    [
        ({"delivery_date": "2025-12-31", "decision_time": "2025-12-30T13:00:00Z"}, "January 2026"),
        ({"delivery_date": "2026-02-01", "decision_time": "2026-01-31T13:00:00Z"}, "January 2026"),
        ({"delivery_date": "2026-01-15", "decision_time": "2026-01-14T13:00:00"}, "timezone-aware"),
        ({"delivery_date": "15-01-2026", "decision_time": "2026-01-14T13:00:00Z"}, "delivery_date"),
        ({"decision_time": "2026-01-14T13:00:00Z"}, "delivery_date"),
    ],
)
def test_invalid_query_parameters(api_client: TestClient, params: dict[str, str], fragment: str) -> None:
    response = api_client.get("/api/v1/forecasts", params=params)

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert fragment in body["error"]["message"]


def test_publish_window_ends_at_the_cutoff(api_client: TestClient, elexon: AsyncMock) -> None:
    api_client.get("/api/v1/forecasts", params=forecast_params())

    publish_from, publish_to = elexon.get_wind_forecast_versions.await_args.args
    assert publish_from == datetime(2026, 1, 11, 13, 0, tzinfo=timezone.utc)
    assert publish_to == datetime(2026, 1, 14, 13, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    ("error", "status", "code"),
    [
        (UpstreamTimeoutError("timed out"), 504, "upstream_timeout"),
        (UpstreamError("down"), 502, "upstream_unavailable"),
        (RateLimitError("slow down"), 429, "rate_limited"),
    ],
)
def test_upstream_failures(
    api_client: TestClient,
    elexon: AsyncMock,
    error: Exception,
    status: int,
    code: str,
) -> None:
    elexon.get_wind_forecast_versions.side_effect = error

    response = api_client.get("/api/v1/forecasts", params=forecast_params())

    assert response.status_code == status
    assert response.json()["error"]["code"] == code
    assert "Traceback" not in response.text


def test_unexpected_error_hides_internals(elexon: AsyncMock) -> None:
    elexon.get_wind_forecast_versions.side_effect = RuntimeError("secret boom")
    application = create_app()
    application.dependency_overrides[get_elexon_client] = lambda: elexon

    with TestClient(application, raise_server_exceptions=False) as client:
        response = client.get("/api/v1/forecasts", params=forecast_params())

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert "secret" not in response.text
    assert "Traceback" not in response.text
