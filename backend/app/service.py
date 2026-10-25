import logging
import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

import pandas as pd

from app.clients.elexon_client import ElexonClient
from app.config.settings import Settings
from app.dto.accuracy import (
    AccuracyCoverage,
    AccuracyMetrics,
    AccuracyPeriodResponse,
    AccuracyResponse,
)
from app.dto.forecast import (
    ForecastPeriodResponse,
    ForecastResponse,
    ForecastSummary,
    FuelHhRecord,
    WindForRecord,
)
from app.helpers.datetime_utils import delivery_bounds, hour_start, hourly_slots, to_utc

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DayComparison:
    decision_time: datetime
    forecasts: dict[datetime, WindForRecord]
    actuals: dict[datetime, FuelHhRecord]


class ForecastService:
    def __init__(self, client: ElexonClient, settings: Settings) -> None:
        self._client = client
        self._settings = settings

    async def get_forecasts(
        self,
        delivery_date: date,
        decision_time: datetime,
        include_actuals: bool,
    ) -> ForecastResponse:
        day = await self.load_day(delivery_date, decision_time, include_actuals)
        return build_forecast_response(delivery_date, day, include_actuals)

    async def load_day(
        self,
        delivery_date: date,
        decision_time: datetime,
        include_actuals: bool,
    ) -> DayComparison:
        decision_time = to_utc(decision_time)
        publish_from = decision_time - timedelta(hours=self._settings.forecast_lookback_hours)
        versions = await self._client.get_wind_forecast_versions(publish_from, decision_time)
        forecasts = select_latest_forecasts(versions, delivery_date, decision_time)
        actuals: dict[datetime, FuelHhRecord] = {}
        if include_actuals:
            raw_actuals = await self._client.get_wind_actuals(delivery_date)
            actuals = average_half_hour_actuals(select_latest_actuals(raw_actuals, delivery_date))
        _log_coverage(delivery_date, forecasts)
        return DayComparison(decision_time=decision_time, forecasts=forecasts, actuals=actuals)


class AccuracyService:
    def __init__(self, forecasts: ForecastService, settings: Settings) -> None:
        self._forecasts = forecasts
        self._settings = settings

    async def get_accuracy(self, delivery_date: date, decision_time: datetime) -> AccuracyResponse:
        day = await self._forecasts.load_day(delivery_date, decision_time, include_actuals=True)
        return calculate_accuracy(delivery_date, day, self._settings.mape_min_actual_mw)


def select_latest_forecasts(
    records: list[WindForRecord],
    delivery_date: date,
    decision_time: datetime,
) -> dict[datetime, WindForRecord]:
    decision_time = to_utc(decision_time)
    start, end = delivery_bounds(delivery_date)
    chosen: dict[datetime, tuple[int, WindForRecord]] = {}
    for index, record in enumerate(records):
        if not (start <= record.start_time < end):
            continue
        if not _is_hour_start(record.start_time):
            continue
        if record.publish_time > decision_time:
            continue
        current = chosen.get(record.start_time)
        if current is None or (record.publish_time, index) >= (current[1].publish_time, current[0]):
            chosen[record.start_time] = (index, record)
    return {start_time: item[1] for start_time, item in chosen.items()}


def select_latest_actuals(
    records: list[FuelHhRecord],
    delivery_date: date,
) -> dict[datetime, FuelHhRecord]:
    start, end = delivery_bounds(delivery_date)
    chosen: dict[datetime, tuple[int, FuelHhRecord]] = {}
    for index, record in enumerate(records):
        if record.fuel_type is not None and record.fuel_type.upper() != "WIND":
            continue
        if not (start <= record.start_time < end):
            continue
        current = chosen.get(record.start_time)
        if current is None or (record.publish_time, index) >= (current[1].publish_time, current[0]):
            chosen[record.start_time] = (index, record)
    return {start_time: item[1] for start_time, item in chosen.items()}


def average_half_hour_actuals(
    actuals: dict[datetime, FuelHhRecord],
) -> dict[datetime, FuelHhRecord]:
    """Collapse FUELHH half-hours into one value per clock hour.

    Each hour is the mean of the half-hour rows that fall inside it. An hour
    with only one settlement period keeps that single reading.
    """
    grouped: dict[datetime, list[FuelHhRecord]] = {}
    for start_time, record in actuals.items():
        grouped.setdefault(hour_start(start_time), []).append(record)

    averaged: dict[datetime, FuelHhRecord] = {}
    for hour, records in grouped.items():
        generation = sum(record.generation for record in records) / len(records)
        latest = max(records, key=lambda record: (record.publish_time, record.start_time))
        averaged[hour] = latest.model_copy(update={"start_time": hour, "generation": generation})
    return averaged


