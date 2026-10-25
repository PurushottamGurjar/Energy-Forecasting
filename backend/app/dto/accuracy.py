from datetime import date, datetime

from pydantic import BaseModel, field_validator

from app.dto.common import UtcDateTime
from app.dto.forecast import ForecastQueryParams
from app.helpers.datetime_utils import to_utc


class AccuracyQueryParams(BaseModel):
    delivery_date: date
    decision_time: datetime

    @field_validator("delivery_date")
    @classmethod
    def delivery_date_in_scope(cls, value: date) -> date:
        return ForecastQueryParams.delivery_date_in_scope(value)

    @field_validator("decision_time")
    @classmethod
    def decision_time_to_utc(cls, value: datetime) -> datetime:
        return to_utc(value)


class AccuracyPeriodResponse(BaseModel):
    start_time: UtcDateTime
    publish_time: UtcDateTime | None
    forecast_generation_mw: float | None
    actual_generation_mw: float | None
    error_mw: float | None
    absolute_error_mw: float | None


class AccuracyMetrics(BaseModel):
    mae_mw: float | None
    rmse_mw: float | None
    bias_mw: float | None
    mape_percent: float | None
    mape_observations: int


class AccuracyCoverage(BaseModel):
    expected_periods: int
    matched_periods: int
    missing_forecast_periods: int
    missing_actual_periods: int


class AccuracyResponse(BaseModel):
    delivery_date: date
    decision_time: UtcDateTime
    unit: str = "MW"
    coverage: AccuracyCoverage
    metrics: AccuracyMetrics
    data: list[AccuracyPeriodResponse]
