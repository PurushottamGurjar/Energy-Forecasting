# UK Wind Forecast Accuracy Dashboard

Backend for reviewing Great Britain wind generation forecasts before a day-ahead procurement decision. It loads actual wind generation and historical forecast versions from the Elexon Insights API, keeps the version that had been published at a chosen cutoff, and reports MAE, RMSE, bias, and MAPE.

The `frontend/` directory is the Wind Intelligence dashboard. It reads the forecast and accuracy APIs. It does not recalculate MAE, RMSE, bias, or MAPE.

This backend was built with assistance from Cursor's AI coding agent (Grok).

## What the API does

A request names a **delivery date** and a **decision time**. The delivery date is the day whose 24 hourly periods are being evaluated. The decision time is the moment the forecast must have been known. A decision on one day can apply to delivery on the next day. The API does not invent a market gate-closure time.

For each delivery hour it:

1. Loads WINDFOR versions published in a lookback window that ends at the decision time.
2. Drops anything published after that cutoff, so later revisions cannot leak into the result.
3. Keeps the latest remaining `publishTime` for that hourly `startTime`. If two rows share a publish time, the later row in the Elexon payload wins.
4. Compares that forecast with the hourly FUELHH wind actual. FUELHH is half-hourly, so the two settlement periods inside the hour are averaged into one value.

Missing forecasts and missing actuals stay `null`. They are never replaced with zero.

## Confirmed data sources

Base URL: `https://data.elexon.co.uk/bmrs/api/v1`

| Data | Endpoint | Filters used |
| --- | --- | --- |
| Actual wind generation | [`GET /datasets/FUELHH/stream`](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream) | `settlementDateFrom`, `settlementDateTo`, `fuelType=WIND` |
| Forecast versions | [`GET /datasets/WINDFOR/stream`](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream) | `publishDateTimeFrom`, `publishDateTimeTo` |

FUELHH settlement-date filters cannot be combined with publish-time filters. The stream responses are JSON arrays.

