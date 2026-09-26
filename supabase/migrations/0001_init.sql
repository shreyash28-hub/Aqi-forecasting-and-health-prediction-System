-- ============================================================================
-- AQI Forecast & Health Risk: initial Supabase schema
-- Run once in the Supabase SQL editor (Dashboard -> SQL Editor -> New query).
-- Safe to re-run: every object is created with IF NOT EXISTS / OR REPLACE.
--
-- Private tables (RLS: each user sees and changes only their own rows):
--   profiles, saved_forecasts, risk_predictions
-- Public tables (anyone can read; only the backend's service role can write):
--   aqi_forecasts_cache, model_leaderboard
-- ============================================================================


-- ---------------------------------------------------------------------------
-- Helper: keep updated_at current
-- ---------------------------------------------------------------------------
create or replace function public.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;


-- ---------------------------------------------------------------------------
-- profiles: one health profile per user, filled once and reused
-- Required fields match the API (src/api/schemas.py): the exposure fields
-- (occupation, area_type, mask_usage, outdoor_hours) are required because
-- defaulting them understated risk. bmi, exercise_hours, family_history optional.
-- ---------------------------------------------------------------------------
create table if not exists public.profiles (
  user_id        uuid primary key references auth.users (id) on delete cascade,
  age            smallint     not null check (age between 1 and 110),
  gender         text         not null check (gender in ('F', 'M')),
  condition      text         not null check (condition in
                   ('No Condition', 'Asthma', 'COPD', 'HeartDisease', 'Diabetes', 'Hypertension')),
  smoker         boolean      not null,
  occupation     text         not null check (occupation in
                   ('Homemaker', 'Indoor Worker', 'Outdoor Worker', 'Retired', 'Student')),
  area_type      text         not null check (area_type in ('Commercial', 'Industrial', 'Residential')),
  mask_usage     text         not null check (mask_usage in ('No', 'Sometimes', 'Yes')),
  outdoor_hours  numeric(4,1) not null check (outdoor_hours between 0 and 24),     -- hours per day
  bmi            numeric(4,1)          check (bmi between 10 and 70),
  exercise_hours numeric(4,1)          check (exercise_hours between 0 and 40),    -- hours per week
  family_history boolean,                                                           -- respiratory disease
  city           text,                                                              -- last selected city (UI convenience)
  created_at     timestamptz  not null default now(),
  updated_at     timestamptz  not null default now()
);

drop trigger if exists profiles_set_updated_at on public.profiles;
create trigger profiles_set_updated_at
  before update on public.profiles
  for each row execute function public.set_updated_at();


-- ---------------------------------------------------------------------------
-- saved_forecasts: the air forecast a user's prediction run was based on
-- ---------------------------------------------------------------------------
create table if not exists public.saved_forecasts (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid not null default auth.uid() references auth.users (id) on delete cascade,
  city          text not null,
  horizon       smallint not null check (horizon between 1 and 30),
  origin_date   date not null,                 -- last observed day; forecast starts the day after
  model_used    jsonb not null,                -- {"AQI": "SARIMA", "PM2.5": "Prophet", "NO2": ...}
  forecast_json jsonb not null,                -- [{date, aqi, aqi_category, pm25, no2}, ...]
  generated_at  timestamptz not null default now()
);

create index if not exists saved_forecasts_user_time_idx
  on public.saved_forecasts (user_id, generated_at desc);


-- ---------------------------------------------------------------------------
-- risk_predictions: one row per forecast day of a prediction run (history)
-- ---------------------------------------------------------------------------
create table if not exists public.risk_predictions (
  id                  uuid primary key default gen_random_uuid(),
  user_id             uuid not null default auth.uid() references auth.users (id) on delete cascade,
  forecast_id         uuid not null references public.saved_forecasts (id) on delete cascade,
  city                text not null,
  date_of_prediction  date not null,           -- the forecast day this risk is for
  risk_level          text not null check (risk_level in ('Low', 'Moderate', 'High', 'Severe')),
  risk_score          numeric(6,3) not null check (risk_score >= 0),
  confidence          numeric(4,3) check (confidence between 0 and 1),
  probabilities       jsonb,                   -- {"Low": .., "Moderate": .., "High": .., "Severe": ..}
  borderline          boolean not null default false,
  risk_range          text,                    -- e.g. "Moderate-High" when borderline
  alert_level         text not null check (alert_level in ('Low', 'Moderate', 'High', 'Severe')),
  model_used          jsonb not null,          -- {"feature_set": .., "classification": .., "regression": ..}
  input_snapshot_json jsonb not null,          -- profile + air values actually used
  predicted_at        timestamptz not null default now()
);

create index if not exists risk_predictions_user_time_idx
  on public.risk_predictions (user_id, predicted_at desc);
create index if not exists risk_predictions_forecast_idx
  on public.risk_predictions (forecast_id);


-- ---------------------------------------------------------------------------
-- Public tables: readable by everyone, written only by the backend
-- ---------------------------------------------------------------------------
create table if not exists public.aqi_forecasts_cache (
  city          text not null,
  horizon       smallint not null check (horizon between 1 and 30),
  origin_date   date not null,
  model_used    jsonb not null,
  forecast_json jsonb not null,
  generated_at  timestamptz not null default now(),
  primary key (city, horizon)
);

create table if not exists public.model_leaderboard (
  task          text not null,                 -- e.g. aqi_forecast, pm25_forecast, health_classification
  scope         text not null default '',      -- city for forecasting tasks, feature set for health
  model_name    text not null,
  metrics_json  jsonb not null,
  is_selected   boolean not null default false,
  trained_at    timestamptz not null default now(),
  primary key (task, scope, model_name)
);


-- ---------------------------------------------------------------------------
-- Row Level Security
-- ---------------------------------------------------------------------------
alter table public.profiles            enable row level security;
alter table public.saved_forecasts     enable row level security;
alter table public.risk_predictions    enable row level security;
-- Public tables also get RLS: without it, Supabase's API would let anyone
-- *write* to them with the public anon key. With RLS + a read-only policy,
-- anyone can read and only the service role (which bypasses RLS) can write.
alter table public.aqi_forecasts_cache enable row level security;
alter table public.model_leaderboard   enable row level security;

-- profiles: owner can read, create, update and delete their own row
drop policy if exists "profiles: owner select" on public.profiles;
create policy "profiles: owner select" on public.profiles
  for select to authenticated using ((select auth.uid()) = user_id);
drop policy if exists "profiles: owner insert" on public.profiles;
create policy "profiles: owner insert" on public.profiles
  for insert to authenticated with check ((select auth.uid()) = user_id);
drop policy if exists "profiles: owner update" on public.profiles;
create policy "profiles: owner update" on public.profiles
  for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
drop policy if exists "profiles: owner delete" on public.profiles;
create policy "profiles: owner delete" on public.profiles
  for delete to authenticated using ((select auth.uid()) = user_id);

-- saved_forecasts / risk_predictions: history is append-only (no update policy)
drop policy if exists "saved_forecasts: owner select" on public.saved_forecasts;
create policy "saved_forecasts: owner select" on public.saved_forecasts
  for select to authenticated using ((select auth.uid()) = user_id);
drop policy if exists "saved_forecasts: owner insert" on public.saved_forecasts;
create policy "saved_forecasts: owner insert" on public.saved_forecasts
  for insert to authenticated with check ((select auth.uid()) = user_id);
drop policy if exists "saved_forecasts: owner delete" on public.saved_forecasts;
create policy "saved_forecasts: owner delete" on public.saved_forecasts
  for delete to authenticated using ((select auth.uid()) = user_id);

drop policy if exists "risk_predictions: owner select" on public.risk_predictions;
create policy "risk_predictions: owner select" on public.risk_predictions
  for select to authenticated using ((select auth.uid()) = user_id);
drop policy if exists "risk_predictions: owner insert" on public.risk_predictions;
create policy "risk_predictions: owner insert" on public.risk_predictions
  for insert to authenticated with check (
    (select auth.uid()) = user_id
    -- the run must belong to the same user
    and exists (select 1 from public.saved_forecasts f
                where f.id = forecast_id and f.user_id = (select auth.uid()))
  );
drop policy if exists "risk_predictions: owner delete" on public.risk_predictions;
create policy "risk_predictions: owner delete" on public.risk_predictions
  for delete to authenticated using ((select auth.uid()) = user_id);

-- public tables: read-only for everyone
drop policy if exists "aqi_forecasts_cache: public read" on public.aqi_forecasts_cache;
create policy "aqi_forecasts_cache: public read" on public.aqi_forecasts_cache
  for select to anon, authenticated using (true);
drop policy if exists "model_leaderboard: public read" on public.model_leaderboard;
create policy "model_leaderboard: public read" on public.model_leaderboard
  for select to anon, authenticated using (true);


-- ---------------------------------------------------------------------------
-- Table privileges (RLS decides which rows; these decide which operations)
-- ---------------------------------------------------------------------------
grant select, insert, update, delete on public.profiles         to authenticated;
grant select, insert, delete         on public.saved_forecasts  to authenticated;
grant select, insert, delete         on public.risk_predictions to authenticated;
grant select on public.aqi_forecasts_cache, public.model_leaderboard to anon, authenticated;
revoke insert, update, delete on public.aqi_forecasts_cache, public.model_leaderboard from anon, authenticated;
-- Supabase grants broad default privileges on new public tables; tighten them.
revoke all on public.profiles, public.saved_forecasts, public.risk_predictions from anon;
revoke update on public.saved_forecasts, public.risk_predictions from authenticated;
