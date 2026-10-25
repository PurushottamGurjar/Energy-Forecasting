import math
from datetime import date, datetime, timezone

from app.dto.forecast import FuelHhRecord, WindForRecord

UTC = timezone.utc
DELIVERY_DATE = date(2026, 1, 15)
DECISION_TIME = datetime(2026, 1, 14, 13, 0, tzinfo=UTC)

# Hourly actuals: 00:00 is mean(80, 40)=60, 01:00 is 100, 02:00 is 0.
# Matched errors against forecasts 100, 50, and 0 are 40, -50, and 0.
EXPECTED_MAE = 30.0
EXPECTED_RMSE = math.sqrt(4100 / 3)
EXPECTED_BIAS = -10 / 3
EXPECTED_MAPE = ((40 / 60) + (50 / 100)) / 2 * 100
EXPECTED_MAPE_OBSERVATIONS = 2
EXPECTED_MATCHED = 3
EXPECTED_FORECASTS = 4
EXPECTED_ACTUALS = 3
EXPECTED_AVERAGE = 40.0
HOURS_PER_DAY = 24


def wind_record(publish_time: str, start_time: str, generation: float) -> WindForRecord:
    return WindForRecord.model_validate(
        {"publishTime": publish_time, "startTime": start_time, "generation": generation}
    )


def actual_record(
    publish_time: str,
    start_time: str,
    generation: float,
    fuel_type: str = "WIND",
) -> FuelHhRecord:
    return FuelHhRecord.model_validate(
        {
            "publishTime": publish_time,
            "startTime": start_time,
            "generation": generation,
            "fuelType": fuel_type,
        }
    )


def synthetic_forecasts() -> list[WindForRecord]:
    return [
        wind_record("2026-01-14T10:00:00Z", "2026-01-15T00:00:00Z", 1),
        wind_record("2026-01-14T12:00:00Z", "2026-01-15T00:00:00Z", 100),
        wind_record("2026-01-14T14:00:00Z", "2026-01-15T00:00:00Z", 999),
        wind_record("2026-01-14T12:00:00Z", "2026-01-15T01:00:00Z", 50),
        wind_record("2026-01-14T15:00:00Z", "2026-01-15T01:00:00Z", 80),
        wind_record("2026-01-14T11:00:00Z", "2026-01-15T02:00:00Z", 0),
        wind_record("2026-01-14T11:00:00Z", "2026-01-15T03:00:00Z", 10),
        wind_record("2026-01-14T11:00:00Z", "2026-01-16T00:00:00Z", 70),
    ]


def synthetic_actuals() -> list[FuelHhRecord]:
    return [
        actual_record("2026-01-15T00:30:00Z", "2026-01-15T00:00:00Z", 70),
        actual_record("2026-01-15T01:00:00Z", "2026-01-15T00:00:00Z", 80),
        actual_record("2026-01-15T01:00:00Z", "2026-01-15T00:30:00Z", 40),
        actual_record("2026-01-15T01:00:00Z", "2026-01-15T01:00:00Z", 100),
        actual_record("2026-01-15T01:00:00Z", "2026-01-15T02:00:00Z", 0),
        actual_record("2026-01-15T01:00:00Z", "2026-01-15T04:00:00Z", 5, fuel_type="CCGT"),
    ]
