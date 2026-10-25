# UK Wind Forecast Accuracy Dashboard

Wind Intelligence is a dashboard for evaluating Great Britain’s wind generation forecasts against actual generation before a day-ahead procurement decision. The application combines a frontend dashboard with a Python backend that retrieves historical forecast versions and actual generation data from the Elexon Insights API.

The project focuses on forecast accuracy, historical forecast selection, and hourly comparisons using MAE, RMSE, bias, and MAPE.

## Frontend — Wind Intelligence Dashboard
Link: https://windee-forecast.vercel.app/

<img width="1637" height="972" alt="image" src="https://github.com/user-attachments/assets/2bba8636-8779-419d-a3b5-a9a8321adaf2" />

<img width="1560" height="967" alt="image" src="https://github.com/user-attachments/assets/6a8e463b-2d8c-4a40-8fac-6f6d5e4239b8" />



The frontend provides the dashboard interface for reviewing wind generation forecasts and their accuracy for a selected delivery date and decision time.

### Features

- **Forecast visualization:** Review hourly wind generation forecasts for the selected delivery day.
- **Forecast accuracy:** Display MAE, RMSE, bias, and MAPE calculated by the backend.
- **Actual generation comparison:** Compare forecast values against observed wind generation.
- **Historical forecast selection:** View forecasts that were available at the specified decision cutoff, excluding later revisions.
- **Missing data handling:** Preserve unavailable forecast and actual values rather than treating them as zero.
- **API integration:** Retrieve forecast and accuracy data through the backend REST API.

The frontend does not calculate forecast accuracy metrics. All forecast selection, actual-generation processing, and metric calculations are handled by the backend.

### Technology Stack

- React
- Vite
- JavaScript
- React Query
- Nginx for production serving and reverse proxying
- Docker for containerized deployment

### Run Locally

Requirements: a current Node.js release and npm.

```bash
cd frontend
npm install
npm run dev
```

The development server runs at:

`http://localhost:5173`

### Frontend Configuration

The frontend uses `frontend/.env.example` for its API configuration.


Keep the API base URL relative. During local development, Vite forwards `/api` requests to the configured backend. In production, Nginx forwards requests server-side, avoiding the need for direct browser-to-backend requests.

To build the production frontend:

```bash
npm run build
```

---

## Backend — Forecast Processing and Accuracy Analysis

The backend retrieves actual wind generation and historical wind forecast versions from the Elexon Insights API. It selects the latest eligible forecast available at the requested decision time and compares it with the corresponding actual generation.

### Core Responsibilities

- Retrieve historical forecast versions and actual generation data.
- Filter forecasts by their publication timestamps to prevent future information from affecting historical evaluations.
- Select the latest eligible forecast for each delivery hour.
- Convert half-hourly actual generation readings into hourly values.
- Calculate forecast accuracy metrics.
- Expose forecast and accuracy data through REST endpoints.
- Handle upstream API errors, rate limits, timeouts, and invalid requests.

### Technology Stack

- Python 3.12
- FastAPI
- Uvicorn
- HTTPX for HTTP requests
- Pydantic for request validation and data models
- Pytest for testing
- Docker and Docker Compose

## Data Sources

The backend uses the Elexon Insights API.

**Base URL:** `https://data.elexon.co.uk/bmrs/api/v1`

| Data | Endpoint | Purpose |
|---|---|---|
| Actual wind generation | `GET /datasets/FUELHH/stream` | Retrieve half-hourly wind generation readings using settlement-date and fuel-type filters. |
| Historical wind forecasts | `GET /datasets/WINDFOR/stream` | Retrieve forecast versions using publication-time filters. |

The backend uses historical forecast data rather than the latest forecast snapshot, because the latest snapshot can contain revisions published after the decision cutoff.

The `/forecast/generation/wind/latest` endpoint has the same limitation. The `/forecast/generation/wind/evolution` endpoint can be used to inspect the history of an individual delivery period, while the stream endpoint provides the data needed for a full-day evaluation.

## Forecast Selection and Processing

Each request specifies a **delivery date** and a **decision time**.

