# Airware frontend: design decisions

Agreed with the user on 26 Sep 2026 before any frontend code was written. **Coding starts
only when the user says so.** Approved visual references (serve the folder with
`python -m http.server 8765 -d docs/design`, then open the file; add `?theme=light` for
light mode):
- `docs/design/airware_landing_mockup.html`: landing page (`/`)
- `docs/design/airware_overview_mockup.html`: dashboard (`/dashboard`)

## Name

**Airware**.

## Stack (finalized)

| Part | Choice |
|---|---|
| Framework | Next.js (App Router) |
| Language | React + TypeScript |
| Styling | Tailwind CSS |
| Components | shadcn/ui |
| Animation | Motion (npm package `motion`, imported from `motion/react`) |
| Charts | ECharts |
| Icons | Lucide React |
| Map | Leaflet + OpenStreetMap tiles |
| Hospital data | Overpass API |
| Sign-in | `@supabase/supabase-js` (part of the Supabase choice) |

Recommended defaults, not yet explicitly confirmed by the user: code in a `frontend/`
folder in this repo; npm; a small in-house ECharts React wrapper; `react-leaflet` for the map.

## Site structure

| Page | Route | Status |
|---|---|---|
| Landing page | `/` | Mockup approved |
| Dashboard (Overview) | `/dashboard` | Mockup approved |
| Sign in | `/sign-in` | Planned |
| Profile setup wizard | `/profile` | Planned |
| My risk | `/risk` | Planned |
| History | `/history` | Planned |
| Models leaderboard | `/models` | Planned |
| Hospitals map | inside My risk, when `alert_level` is High or Severe | Planned, later |

## Visual direction

Product pages are a **data-first dashboard**, like IQAir or Windy. The landing page
introduces the product in the same visual language and links into the dashboard.

**Avoid the "AI template" look**, which the user explicitly rejected in the first mockup:
- no giant centred hero headline
- no gradient or glowing blob backgrounds
- no gradient text
- no pill badges
- no oversized rounded cards

**Typography:** IBM Plex Sans for UI text, IBM Plex Mono with tabular figures for all
numbers.

**Colour:**
- neutral greys for surfaces and text
- **one** restrained brand colour, deep teal: `#0b6e74` in light mode, `#3fb5b8` in dark
- **CPCB AQI colours are reserved for data**, never used as brand colours: Good `#2e9e5b`,
  Satisfactory `#8cc152`, Moderate `#e8b923`, Poor `#ea8a2e`, Very poor `#d9453f`,
  Severe `#8e2436`
- risk levels reuse them: Low green, Moderate yellow, High orange, Severe red

**Shape:**
- corner radius 10 px on cards and 7 px on controls
- 1 px borders
- almost no shadows

**Themes:**
- light and dark
- the default follows the system setting
- a sun/moon toggle in the header, with the user's choice remembered
- AQI colours are identical in both themes

**Motion:** subtle only:
- cards fade up about 8 px on load, staggered
- charts draw in
- small hover states

Everything is disabled under `prefers-reduced-motion`.

**Copy:** sentence case; short, plain labels.

## Layout

- Full width: fluid up to **1840 px**, 32 px side gutters, 12-column grid, 16 px gaps.
- **The user's screen is 1920×1080 with Windows display scaling, which is about 1280 CSS px
  wide at 150%.** Every page must be designed and checked at **1280, 1536 and 1920 px**,
  with no half-empty rows and no horizontal scroll.
- Overview breakpoints:

| Width | Row 1 | Row 2 | Row 3 | Row 4 |
|---|---|---|---|---|
| >= 1500 px | Tomorrow (3) + chart (9) | Risk (5) + pollutants (4) + precautions (3) | All cities (12) | |
| 1024-1499 px | Tomorrow (4) + chart (8) | Risk (12) | Pollutants (6) + precautions (6) | All cities (12) |
| < 1024 px | everything stacked | | | |

## Headers

**Landing header:**
- logo mark and "Airware" wordmark
- anchor links: How it works · Features · Models · Data · FAQ
- theme toggle
- Sign in
- **Open dashboard** (primary button)

**App header** (dashboard and signed-in pages):
- logo mark and wordmark
- nav: Overview · Forecast · My risk · History · Models
- city selector
- theme toggle
- Sign in

## Landing page (approved)

