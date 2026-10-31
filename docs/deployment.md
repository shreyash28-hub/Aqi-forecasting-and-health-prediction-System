# Deploying Airware

| Part | Host | Config |
|---|---|---|
| API (FastAPI) | Render, Singapore region | `render.yaml` (Blueprint) |
| Website (Next.js) | Vercel | `frontend/` as the project root |
| Daily model refresh | GitHub Actions + Supabase Storage | `.github/workflows/refresh-live.yml`, see `docs/live_refresh.md` |

## Memory: why the API fits a 512 MB server

Loading the 18 forecasters needs statsmodels, Prophet, XGBoost and PyTorch, about 490 MB
in all. The models change once a day, so the daily job saves their 30-day forecasts to
`data/processed/live_forecasts.json` (`src/forecast_export.py`) and the API serves those:
it needs about 170 MB and starts in ~2 s. It only loads the models if that file is missing
or out of step with them (then it needs ~490 MB, too close to 512 MB on Render's free and
Starter plans).

## 1. API on Render

1. Push the repository to GitHub.
2. Render dashboard > **New** > **Blueprint** > connect GitHub and pick
   `Aqi-forecasting-and-health-prediction-System`. Render reads `render.yaml` and proposes the
   `airware-api` web service.
3. Fill in the settings marked "sync: false":
   - `SUPABASE_URL`, `SUPABASE_ANON_KEY`: from your local `.env` (the **anon** key; the
     service-role key never goes on the API).
   - `OPENAQ_API_KEY`: from `.env`.
   - `ALLOWED_ORIGINS`: leave empty for now; set it after step 2 below.
4. **Apply**. The first build takes ~5-10 minutes (PyTorch is large). Then open
   `https://<service>.onrender.com/api/health`: it should show 6 cities and 18 forecasters.

Plan: **free** sleeps after 15 minutes without visits, and the next visit waits ~1 minute
while it wakes. **Starter** ($7/month) stays awake. Change `plan:` in `render.yaml` or in the
dashboard.

## 2. Website on Vercel

1. Vercel > **Add New** > **Project** > import the same repository.
2. **Root Directory**: `frontend`. Framework: Next.js (detected).
3. Environment variables:
   - `NEXT_PUBLIC_API_URL` = `https://<service>.onrender.com`
   - `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`: from `frontend/.env.local`.
4. Deploy, and note the site address (e.g. `https://airware.vercel.app`).

## 3. Connect them

1. Render > `airware-api` > Environment: `ALLOWED_ORIGINS` = the Vercel address (no trailing
   slash). Several addresses: comma-separated.
2. Supabase > Authentication > URL Configuration: **Site URL** = the Vercel address, and add
   `https://<your-site>/**` to **Redirect URLs**, so sign-up confirmation links lead back to
   the live site.

## Checks after deploying

- `/api/health` on Render: `"cities": 6`.
- The dashboard shows today's date and "Today updated with readings to HH:MM".
- Sign in, fill the profile, open My risk.
- Hospitals: the first search for an area takes 30-70 s (OpenStreetMap's Overpass service);
  repeats are instant until the server restarts.
