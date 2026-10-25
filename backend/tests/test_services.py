from datetime import date, datetime, timedelta, timezone

import httpx
import pytest

from app.clients.elexon_client import ElexonClient
from app.config.settings import Settings
from app.core.exceptions import RateLimitError, UpstreamError, UpstreamTimeoutError
from app.dto.forecast import FuelHhRecord, WindForRecord
from app.service import (
    DayComparison,
    ForecastService,
    average_half_hour_actuals,
    calculate_accuracy,
    select_latest_actuals,
    select_latest_forecasts,
)
from tests.synthetic_data import (
    DELIVERY_DATE,
    DECISION_TIME,
    EXPECTED_BIAS,
    EXPECTED_MAE,
    EXPECTED_MAPE,
    synthetic_actuals,
    synthetic_forecasts,
    wind_record,
)

UTC = timezone.utc


def test_latest_publish_time_wins_and_later_rows_break_ties() -> None:
    records = [
        wind_record("2026-01-14T12:00:00Z", "2026-01-15T00:00:00Z", 10),
        wind_record("2026-01-14T12:00:00Z", "2026-01-15T00:00:00Z", 25),
        wind_record("2026-01-14T11:00:00Z", "2026-01-15T00:00:00Z", 99),
    ]

    selected = select_latest_forecasts(records, DELIVERY_DATE, DECISION_TIME)

    assert selected[datetime(2026, 1, 15, 0, 0, tzinfo=UTC)].generation == 25


def test_forecasts_after_the_cutoff_are_excluded() -> None:
    selected = select_latest_forecasts(synthetic_forecasts(), DELIVERY_DATE, DECISION_TIME)

    assert selected[datetime(2026, 1, 15, 0, 0, tzinfo=UTC)].generation == 100
    assert selected[datetime(2026, 1, 15, 1, 0, tzinfo=UTC)].generation == 50
    assert datetime(2026, 1, 16, 0, 0, tzinfo=UTC) not in selected


def test_cutoff_uses_utc_when_the_input_has_another_offset() -> None:
    decision = datetime(2026, 1, 14, 14, 0, tzinfo=timezone(timedelta(hours=1)))
    records = [
        wind_record("2026-01-14T12:30:00Z", "2026-01-15T05:00:00Z", 40),
        wind_record("2026-01-14T13:30:00Z", "2026-01-15T05:00:00Z", 90),
    ]

    selected = select_latest_forecasts(records, DELIVERY_DATE, decision)

    assert selected[datetime(2026, 1, 15, 5, 0, tzinfo=UTC)].generation == 40


def test_duplicate_actuals_keep_the_latest_publication() -> None:
    selected = select_latest_actuals(synthetic_actuals(), DELIVERY_DATE)

    midnight = datetime(2026, 1, 15, 0, 0, tzinfo=UTC)
    assert selected[midnight].generation == 80
    assert datetime(2026, 1, 15, 4, 0, tzinfo=UTC) not in selected


def test_mape_is_null_when_every_actual_is_too_small() -> None:
    slot = datetime(2026, 1, 15, 0, 0, tzinfo=UTC)
    day = DayComparison(
        decision_time=DECISION_TIME,
        forecasts={slot: wind_record("2026-01-14T12:00:00Z", "2026-01-15T00:00:00Z", 10)},
        actuals={
            slot: FuelHhRecord.model_validate(
                {
                    "publishTime": "2026-01-15T01:00:00Z",
                    "startTime": "2026-01-15T00:00:00Z",
                    "generation": 0,
                    "fuelType": "WIND",
                }
            )
        },
    )

    result = calculate_accuracy(DELIVERY_DATE, day, mape_min_actual_mw=1)

    assert result.coverage.matched_periods == 1
    assert result.metrics.mae_mw == pytest.approx(10)
    assert result.metrics.mape_percent is None
    assert result.metrics.mape_observations == 0


def test_metrics_are_null_when_nothing_matches() -> None:
    day = DayComparison(decision_time=DECISION_TIME, forecasts={}, actuals={})

    result = calculate_accuracy(DELIVERY_DATE, day, mape_min_actual_mw=1)

    assert result.metrics.mae_mw is None
    assert result.metrics.rmse_mw is None
    assert result.metrics.bias_mw is None
    assert result.coverage.matched_periods == 0
    assert result.coverage.expected_periods == 24


def test_half_hour_actuals_average_into_one_hourly_value() -> None:
    selected = select_latest_actuals(synthetic_actuals(), DELIVERY_DATE)

    averaged = average_half_hour_actuals(selected)

    midnight = datetime(2026, 1, 15, 0, 0, tzinfo=UTC)
    one_am = datetime(2026, 1, 15, 1, 0, tzinfo=UTC)
    assert averaged[midnight].generation == 60
    assert averaged[one_am].generation == 100
    assert datetime(2026, 1, 15, 0, 30, tzinfo=UTC) not in averaged
    assert len(averaged) == 3


