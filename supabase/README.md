# Supabase setup

The database and sign-in for the website. The schema lives in
`migrations/0001_init.sql`.

## 1. Create the project (you do this; it needs your account)

1. Go to https://supabase.com, sign in and click **New project**.
2. Name: `aqi-health-forecast` (any name works). Region: **Mumbai (ap-south-1)** is closest to the users.
3. Set a strong database password and save it in your password manager. The app doesn't need it.
4. Wait about 2 minutes for the project to start.

## 2. Create the tables

1. In the project dashboard open **SQL Editor → New query**.
2. Paste the whole of `supabase/migrations/0001_init.sql` and click **Run**.
3. Check **Table Editor**: you should see `profiles`, `saved_forecasts`, `risk_predictions`,
   `aqi_forecasts_cache` and `model_leaderboard`, each marked **RLS enabled**.

The script is safe to run again if something fails halfway.

## 3. Turn on email sign-in

1. **Authentication → Sign In / Providers**: make sure **Email** is enabled.
2. **Authentication → URL Configuration**: set **Site URL** to `http://localhost:3000`
   for now (change it to the Vercel URL at deployment).

## 4. Collect the keys

**Project Settings → API** (or **API Keys**):

| Value | Where it goes | Secret? |
|---|---|---|
| Project URL | frontend + backend `.env` | No |
| `anon` / publishable key | frontend + backend `.env` | No (safe in the browser; RLS protects the data) |
| `service_role` / secret key | backend `.env` **only** | **Yes**: bypasses RLS. Never commit it, paste it in chat or put it in the frontend |

Copy `.env.example` (repo root) to `.env` and fill in the values. `.env` is git-ignored.

## What's in the schema

| Table | Access | Holds |
|---|---|---|
| `profiles` | Owner only (RLS) | One health profile per user; same required/optional fields as the API |
| `saved_forecasts` | Owner only | The air forecast a prediction run used |
| `risk_predictions` | Owner only | One row per forecast day of a run: level, score, confidence, borderline, alert level, inputs used |
| `aqi_forecasts_cache` | Public read, backend write | Cached city forecasts |
| `model_leaderboard` | Public read, backend write | Model rankings for the leaderboard page |

The prediction history is append-only: users can read and delete their own history,
but can't edit it. The public tables also have RLS with a read-only policy, so the public
anon key can't be used to write to them; only the backend's service role can.
