import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import date, datetime
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.config.settings import Settings
from app.core.exceptions import RateLimitError, UpstreamError, UpstreamTimeoutError
from app.dto.forecast import FuelHhRecord, WindForRecord
from app.helpers.datetime_utils import format_utc

logger = logging.getLogger(__name__)

RETRYABLE_STATUS = {429, 502, 503}
RecordT = TypeVar("RecordT", bound=BaseModel)
Sleeper = Callable[[float], Awaitable[None]]


class ElexonClient:
    def __init__(
        self,
        http: httpx.AsyncClient,
        settings: Settings,
        sleeper: Sleeper | None = None,
    ) -> None:
        self._http = http
        self._settings = settings
        self._sleep = sleeper or asyncio.sleep

    async def get_wind_actuals(self, settlement_date: date) -> list[FuelHhRecord]:
        payload = await self._get(
            "/datasets/FUELHH/stream",
            {
                "settlementDateFrom": settlement_date.isoformat(),
                "settlementDateTo": settlement_date.isoformat(),
                "fuelType": "WIND",
            },
        )
        return self._parse_records(payload, FuelHhRecord)

    async def get_wind_forecast_versions(
        self,
        publish_from: datetime,
        publish_to: datetime,
    ) -> list[WindForRecord]:
        payload = await self._get(
            "/datasets/WINDFOR/stream",
            {
                "publishDateTimeFrom": format_utc(publish_from),
                "publishDateTimeTo": format_utc(publish_to),
            },
        )
        return self._parse_records(payload, WindForRecord)

    async def _get(self, path: str, params: dict[str, str]) -> list[object]:
        attempts = self._settings.elexon_max_retries + 1
        for attempt in range(attempts):
            try:
                response = await self._http.get(path, params=params)
            except httpx.TimeoutException as exc:
                logger.warning("Elexon timeout for %s", path)
                raise UpstreamTimeoutError("The Elexon request timed out") from exc
            except httpx.RequestError as exc:
                logger.warning("Elexon connection error for %s: %s", path, exc)
                raise UpstreamError("The Elexon service could not be reached") from exc

            if response.status_code in RETRYABLE_STATUS and attempt + 1 < attempts:
                delay = _retry_delay(response, attempt)
                logger.warning(
                    "Retrying Elexon %s after HTTP %s (attempt %s)",
                    path,
                    response.status_code,
                    attempt + 1,
                )
                await self._sleep(delay)
                continue

            if response.status_code == 429:
                raise RateLimitError("Elexon rate limited the request")
            if response.status_code >= 400:
                logger.warning(
                    "Elexon HTTP %s for %s: %s",
                    response.status_code,
                    path,
                    response.text[:300],
                )
                raise UpstreamError("The Elexon service returned an error")

            return _decode_json_array(response)

        raise UpstreamError("The Elexon service returned an error")

    def _parse_records(self, payload: list[object], model: type[RecordT]) -> list[RecordT]:
        records: list[RecordT] = []
        invalid = 0
        for item in payload:
            try:
                records.append(model.model_validate(item))
            except ValidationError:
                invalid += 1
        if invalid:
            logger.warning("Skipped %s invalid Elexon records from %s", invalid, model.__name__)
        if payload and not records:
            raise UpstreamError("The Elexon response did not contain any valid records")
        return records


def _decode_json_array(response: httpx.Response) -> list[object]:
    try:
        payload = response.json()
    except ValueError as exc:
        logger.warning("Elexon returned invalid JSON")
        raise UpstreamError("The Elexon response was not valid JSON") from exc
    if not isinstance(payload, list):
        logger.warning("Elexon returned %s instead of a list", type(payload).__name__)
        raise UpstreamError("The Elexon response had an unexpected structure")
    return payload


def _retry_delay(response: httpx.Response, attempt: int) -> float:
    header = response.headers.get("Retry-After")
    if header:
        try:
            return min(float(header), 10.0)
        except ValueError:
            logger.warning("Ignoring non-numeric Retry-After header")
    return min(0.5 * (2**attempt), 10.0)
