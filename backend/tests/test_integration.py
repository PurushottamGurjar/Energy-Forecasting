from datetime import date, datetime, timezone

import httpx
import pytest

from app.clients.elexon_client import ElexonClient
from app.config.settings import get_settings
from app.service import ForecastService

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_live_january_delivery_uses_the_pre_cutoff_forecast() -> None:
    settings = get_settings()
    timeout = httpx.Timeout(settings.elexon_timeout_seconds)
    async with httpx.AsyncClient(
        base_url=settings.elexon_base_url_normalized,
        timeout=timeout,
    ) as http:
        service = ForecastService(ElexonClient(http, settings), settings)
        result = await service.get_forecasts(
            date(2026, 1, 15),
            datetime(2026, 1, 14, 13, 0, tzinfo=timezone.utc),
            include_actuals=True,
        )

    rows = {row.start_time: row for row in result.data}
    hour = rows[datetime(2026, 1, 15, 10, 0, tzinfo=timezone.utc)]
    assert datetime(2026, 1, 15, 10, 30, tzinfo=timezone.utc) not in rows
    assert hour.forecast_generation_mw == 12362
    assert hour.publish_time == datetime(2026, 1, 14, 11, 30, tzinfo=timezone.utc)
    assert hour.actual_generation_mw == (9807 + 11303) / 2
    assert result.summary.periods_expected == 24
