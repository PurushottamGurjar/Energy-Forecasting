from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.dependencies import (
    get_accuracy_service,
    get_forecast_service,
    parse_accuracy_query,
    parse_forecast_query,
)
from app.dto.accuracy import AccuracyQueryParams, AccuracyResponse
from app.dto.common import ErrorResponse, HealthResponse
from app.dto.forecast import ForecastQueryParams, ForecastResponse
from app.service import AccuracyService, ForecastService

router = APIRouter()

_UPSTREAM_ERRORS = {
    422: {"model": ErrorResponse},
    429: {"model": ErrorResponse},
    502: {"model": ErrorResponse},
    504: {"model": ErrorResponse},
}


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/forecasts", response_model=ForecastResponse, responses=_UPSTREAM_ERRORS)
async def read_forecasts(
    params: Annotated[ForecastQueryParams, Depends(parse_forecast_query)],
    service: Annotated[ForecastService, Depends(get_forecast_service)],
) -> ForecastResponse:
    return await service.get_forecasts(
        delivery_date=params.delivery_date,
        decision_time=params.decision_time,
        include_actuals=params.include_actuals,
    )


@router.get("/accuracy", response_model=AccuracyResponse, responses=_UPSTREAM_ERRORS)
async def read_accuracy(
    params: Annotated[AccuracyQueryParams, Depends(parse_accuracy_query)],
    service: Annotated[AccuracyService, Depends(get_accuracy_service)],
) -> AccuracyResponse:
    return await service.get_accuracy(params.delivery_date, params.decision_time)