def test_hand_calculated_metrics() -> None:
    day = DayComparison(
        decision_time=DECISION_TIME,
        forecasts=select_latest_forecasts(synthetic_forecasts(), DELIVERY_DATE, DECISION_TIME),
        actuals=select_latest_actuals(synthetic_actuals(), DELIVERY_DATE),
    )

    result = calculate_accuracy(DELIVERY_DATE, day, mape_min_actual_mw=1)

    assert result.metrics.mae_mw == pytest.approx(EXPECTED_MAE)
    assert result.metrics.bias_mw == pytest.approx(EXPECTED_BIAS)
    assert result.metrics.mape_percent == pytest.approx(EXPECTED_MAPE)


@pytest.mark.asyncio
async def test_load_day_requests_the_publish_window() -> None:
    client = AsyncMockClient()
    service = ForecastService(client, Settings(forecast_lookback_hours=72, _env_file=None))

    await service.load_day(date(2026, 1, 1), datetime(2025, 12, 31, 13, 0, tzinfo=UTC), False)

    publish_from, publish_to = client.get_wind_forecast_versions.await_args.args
    assert publish_from == datetime(2025, 12, 28, 13, 0, tzinfo=UTC)
    assert publish_to == datetime(2025, 12, 31, 13, 0, tzinfo=UTC)
    client.get_wind_actuals.assert_not_awaited()


@pytest.mark.asyncio
async def test_client_sends_documented_query_parameters() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=[])

    client = _client(handler)
    await client.get_wind_actuals(date(2026, 1, 15))
    await client.get_wind_forecast_versions(
        datetime(2026, 1, 11, 13, 0, tzinfo=UTC),
        datetime(2026, 1, 14, 13, 0, tzinfo=UTC),
    )

    actual_params = dict(seen[0].url.params)
    forecast_params = dict(seen[1].url.params)
    assert seen[0].url.path == "/datasets/FUELHH/stream"
    assert actual_params == {
        "settlementDateFrom": "2026-01-15",
        "settlementDateTo": "2026-01-15",
        "fuelType": "WIND",
    }
    assert seen[1].url.path == "/datasets/WINDFOR/stream"
    assert forecast_params == {
        "publishDateTimeFrom": "2026-01-11T13:00:00Z",
        "publishDateTimeTo": "2026-01-14T13:00:00Z",
    }


@pytest.mark.asyncio
async def test_client_retries_rate_limits_then_parses_records() -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls < 3:
            return httpx.Response(429, headers={"Retry-After": "0"})
        return httpx.Response(
            200,
            json=[
                {
                    "publishTime": "2026-01-14T11:30:00Z",
                    "startTime": "2026-01-15T10:00:00Z",
                    "generation": 15,
                },
                {"publishTime": "not-a-timestamp"},
            ],
        )

    records = await _client(handler, retries=3).get_wind_forecast_versions(
        datetime(2026, 1, 14, 11, 0, tzinfo=UTC),
        datetime(2026, 1, 14, 12, 0, tzinfo=UTC),
    )

    assert calls == 3
    assert len(records) == 1
    assert records[0].generation == 15


@pytest.mark.asyncio
async def test_client_stops_after_the_retry_budget() -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(503)

    with pytest.raises(UpstreamError):
        await _client(handler, retries=2).get_wind_actuals(date(2026, 1, 15))

    assert calls == 3


@pytest.mark.asyncio
async def test_exhausted_rate_limit_is_distinct_from_a_server_error() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"Retry-After": "0"})

    with pytest.raises(RateLimitError):
        await _client(handler, retries=1).get_wind_actuals(date(2026, 1, 15))


@pytest.mark.asyncio
async def test_server_error_is_not_retried() -> None:
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(500, text="boom")

    with pytest.raises(UpstreamError):
        await _client(handler, retries=3).get_wind_actuals(date(2026, 1, 15))

    assert calls == 1


@pytest.mark.asyncio
async def test_timeout_and_invalid_payloads() -> None:
    def timeout(_request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out")

    def invalid_json(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"{")

    def wrapped(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": []})

    def empty(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    def all_invalid(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"generation": "nope"}])

    with pytest.raises(UpstreamTimeoutError):
        await _client(timeout).get_wind_actuals(date(2026, 1, 15))
    with pytest.raises(UpstreamError):
        await _client(invalid_json).get_wind_actuals(date(2026, 1, 15))
    with pytest.raises(UpstreamError):
        await _client(wrapped).get_wind_actuals(date(2026, 1, 15))
    with pytest.raises(UpstreamError):
        await _client(all_invalid).get_wind_actuals(date(2026, 1, 15))
    assert await _client(empty).get_wind_actuals(date(2026, 1, 15)) == []


class AsyncMockClient:
    def __init__(self) -> None:
        self.get_wind_forecast_versions = _AsyncRecorder([])
        self.get_wind_actuals = _AsyncRecorder([])


class _AsyncRecorder:
    def __init__(self, result: list[WindForRecord]) -> None:
        self.result = result
        self.await_args = None
        self.called = False

    async def __call__(self, *args: object) -> list[WindForRecord]:
        self.await_args = type("Args", (), {"args": args})()
        self.called = True
        return self.result

    def assert_not_awaited(self) -> None:
        assert not self.called


def _client(handler: object, retries: int = 0) -> ElexonClient:
    settings = Settings(elexon_max_retries=retries, _env_file=None)
    http = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),  # type: ignore[arg-type]
        base_url="https://elexon.test",
    )
    return ElexonClient(http, settings)
