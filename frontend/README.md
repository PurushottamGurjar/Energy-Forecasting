# Wind Intelligence

React dashboard for the UK wind forecast API in this repository.

Local development uses the Vite proxy to forward `/api` requests to the deployed Render backend.

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. One page holds the delivery date, decision cutoff, an actuals toggle, and a switch between forecast analysis and accuracy analysis. The default delivery date is 15 January 2026, with a cutoff of 13:00 Europe/London on 14 January 2026.

`VITE_API_BASE_URL` defaults to `/api/v1`. The Vite development server proxies `/api` requests to `https://wind-energy-forecasting-2c1x.onrender.com`, so local development uses the deployed API without requiring browser CORS configuration.

```bash
npm run build
```

The production build writes static files to `dist/`. Docker serves that build with nginx and proxies `/api` to `https://wind-energy-forecasting-2c1x.onrender.com` by default. Set `API_UPSTREAM` to another API origin when deploying the image. Docker Compose overrides it to use its local `backend` service. From the repository root:

```bash
docker compose up --build
```

The UI is then on port 8080.

For Vercel, set the project Root Directory to `frontend`. The `vercel.json` rewrite forwards `/api/...` requests to the Render backend, so the browser continues to call the same-origin `/api/v1` path.
