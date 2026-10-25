from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from app.core.dependencies import get_elexon_client
from app.main import create_app
from tests.synthetic_data import synthetic_actuals, synthetic_forecasts


@pytest.fixture
def elexon() -> AsyncMock:
    mock = AsyncMock()
    mock.get_wind_forecast_versions.return_value = synthetic_forecasts()
    mock.get_wind_actuals.return_value = synthetic_actuals()
    return mock


@pytest.fixture
def api_client(elexon: AsyncMock) -> Iterator[TestClient]:
    application = create_app()
    application.dependency_overrides[get_elexon_client] = lambda: elexon
    with TestClient(application) as client:
        yield client


def forecast_params(**overrides: object) -> dict[str, object]:
    params: dict[str, object] = {
        "delivery_date": "2026-01-15",
        "decision_time": "2026-01-14T13:00:00Z",
    }
    params.update(overrides)
    return params
