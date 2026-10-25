from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.config.settings import DELIVERY_END, DELIVERY_START
from app.dto.common import UtcDateTime
from app.helpers.datetime_utils import assume_utc, to_utc


class ForecastQueryParams(BaseModel):
    delivery_date: date
    decision_time: datetime
    include_actuals: bool = False

    @field_validator("delivery_date")
    @classmethod
    def delivery_date_in_scope(cls, value: date) -> date:
        if value < DELIVERY_START or value > DELIVERY_END:
            raise ValueError(
                "delivery_date must be a January 2026 delivery date "
                f"({DELIVERY_START.isoformat()} to {DELIVERY_END.isoformat()})"
            )
        return value

    @field_validator("decision_time")
    @classmethod
    def decision_time_to_utc(cls, value: datetime) -> datetime:
        return to_utc(value)


class WindForRecord(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    publish_time: datetime = Field(alias="publishTime")
    start_time: datetime = Field(alias="startTime")
    generation: float

    @field_validator("publish_time", "start_time")
    @classmethod
    def timestamps_to_utc(cls, value: datetime) -> datetime:
        return assume_utc(value)


class FuelHhRecord(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    publish_time: datetime = Field(alias="publishTime")
    start_time: datetime = Field(alias="startTime")
    fuel_type: str | None = Field(default=None, alias="fuelType")
    generation: float

    @field_validator("publish_time", "start_time")
    @classmethod
    def timestamps_to_utc(cls, value: datetime) -> datetime:
        return assume_utc(value)


class ForecastPeriodResponse(BaseModel):
    start_time: UtcDateTime
    publish_time: UtcDateTime | None
    forecast_generation_mw: float | None
    actual_generation_mw: float | None


class ForecastSummary(BaseModel):
    periods_expected: int
    periods_with_forecast: int
    missing_forecast_periods: int
    average_forecast_mw: float | None


class ForecastResponse(BaseModel):
    delivery_date: date
    decision_time: UtcDateTime
    timezone: str = "UTC"
    unit: str = "MW"
    summary: ForecastSummary
    data: list[ForecastPeriodResponse]