- **Delivery date:** The day whose 24 hourly periods are evaluated.
- **Decision time:** The cutoff by which a forecast must have been published to qualify for the evaluation.

For every delivery hour, the backend:

1. Retrieves WINDFOR forecast versions from a configurable lookback window ending at the decision time.
2. Excludes forecasts published after the decision cutoff.
3. Selects the latest remaining `publishTime` for each hourly `startTime`. If multiple rows share a publication time, the later row in the Elexon response takes precedence.
4. Retrieves the corresponding FUELHH wind generation readings.
5. Averages the two half-hourly readings into an hourly actual value. If only one reading is available, that reading is used.
6. Aligns the hourly actual value with the corresponding forecast hour.

Missing forecasts and actual readings remain `null`. They are not replaced with zero, and missing data is not silently converted into a successful upstream response.

## Forecast Accuracy Metrics

The backend calculates accuracy metrics using only periods for which both forecast and actual values are available.

| Metric | Description |
|---|---|
| MAE | Mean Absolute Error; measures the average absolute difference between forecast and actual generation. |
| RMSE | Root Mean Squared Error; penalizes larger forecast errors more heavily. |
| Bias | Mean signed error; indicates whether forecasts tend to overestimate or underestimate generation. |
| MAPE | Mean Absolute Percentage Error; measures absolute error relative to actual generation, excluding periods below the configured minimum actual-generation threshold. |

The signed error is defined as:

`error_mw = forecast_generation_mw - actual_generation_mw`

A positive error indicates an overestimate, while a negative error indicates an underestimate.

A bias close to zero does not necessarily mean the forecast is accurate, because positive and negative errors can cancel each other out. MAE and RMSE should be considered alongside bias.

MAPE excludes periods where actual generation is below `MAPE_MIN_ACTUAL_MW`, which defaults to 1 MW. If no eligible periods remain, `mape_percent` is `null`. The response includes `mape_observations` to indicate how many periods contributed to the MAPE calculation.

## Historical Evaluation Assumptions

- The supported analysis scope is delivery in January 2026, from `2026-01-01` through `2026-01-31`.
- The evaluation returns 24 hourly delivery periods for a day.
- January 2026 uses GMT, so UTC calendar dates align with the relevant Elexon settlement dates.
- `decision_time` is required, must include a timezone, and is normalized to UTC.
- `DEFAULT_DECISION_CUTOFF_UTC=13:00` is a configurable pilot example. It is not an official market rule and is not automatically applied when the request omits `decision_time`.
- The default forecast lookback is 72 hours, configurable through `FORECAST_LOOKBACK_HOURS`.
- Forecast rows that do not start on the hour are ignored.
- Half-hourly FUELHH actuals are averaged before being returned as hourly readings.
- A missing forecast or actual remains `null`.

## API Reference

All application endpoints are under `/api/v1`.

### Health Check

`GET /api/v1/health`

Example response:

```json
{
  "status": "ok"
}
```

### Retrieve Forecasts

`GET /api/v1/forecasts`

**Query parameters**

| Parameter | Required | Description |
|---|---|---|
| `delivery_date` | Yes | Delivery date in `YYYY-MM-DD` format, within January 2026. |
| `decision_time` | Yes | Timezone-aware ISO 8601 timestamp. |
| `include_actuals` | No | Include actual generation values; defaults to `false`. |

Example:

```bash
curl "http://localhost:8000/api/v1/forecasts?delivery_date=2026-01-15&decision_time=2026-01-14T13:00:00Z&include_actuals=true"
```

`average_forecast_mw` is the mean of the forecasts found for the requested delivery day. It is `null` if no eligible forecasts are available.

An empty upstream data array is handled as a valid response with missing periods accounted for. Upstream failures are reported as errors rather than being treated as empty successful results.

### Retrieve Forecast Accuracy

`GET /api/v1/accuracy`

Uses the same `delivery_date` and `decision_time` parameters. Actual generation is always retrieved for accuracy calculations.

Example:

```bash
curl "http://localhost:8000/api/v1/accuracy?delivery_date=2026-01-15&decision_time=2026-01-14T13:00:00Z"
```

