# Keeping the live forecasts current

The site forecasts from today because the models are retrained every day on the latest CPCB
station readings (OpenAQ), and today's forecast is nudged with the readings so far
(`src/nowcast.py`). Two things keep this running without you:

| What | How often | Where it runs | What it does |
|---|---|---|---|
| **Daily refresh** | daily at 02:37 IST, again at 04:37 IST as a backup (GitHub often starts scheduled runs hours late) | GitHub Actions (`.github/workflows/refresh-live.yml`) | fetches the last days of readings, merges them into the daily data, retrains the 18 live models, uploads one bundle to Supabase Storage |
| **Hourly top-up** | every `LIVE_REFRESH_MINUTES` (e.g. 60) | inside the API | downloads the newest hourly readings (about 144 requests) for today's figure; checks for a new daily bundle; reloads the forecasts |

Nothing is committed daily (the models are ~25 MB and change every run), and a running API
reloads by itself when its files change, so no redeploy or restart is needed.

## On your own computer

```bash
venv\Scripts\python -m src.refresh_live                 # the daily refresh (about 2-4 minutes)
venv\Scripts\python -m src.refresh_live --nowcast-only  # just today's readings (about 3 minutes)
```

A running API picks the new files up within about 10 seconds of the next request. To have the
API itself fetch new readings, start it with `LIVE_REFRESH_MINUTES=60` set.

## One-time setup for the deployed site

1. **Supabase Storage:** create a bucket named `live` and make it **public** (Storage > New bucket > Public).
2. **GitHub repository settings > Secrets and variables > Actions**
   - Secrets: `OPENAQ_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` (the service-role key
     stays in GitHub; the API never gets it).
   - Variable: `LIVE_BUNDLE_URL` = `https://<project-ref>.supabase.co/storage/v1/object/public/live/live_bundle.tar.gz`
3. **Run the workflow once by hand** (Actions > Refresh live forecasts > Run workflow) to create the first bundle.
4. **API host (Render or Railway) environment variables:** `LIVE_BUNDLE_URL` (same URL),
   `LIVE_REFRESH_MINUTES=60`, `OPENAQ_API_KEY`. Install from `requirements.lock.txt`: the models are
   pickled files that only load under the library versions they were trained with, and the job and
   the API must use the same ones. If you change a version, change the file and retrain.

At startup the API downloads the latest bundle (falling back to the models in the repository if
that fails), and then checks again every `LIVE_REFRESH_MINUTES`.

## Limits

- Free hosting may put the API to sleep when idle; it loads the bundle again when it wakes.
- OpenAQ allows about 2,000 requests an hour. One refresh is about 144, so hourly is well within it.
- The daily job only adds the last 6 days to the saved daily data. If it fails for more than
  4 days in a row, the days in between stay empty (the models interpolate short gaps).
- The model comparison (`--evaluate`) needs the Kaggle file and is run by hand, not by the job.
- The two OpenAQ-dependent steps log a warning and carry on if OpenAQ is down; the API keeps
  serving the last forecasts it has.
