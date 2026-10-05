# Airware frontend

Next.js (App Router) + React + TypeScript, Tailwind CSS, shadcn/ui, Motion, ECharts and
Lucide React. Design spec: `../docs/frontend_design.md`.

## Run locally

Start the FastAPI backend from the repo root first (models load in about 20 s):

```bash
venv\Scripts\python -m uvicorn src.api.main:app --port 8000
```

Then the frontend:

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000
```

`NEXT_PUBLIC_API_URL` (see `.env.example`) points at the backend; it defaults to
`http://localhost:8000`.

## Pages

| Route | Status |
|---|---|
| `/` | Landing page |
| `/dashboard?city=Delhi&h=7` | Overview dashboard (city and horizon live in the URL) |
| `/sign-in` | Sign in / create account (Supabase email + password) |
| `/profile` | 3-step health-profile wizard (signed in) |
| `/risk` | Personal day-by-day risk; each new estimate is saved to history (signed in) |
| `/history`, `/history/[id]` | Saved estimates, detail view, delete (signed in) |
| `/models?tab=AQI` | Model leaderboards: AQI, PM2.5, NO2, health risk |
| `/forecast` | Placeholder, built later |

Sign-in needs `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` in
`.env.local` (the public anon key only, never the service-role key).

## Structure

| Path | Contents |
|---|---|
| `src/lib/api.ts` | Typed client for the FastAPI endpoints |
| `src/lib/aqi.ts` | CPCB categories, colours, scale position |
| `src/lib/content.ts` | Cities, example profiles, precautions, disclaimer |
| `src/lib/supabase.ts` | Supabase browser client (sign-in only; data goes through the API) |
| `src/components/auth/` | Auth provider, `RequireAuth`, sign-in view |
| `src/components/profile/`, `risk/`, `history/`, `models/` | Signed-in pages and the leaderboard |
| `src/components/dashboard/` | Dashboard data hooks and sections |
| `src/components/landing/` | Landing page sections |
| `src/components/charts/` | ECharts wrapper, forecast chart, sparkline |
| `src/components/theme/` | Light/dark theme (class on `<html>`, set before paint) |

Every page is checked at 1280, 1536 and 1920 px wide (a 1920x1080 screen at 150%, 125%
and 100% Windows scaling). Layout breakpoints: `lg` (1024 px) and `wide` (1700 px).
