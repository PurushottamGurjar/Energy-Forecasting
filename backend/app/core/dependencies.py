from typing import Annotated

from fastapi import Depends, Query, Request
from pydantic import ValidationError
from fastapi.exceptions import RequestValidationError

from app.clients.elexon_client import ElexonClient
from app.config.settings import Settings, get_settings
from app.core.exceptions import AppError
from app.dto.accuracy import AccuracyQueryParams
from app.dto.forecast import ForecastQueryParams
from app.service import AccuracyService, ForecastService

DECISION_TIME_DESCRIPTION = (
    "Timezone-aware ISO 8601 decision cutoff. It is normalized to UTC and is "
    "not inferred from the delivery date. A documented pilot assumption for a "
    "day-ahead review is 13:00 UTC on the previous calendar day."
)


def get_elexon_client(request: Request) -> ElexonClient:
    client = getattr(request.app.state, "elexon_client", None)
    if client is None:
        raise AppError("The Elexon client is not available")
    return client


def get_forecast_service(
    client: Annotated[ElexonClient, Depends(get_elexon_client)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ForecastService:
    return ForecastService(client, settings)


def get_accuracy_service(
    forecasts: Annotated[ForecastService, Depends(get_forecast_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AccuracyService:
    return AccuracyService(forecasts, settings)


def parse_forecast_query(
    delivery_date: Annotated[
        str,
        Query(description="Delivery date in YYYY-MM-DD. Must be in January 2026."),
    ],
    decision_time: Annotated[str, Query(description=DECISION_TIME_DESCRIPTION)],
    include_actuals: Annotated[
        bool,
        Query(
            description=(
                "When true, attach hourly FUELHH wind actuals. Each hour is the "
                "average of the half-hour settlement periods inside it."
            )
        ),
    ] = False,
) -> ForecastQueryParams:
    try:
        return ForecastQueryParams.model_validate(
            {
                "delivery_date": delivery_date,
                "decision_time": decision_time,
                "include_actuals": include_actuals,
            }
        )
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


def parse_accuracy_query(
    delivery_date: Annotated[
        str,
        Query(description="Delivery date in YYYY-MM-DD. Must be in January 2026."),
    ],
    decision_time: Annotated[str, Query(description=DECISION_TIME_DESCRIPTION)],
) -> AccuracyQueryParams:
    try:
        return AccuracyQueryParams.model_validate(
            {"delivery_date": delivery_date, "decision_time": decision_time}
        )
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc
