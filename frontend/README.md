# Wind Intelligence

React dashboard for the UK wind forecast API in this repository.

Local development uses the Vite proxy. Requests to `/api` are forwarded to `http://127.0.0.1:8000`, so the backend must already be running.

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. One page holds the delivery date, decision cutoff, an actuals toggle, and a switch between forecast analysis and accuracy analysis. The default delivery date is 15 January 2026, with a cutoff of 13:00 Europe/London on 14 January 2026.

`VITE_API_BASE_URL` defaults to `/api/v1`. Set it to an absolute backend URL only when the UI is served separately from the API. In that case set `CORS_ORIGINS` on the backend to the frontend origin.

```bash
npm run build
```

The production build writes static files to `dist/`. Docker serves that build with nginx and proxies `/api` to the `backend` service. From the repository root:

```bash
docker compose up --build
```

The UI is then on port 8080.