def build_forecast_response(
    delivery_date: date,
    day: DayComparison,
    include_actuals: bool,
) -> ForecastResponse:
    slots = hourly_slots(delivery_date)
    actuals = average_half_hour_actuals(day.actuals) if include_actuals else {}
    data: list[ForecastPeriodResponse] = []
    forecast_values: list[float] = []
    for slot in slots:
        forecast = day.forecasts.get(slot)
        actual = actuals.get(slot) if include_actuals else None
        if forecast is not None:
            forecast_values.append(forecast.generation)
        data.append(
            ForecastPeriodResponse(
                start_time=slot,
                publish_time=forecast.publish_time if forecast else None,
                forecast_generation_mw=forecast.generation if forecast else None,
                actual_generation_mw=actual.generation if actual else None,
            )
        )
    present = len(forecast_values)
    average = sum(forecast_values) / present if present else None
    return ForecastResponse(
        delivery_date=delivery_date,
        decision_time=day.decision_time,
        summary=ForecastSummary(
            periods_expected=len(slots),
            periods_with_forecast=present,
            missing_forecast_periods=len(slots) - present,
            average_forecast_mw=average,
        ),
        data=data,
    )


def calculate_accuracy(
    delivery_date: date,
    day: DayComparison,
    mape_min_actual_mw: float,
) -> AccuracyResponse:
    slots = hourly_slots(delivery_date)
    actuals = average_half_hour_actuals(day.actuals)
    frame = pd.DataFrame(
        {
            "start_time": slots,
            "publish_time": [
                day.forecasts[slot].publish_time if slot in day.forecasts else None for slot in slots
            ],
            "forecast_generation_mw": [
                day.forecasts[slot].generation if slot in day.forecasts else math.nan for slot in slots
            ],
            "actual_generation_mw": [
                actuals[slot].generation if slot in actuals else math.nan for slot in slots
            ],
        }
    )
    frame["error_mw"] = frame["forecast_generation_mw"] - frame["actual_generation_mw"]
    frame["absolute_error_mw"] = frame["error_mw"].abs()

    matched = frame.dropna(subset=["forecast_generation_mw", "actual_generation_mw"])
    if matched.empty:
        logger.warning("No matched forecast-actual pairs for delivery %s", delivery_date.isoformat())

    return AccuracyResponse(
        delivery_date=delivery_date,
        decision_time=day.decision_time,
        coverage=AccuracyCoverage(
            expected_periods=len(frame),
            matched_periods=int(len(matched)),
            missing_forecast_periods=int(frame["forecast_generation_mw"].isna().sum()),
            missing_actual_periods=int(frame["actual_generation_mw"].isna().sum()),
        ),
        metrics=_metrics(matched, mape_min_actual_mw),
        data=[_period_from_row(row) for row in frame.itertuples(index=False)],
    )


def _log_coverage(delivery_date: date, forecasts: dict[datetime, WindForRecord]) -> None:
    missing_hours = [slot for slot in hourly_slots(delivery_date) if slot not in forecasts]
    if missing_hours:
        logger.warning(
            "Delivery %s is missing %s of 24 hourly wind forecasts",
            delivery_date.isoformat(),
            len(missing_hours),
        )


def _metrics(matched: pd.DataFrame, mape_min_actual_mw: float) -> AccuracyMetrics:
    if matched.empty:
        return AccuracyMetrics(
            mae_mw=None,
            rmse_mw=None,
            bias_mw=None,
            mape_percent=None,
            mape_observations=0,
        )

    errors = matched["error_mw"]
    usable = matched[matched["actual_generation_mw"] >= mape_min_actual_mw]
    if usable.empty:
        mape = None
    else:
        mape = float((usable["error_mw"].abs() / usable["actual_generation_mw"]).mean() * 100)

    return AccuracyMetrics(
        mae_mw=float(errors.abs().mean()),
        rmse_mw=float((errors.pow(2).mean()) ** 0.5),
        bias_mw=float(errors.mean()),
        mape_percent=mape,
        mape_observations=int(len(usable)),
    )


def _period_from_row(row: object) -> AccuracyPeriodResponse:
    return AccuracyPeriodResponse(
        start_time=_as_datetime(row.start_time),
        publish_time=_optional_datetime(row.publish_time),
        forecast_generation_mw=_optional_float(row.forecast_generation_mw),
        actual_generation_mw=_optional_float(row.actual_generation_mw),
        error_mw=_optional_float(row.error_mw),
        absolute_error_mw=_optional_float(row.absolute_error_mw),
    )


def _optional_float(value: object) -> float | None:
    if value is None or _is_missing(value):
        return None
    return float(value)  # type: ignore[arg-type]


def _optional_datetime(value: object) -> datetime | None:
    if value is None or _is_missing(value):
        return None
    return _as_datetime(value)


def _as_datetime(value: object) -> datetime:
    if isinstance(value, pd.Timestamp):
        value = value.to_pydatetime()
    if not isinstance(value, datetime):
        raise TypeError("Expected a datetime value in the accuracy frame")
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _is_hour_start(value: datetime) -> bool:
    return value.minute == 0 and value.second == 0 and value.microsecond == 0


def _is_missing(value: object) -> bool:
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False