1. **Hero, left-aligned (not centred):**
   - eyebrow "Air quality forecasts for Indian cities"
   - headline *"Plan your week around the air you'll breathe."*
   - one-line description
   - buttons: **Open the dashboard** (primary) and **Check my risk**
   - a facts row: 6 cities · 7 and 30-day forecasts · 6 models compared per city · health model F1 0.87
   - on the right, a **live dashboard preview card** with city tabs, tomorrow's AQI, a 7-day chart and a 7-day risk strip
2. **Live city strip:** tomorrow's AQI and category for all six cities, linking to the dashboard.
3. **"The same air affects people differently":** two profiles on the same Delhi week.
   - Aarav, 25: no condition, residential area, wears a mask, 1 h outdoors → **Low** all week
   - Ramesh, 67: COPD, industrial area, no mask, 3 h outdoors → **Moderate** all week

   Both were verified with the deployed model; re-check them if the models change.
4. **How it works:** 4 numbered steps (pick your city, add your profile once, see risk day
   by day, act on it).
5. **Features:** six cards (forecasts, personal risk, precautions, nearby hospitals,
   history, city comparison).
6. **Behind the forecasts:**
   - the testing process, with 6 models, 6 test periods, 5–33% lower error than the best baseline, and F1 0.87
   - a per-city table of the model in use and its improvement over the baseline
   - a link to the leaderboard

   Numbers come from `/api/leaderboard/*`, not hard-coded.
7. **Data and methodology:**
   - CPCB monitoring data
   - the full CPCB AQI scale (six bands with ranges and meanings)
   - three method notes: cities, cleaning, and the risk model
8. **Privacy** (only you can see your data; no account needed to browse; delete anytime)
   and an **FAQ** (What is AQI · accuracy · not a medical diagnosis · account · free).
9. **Closing call to action** on a teal band, and a **footer** (product, learn and account
   links, plus the disclaimer).

Open question: whether to mention the course project (team, institute, guide). Left out
for now so it reads as a product.

## Dashboard / Overview page (approved)

1. **Page head:** "<City> air quality forecast", plus issued date, model used, and source
   (CPCB monitoring stations). A 7 days / 30 days segmented toggle.
2. **City tabs:** all six cities, each with a category-coloured dot and tomorrow's AQI;
   click to switch.
3. **Tomorrow card:**
   - large AQI number and category chip
   - CPCB scale bar of six **equal-width** bands, with the marker placed *within its band*
     rather than linearly across 0-500
   - the CPCB health advisory for the category
   - range over the horizon, peak day, and tomorrow's PM2.5
4. **AQI forecast chart (ECharts):**
   - line coloured by CPCB category, with faint category bands behind it
   - value labels on the 7-day view
   - tooltip with date, AQI and category
   - category legend
5. **Pollutants:** PM2.5 and NO2 for tomorrow with sparklines over the horizon.
6. **Your health risk:**
   - profile tags
   - seven day cards: weekday and date, `risk_range` (shows a range when borderline),
     confidence bar, score
   - "Update estimate" button
   - the disclaimer: *Estimated risk for decision support only. This is not a medical
     diagnosis.*
7. **Precautions:** advice matched to the risk level; this is where the assistant goes later.
8. **All cities table:** city, AQI tomorrow, category chip, 7-day sparkline, 7-day range,
   PM2.5, NO2, forecast model; rows are clickable.
9. **Footer:** data source and the disclaimer.

## Other pages (planned, same design language)

- **Sign in:** centred card, email sign-in via Supabase.
- **Profile setup:** a one-time 3-step wizard with a progress indicator. The 8 required
  fields match the API; BMI, exercise and family history are optional.
- **My risk:** the day-by-day view following the forecast curve, with confidence and
  borderline ranges.
- **History:** past runs, with a click-through to details.
- **Models:** the leaderboard, from `/api/leaderboard/*`.
- **Hospitals (later):** Leaflet map and contact cards when `alert_level` is High or Severe.
  Enquiry only, no booking.

## Content rules (from CLAUDE.md)

- The health disclaimer is always visible wherever risk is shown.
- No "synthetic" wording anywhere in the UI.
- No caveat about the 2020 data cutoff unless the user asks for one.

## Deferred

- **Live 2026 data:** to be done after the frontend, so the site shows today's AQI rather
  than July 2020. Never relabel 2020 dates. OpenAQ station data is recommended (free API
  key from the user); Open-Meteo is a keyless fallback made of model estimates. See the
  `CLAUDE.md` decisions log.
