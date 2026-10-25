import pytest
from fastapi.testclient import TestClient

from tests.conftest import forecast_params
from tests.synthetic_data import (
    EXPECTED_ACTUALS,
    EXPECTED_BIAS,
    EXPECTED_FORECASTS,
    EXPECTED_MAE,
    EXPECTED_MAPE,
    EXPECTED_MAPE_OBSERVATIONS,
    EXPECTED_MATCHED,
    EXPECTED_RMSE,
    HOURS_PER_DAY,
)


def test_accuracy_metrics_and_period_errors(api_client: TestClient) -> None:
    response = api_client.get("/api/v1/accuracy", params=forecast_params())

    assert response.status_code == 200
    body = response.json()
    assert body["unit"] == "MW"
    assert body["coverage"] == {
        "expected_periods": HOURS_PER_DAY,
        "matched_periods": EXPECTED_MATCHED,
        "missing_forecast_periods": HOURS_PER_DAY - EXPECTED_FORECASTS,
        "missing_actual_periods": HOURS_PER_DAY - EXPECTED_ACTUALS,
    }
    metrics = body["metrics"]
    assert metrics["mae_mw"] == pytest.approx(EXPECTED_MAE)
    assert metrics["rmse_mw"] == pytest.approx(EXPECTED_RMSE)
    assert metrics["bias_mw"] == pytest.approx(EXPECTED_BIAS)
    assert metrics["mape_percent"] == pytest.approx(EXPECTED_MAPE)
    assert metrics["mape_observations"] == EXPECTED_MAPE_OBSERVATIONS

    rows = {row["start_time"]: row for row in body["data"]}
    midnight = rows["2026-01-15T00:00:00Z"]
    assert midnight["forecast_generation_mw"] == 100
    assert midnight["actual_generation_mw"] == 60
    assert midnight["error_mw"] == 40
    assert midnight["absolute_error_mw"] == 40
    assert "2026-01-15T00:30:00Z" not in rows
    missing_actual = rows["2026-01-15T03:00:00Z"]
    assert missing_actual["forecast_generation_mw"] == 10
    assert missing_actual["actual_generation_mw"] is None
    assert missing_actual["error_mw"] is None
    zero_actual = rows["2026-01-15T02:00:00Z"]
    assert zero_actual["error_mw"] == 0
    assert zero_actual["actual_generation_mw"] == 0


def test_accuracy_rejects_a_naive_cutoff(api_client: TestClient) -> None:
    response = api_client.get(
        "/api/v1/accuracy",
        params={"delivery_date": "2026-01-15", "decision_time": "2026-01-14T13:00:00"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