Metrics are calculated only for delivery periods with both a forecast and an actual value.

The accuracy endpoint evaluates one delivery day per request. Monthly accuracy trends and `GET /api/v1/accuracy/summary` are not implemented.

### Error Handling

Errors use a consistent response structure:

```json
{
  "error": {
    "code": "validation_error",
    "message": "delivery_date: ..."
  }
}
```

| Situation | HTTP status | Error code |
|---|---:|---|
| Invalid or out-of-range parameters | 422 | `validation_error` |
| Elexon continues rate-limiting after retries | 429 | `rate_limited` |
| Elexon error, invalid JSON, or connection failure | 502 | `upstream_unavailable` |
| Elexon request timeout | 504 | `upstream_timeout` |
| Unexpected server error | 500 | `internal_error` |

HTTP 429, 502, and 503 responses from Elexon are retried up to `ELEXON_MAX_RETRIES` times, which defaults to 3. Numeric `Retry-After` headers are honored, with a maximum wait of 10 seconds. Timeouts are not retried.

## Local Backend Setup

Requirements: Python 3.12.

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment.

**Windows:**

```bash
.venv\Scripts\activate
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

Install dependencies and start the server:

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`.

Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

### Backend Configuration

Configuration is documented in `backend/.env.example`.

```dotenv
ELEXON_BASE_URL=https://data.elexon.co.uk/bmrs/api/v1
ELEXON_TIMEOUT_SECONDS=30
DEFAULT_DECISION_CUTOFF_UTC=13:00
FORECAST_LOOKBACK_HOURS=72
MAPE_MIN_ACTUAL_MW=1
```

## Testing

Run the backend test suite from the `backend/` directory:

```bash
pytest
```

The default test suite mocks Elexon responses. A separate integration test is marked `integration` and is skipped unless explicitly requested.

Run the integration test with:

```bash
pytest -m integration
```

The integration test calls the public Elexon API for 15 January 2026 and checks the forecast/actual pair for the 10:00 UTC delivery hour.

## Docker Deployment

Run the application from the repository root:

```bash
docker compose up --build
```

- The backend is exposed on port `8000`.
- The frontend is served on port `8080`.
- Docker Compose configures the frontend proxy to communicate with the backend container.
- The backend health check uses `/api/v1/health`.
- The backend uses `backend/.env.example` for non-secret default settings.

Outside Docker Compose, the production frontend proxy defaults to:

`https://wind-energy-forecasting-2c1x.onrender.com`

Set `API_UPSTREAM` to change the upstream API origin.

## Verified Data Example

For delivery at `2026-01-15T10:00:00Z` with a decision cutoff of `2026-01-14T13:00:00Z`, the backend was checked against live Elexon data.

- Eligible forecast: `12362 MW`, published at `2026-01-14T11:30:00Z`.
- Later revision: `13340 MW`, published at `2026-01-14T15:30:00Z`; excluded because it falls after the decision cutoff.
- Actual generation readings: `9807 MW` at `10:00Z` and `11303 MW` at `10:30Z`.
- Hourly actual generation returned by the backend: `10555 MW`.

This demonstrates how the backend preserves the information available at the decision time instead of using a forecast revision published later.

## Project Structure

```text
.
├── frontend/
│   ├── src/                 React application
│   ├── .env.example         Frontend environment configuration
│   └── ...                  Vite and frontend configuration
├── backend/
│   ├── app/
│   │   ├── config/          Application settings
│   │   ├── core/            Errors and dependencies
│   │   ├── dto/             Request and response models
│   │   ├── helpers/         Datetime utilities
│   │   ├── clients/         Elexon HTTP client
│   │   ├── routes.py        HTTP endpoints
│   │   ├── service.py       Forecast selection and accuracy calculations
│   │   └── main.py          Application entry point
│   ├── .env.example         Backend configuration
│   └── requirements.txt     Python dependencies
└── docker-compose.yml       Container orchestration
```

The structure above describes the main application components; exact filenames may vary with the repository.

Author: Purushottam Gurjar