WINDFOR without a publish window returns only the latest snapshot. That snapshot is not used, because it includes revisions made after the decision. [`/forecast/generation/wind/latest`](https://bmrs.elexon.co.uk/api-documentation/endpoint/forecast/generation/wind/latest) has the same limitation. [`/forecast/generation/wind/evolution`](https://bmrs.elexon.co.uk/api-documentation/endpoint/forecast/generation/wind/evolution) can show the history of one `startTime`, and it was used to check the client, but a full day is loaded from the stream in one request.

Checked live for delivery `2026-01-15T10:00:00Z` and cutoff `2026-01-14T13:00:00Z`:

- Eligible forecast: published `2026-01-14T11:30:00Z`, `12362` MW.
- The `2026-01-14T15:30:00Z` revision (`13340` MW) is after the cutoff and is excluded.
- Half-hour actuals at `10:00Z` and `10:30Z` are `9807` MW and `11303` MW. The API returns their average, `10555` MW.

## Assumptions

- The analysis scope is **delivery** in January 2026 (`2026-01-01` through `2026-01-31`), not the date of the decision. A cutoff on 31 Dec 2025 is valid for delivery on 1 Jan 2026.
- January 2026 is GMT, so the UTC calendar date matches the Elexon settlement date. The API returns 24 hourly periods. There is no clock change in this month.
- `decision_time` is required and must include a timezone. It is normalized to UTC. The value `DEFAULT_DECISION_CUTOFF_UTC=13:00` is a pilot example for documentation: delivery date D is often reviewed at 13:00 UTC on D-1. It is not an official market rule, and the API does not fill it in when the query omits it.
- WINDFOR rows for this dataset are hourly, and the API returns only those 24 hours. A forecast that does not start on the hour is ignored.
- FUELHH wind actuals stay half-hourly upstream. Before they are returned, the two settlement periods in each clock hour are averaged. If only one of the two periods is present, that single reading is used. The averaged actual is aligned to the hour start (`HH:00`), which is the same `startTime` as the WINDFOR row.
- Forecast history is requested from `decision_time` back `FORECAST_LOOKBACK_HOURS` (default 72). NESO publishes several times a day, and the wind forecast horizon is about two days, so this window contains the version that was current at a day-ahead cutoff.
- MAPE ignores periods whose actual generation is below `MAPE_MIN_ACTUAL_MW` (default 1 MW). If none remain, `mape_percent` is `null`. `mape_observations` counts the periods that were used.
- Bias is the mean signed error. A bias near zero does not show that the forecast was accurate, because overestimates and underestimates cancel. Use MAE and RMSE as well.
- `error_mw = forecast_generation_mw - actual_generation_mw`. Positive means the forecast was too high.

`GET /api/v1/accuracy/summary` is not implemented. The single-day forecast and accuracy endpoints are the supported API.

## API

All routes are under `/api/v1`.

### `GET /health`

```json
{"status": "ok"}
```

### `GET /forecasts`

Query parameters:

- `delivery_date` (required): `YYYY-MM-DD` in January 2026.
- `decision_time` (required): timezone-aware ISO 8601 timestamp.
- `include_actuals` (optional): `true` or `false`, default `false`.

```bash
curl "http://localhost:8000/api/v1/forecasts?delivery_date=2026-01-15&decision_time=2026-01-14T13:00:00Z&include_actuals=true"
```

`average_forecast_mw` is the mean of the forecasts that were found. It is `null` when none were published before the cutoff. An empty Elexon payload is still HTTP 200, with the missing periods counted. An upstream failure is not turned into an empty success.

### `GET /accuracy`

Same `delivery_date` and `decision_time` parameters. Actuals are always loaded.

```bash
curl "http://localhost:8000/api/v1/accuracy?delivery_date=2026-01-15&decision_time=2026-01-14T13:00:00Z"
```

Metrics use only periods where both the forecast and the actual are present.

### Errors

```json
{"error": {"code": "validation_error", "message": "delivery_date: ..."}}
```

| Situation | Status | `code` |
| --- | --- | --- |
| Invalid or out-of-range parameters | 422 | `validation_error` |
| Elexon still rate limits after retries | 429 | `rate_limited` |
| Elexon error, bad JSON, or connection failure | 502 | `upstream_unavailable` |
| Elexon timeout | 504 | `upstream_timeout` |
| Unexpected server error | 500 | `internal_error` |

HTTP 429, 502, and 503 from Elexon are retried up to `ELEXON_MAX_RETRIES` times (default 3). A numeric `Retry-After` header is honored, capped at 10 seconds. Timeouts are not retried.

## Local setup

Python 3.12 is required.

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows
# source .venv/bin/activate     # macOS or Linux
pip install -r requirements.txt
cp .env.example .env            # optional
uvicorn app.main:app --reload
```

The API listens on `http://127.0.0.1:8000`. Interactive docs are at `http://127.0.0.1:8000/docs`.

Configuration is in [backend/.env.example](backend/.env.example):

```dotenv
ELEXON_BASE_URL=https://data.elexon.co.uk/bmrs/api/v1
ELEXON_TIMEOUT_SECONDS=30
DEFAULT_DECISION_CUTOFF_UTC=13:00
FORECAST_LOOKBACK_HOURS=72
MAPE_MIN_ACTUAL_MW=1
```

## Tests

From `backend/`:

```bash
pytest
```

The default run mocks Elexon. One live test is marked `integration` and is skipped unless you ask for it:

```bash
pytest -m integration
```

That test calls the public API for 15 January 2026 and checks the 10:00Z forecast/actual pair described above.

## Docker

From the repository root:

```bash
docker compose up --build
```

The backend is published on port 8000. Compose uses `backend/.env.example` for non-secret settings and checks `/api/v1/health`. The frontend image serves the built UI on port 8080 and proxies `/api` to the backend container.

## Frontend

Node 22 is used for the Docker build. Local development needs a current Node release.

```bash
cd frontend
npm install
npm run dev
```

The app is at `http://127.0.0.1:5173`. Vite proxies `/api` to `http://127.0.0.1:8000`. Copy `frontend/.env.example` to `frontend/.env` if you need to change the API base URL.

```dotenv
VITE_API_BASE_URL=/api/v1
```

Leave that value relative for local development and for the Compose nginx proxy. If the browser calls the backend on another origin, set `VITE_API_BASE_URL` to that origin plus `/api/v1`, and set `CORS_ORIGINS` on the backend to the frontend origin. An empty `CORS_ORIGINS` leaves cross-origin requests disabled.

```bash
cd frontend
npm run build
```

There is no monthly accuracy trend. The API scores one delivery day per request and returns 24 hourly periods. FUELHH half-hours are averaged before they reach the frontend.

## Layout

```text
backend/app/config/          settings
backend/app/core/            errors and dependencies
backend/app/dto/             request and response models
backend/app/helpers/         datetime helpers
backend/app/routes.py        HTTP routes
backend/app/service.py       forecast selection and accuracy
backend/app/clients/         Elexon HTTP access
frontend/                   Wind Intelligence UI
```
