"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { ArrowRight, Check, HeartPulse, History, LineChart as LineIcon, ListChecks, MapPin, Table2, User } from "lucide-react";
import { LandingHeader } from "@/components/layout/landing-header";
import { SiteFooter } from "@/components/layout/footer";
import { CategoryChip, Reveal } from "@/components/common";
import { ForecastChart } from "@/components/charts/forecast-chart";
import { Skeleton } from "@/components/ui/skeleton";
import { useCityForecasts, useExampleRisk } from "@/components/dashboard/use-dashboard-data";
import { useAsync } from "@/hooks/use-async";
import { api, type ForecastLeaderboard, type RiskResponse } from "@/lib/api";
import { AQI_CATEGORIES, RISK_COLOR, aqiCategory } from "@/lib/aqi";
import { CITIES, EXAMPLE_PROFILES } from "@/lib/content";
import { fmtWeekday } from "@/lib/format";
import { cn } from "@/lib/utils";

const Eyebrow = ({ children }: { children: React.ReactNode }) => <span className="text-[13px] font-semibold tracking-wide text-brand-ink">{children}</span>;
const H2 = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <h2 className={cn("mt-2.5 text-[clamp(28px,2.4vw,40px)] leading-[1.15] font-semibold tracking-tight", className)}>{children}</h2>
);
function SectionHead({ eyebrow, title, text }: { eyebrow: string; title: string; text?: string }) {
  return (
    <Reveal className="mb-11 grid items-end gap-12 lg:grid-cols-2">
      <div><Eyebrow>{eyebrow}</Eyebrow><H2>{title}</H2></div>
      {text && <p className="max-w-xl text-muted-foreground">{text}</p>}
    </Reveal>
  );
}

/** Per-city improvement of the deployed model over the best naive baseline (mean RMSE). */
function improvements(board?: ForecastLeaderboard) {
  if (!board) return [];
  return Object.entries(board.cities).map(([city, c]) => {
    const rmse = (m: string) => c.ranking.find((r) => r.model === m)?.mean_rmse ?? NaN;
    return { city, model: c.deployed_model, pct: (rmse(c.deployed_model) / rmse(c.best_baseline) - 1) * 100 };
  }).sort((a, b) => a.pct - b.pct);
}

export function LandingView() {
  const forecasts = useCityForecasts();
  const board = useAsync((s) => api.forecastLeaderboard("AQI", s), []);
  const health = useAsync((s) => api.healthLeaderboard(s), []);
  const compare = useAsync(async (s) => {
    const [aarav, ramesh] = await Promise.all([
      api.predictRisk({ city: "Delhi", horizon: 7, profile: EXAMPLE_PROFILES.aarav.profile }, s),
      api.predictRisk({ city: "Delhi", horizon: 7, profile: EXAMPLE_PROFILES.ramesh.profile }, s),
    ]);
    return { aarav, ramesh };
  }, []);

  const gains = useMemo(() => improvements(board.data), [board.data]);
  const range = gains.length ? `${Math.round(-gains[gains.length - 1].pct)}–${Math.round(-gains[0].pct)}%` : "5–33%";
  const f1 = health.data?.tasks.classification.ranking.find((r) => r.selected && r.feature_set === "aqi_pm25_no2")?.test.f1_weighted;
  const f1Text = f1 ? f1.toFixed(2) : "0.87";

  return (
    <div className="bg-background">
      <LandingHeader />
      <main>
        <Hero forecasts={forecasts.data?.byCity} f1={f1Text} />
        <CityStrip byCity={forecasts.data?.byCity} />
        <Comparison data={compare.data} />
        <HowItWorks />
        <Features />
        <Models gains={gains} range={range} f1={f1Text} />
        <DataSection />
        <PrivacyFaq range={range} />
        <FinalCta />
      </main>
      <SiteFooter />
    </div>
  );
}

// ------------------------------------------------------------------ hero

function Hero({ forecasts, f1 }: { forecasts?: Record<string, import("@/lib/api").ForecastResponse>; f1: string }) {
  const [city, setCity] = useState<string>("Delhi");
  const risk = useExampleRisk(city);
  const f = forecasts?.[city];
  const week = f?.days.slice(0, 7);
  const facts = [["6", "cities covered"], ["7 · 30", "day forecasts"], ["6", "models compared per city"], [f1, "health model F1 score"]];
  return (
    <section className="shell grid items-center gap-[clamp(32px,4vw,72px)] pt-[clamp(48px,5vw,80px)] pb-14 lg:grid-cols-[5fr_7fr]">
      <Reveal>
        <Eyebrow>Air quality forecasts for Indian cities</Eyebrow>
        <h1 className="mt-3.5 mb-5 text-[clamp(38px,3.6vw,60px)] leading-[1.08] font-semibold tracking-tight">Plan your week around the air you&apos;ll breathe.</h1>
        <p className="max-w-[620px] text-[clamp(16px,1.15vw,19px)] text-muted-foreground">
          Airware forecasts air quality up to 30 days ahead and turns it into a personal health-risk estimate, based on your age, health conditions and daily exposure.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link href="/dashboard" className="flex h-[46px] items-center gap-2 rounded-[7px] bg-brand px-5 font-medium text-on-brand hover:brightness-110">
            Open the dashboard<ArrowRight className="size-4" aria-hidden />
          </Link>
          <Link href="/risk" className="flex h-[46px] items-center rounded-[7px] border border-border-strong bg-card px-5 font-medium hover:bg-muted">Check my risk</Link>
        </div>
        <div className="mt-10 grid grid-cols-4 gap-5 border-t pt-6">
          {facts.map(([v, l]) => (
            <div key={l} className="flex flex-col">
              <b className="num text-[clamp(20px,1.6vw,26px)] font-medium whitespace-nowrap">{v}</b>
              <span className="text-[13px] leading-tight text-faint">{l}</span>
            </div>
          ))}
        </div>
      </Reveal>

      <Reveal delay={0.1} className="overflow-hidden rounded-[12px] border bg-card shadow-[0_1px_2px_rgba(0,0,0,.04),0_24px_48px_-24px_rgba(10,30,40,.25)]">
        <div className="flex items-center gap-2.5 border-b px-4 py-3 text-[13px] text-muted-foreground">
          <b className="font-semibold text-foreground">{city}</b> · AQI forecast, next 7 days
          <div className="ml-auto flex gap-1.5" role="tablist" aria-label="Preview city">
            {CITIES.map((c) => (
              <button key={c} role="tab" aria-selected={c === city} onClick={() => setCity(c)}
                className={cn("rounded-[6px] border px-2 py-0.5 text-xs", c === city ? "border-brand text-brand-ink" : "hover:bg-muted")}>
                {c.slice(0, 3)}
              </button>
            ))}
          </div>
        </div>
        <div className="grid grid-cols-[190px_minmax(0,1fr)]">
          <div className="border-r p-4">
            <div className="text-[13px] text-muted-foreground">Tomorrow</div>
            {week ? <>
              <div className="num my-2 text-[52px] leading-none font-medium tracking-tighter">{Math.round(week[0].aqi)}</div>
              <CategoryChip aqi={week[0].aqi} />
              <dl className="mt-4 grid gap-1.5 text-[13px] [&>div]:flex [&>div]:justify-between [&_dt]:text-muted-foreground [&_dd]:font-medium">
                <div><dt>7-day range</dt><dd className="num">{Math.round(Math.min(...week.map((d) => d.aqi)))}–{Math.round(Math.max(...week.map((d) => d.aqi)))}</dd></div>
                <div><dt>PM2.5</dt><dd className="num">{Math.round(week[0].pm25 ?? 0)}</dd></div>
                <div><dt>NO2</dt><dd className="num">{Math.round(week[0].no2 ?? 0)}</dd></div>
                <div><dt>Model</dt><dd>{f?.models.AQI?.model}</dd></div>
              </dl>
            </> : <Skeleton className="mt-3 h-40" />}
          </div>
          {week ? <ForecastChart days={week} compact className="h-[250px]" /> : <Skeleton className="m-4 h-[220px]" />}
        </div>
        <div className="grid grid-cols-7 gap-1.5 border-t px-4 pt-3.5 pb-4">
          {(risk.data?.days ?? Array.from({ length: 7 })).slice(0, 7).map((d, i) => d ? (
            <div key={d.date} className="rounded-[7px] border px-2 py-1.5 text-[11.5px] text-faint">
              {fmtWeekday(d.date)}<b className="mt-0.5 block text-[12.5px] font-semibold text-foreground">{d.risk_range}</b>
              <i className="mt-1.5 block h-[3px] rounded-full" style={{ width: `${Math.round(d.confidence * 100)}%`, background: RISK_COLOR[d.risk_level] }} />
            </div>
          ) : <Skeleton key={i} className="h-[52px]" />)}
        </div>
      </Reveal>
    </section>
  );
}

// ------------------------------------------------------------------ city strip

function CityStrip({ byCity }: { byCity?: Record<string, import("@/lib/api").ForecastResponse> }) {
  return (
    <section className="shell">
      <Reveal className="grid grid-cols-3 overflow-hidden rounded-[12px] border bg-card xl:grid-cols-6">
        {(byCity ? Object.values(byCity) : CITIES.map(() => undefined)).map((f, i) => f ? (
          <Link key={f.city} href={`/dashboard?city=${f.city}`} className="border-r border-b px-5 py-4 transition-colors hover:bg-muted xl:border-b-0 xl:last:border-r-0 [&:nth-child(3)]:border-r-0 xl:[&:nth-child(3)]:border-r">
            <div className="flex items-center gap-2 font-medium"><i className="size-2 rounded-full" style={{ background: aqiCategory(f.days[0].aqi).color }} />{f.city}</div>
            <div className="num mt-1.5 text-[30px] font-medium">{Math.round(f.days[0].aqi)}</div>
            <div className="text-[13px] text-muted-foreground">{aqiCategory(f.days[0].aqi).name}</div>
          </Link>
        ) : <div key={i} className="border-r px-5 py-4"><Skeleton className="h-[78px]" /></div>)}
      </Reveal>
      <div className="mt-3 flex justify-between px-0.5 text-[13px] text-faint">
        <span>Tomorrow&apos;s forecast AQI · CPCB scale</span>
        <Link href="/dashboard" className="hover:text-foreground">See all cities in the dashboard →</Link>
      </div>
    </section>
  );
}

// ------------------------------------------------------------------ comparison

function Comparison({ data }: { data?: { aarav: RiskResponse; ramesh: RiskResponse } }) {
  const people = [
    { key: "aarav" as const, ex: EXAMPLE_PROFILES.aarav },
    { key: "ramesh" as const, ex: EXAMPLE_PROFILES.ramesh },
  ];
  const meanAqi = data ? Math.round(data.ramesh.days.reduce((s, d) => s + d.aqi, 0) / data.ramesh.days.length) : undefined;
  return (
    <section className="py-[clamp(56px,7vw,104px)]">
      <div className="shell">
        <SectionHead eyebrow="Why Airware" title="The same air affects people differently."
          text="A city's AQI tells you how polluted the air is, not what it means for you. Age, lung or heart conditions, time spent outdoors and mask use all change the risk. Airware combines the forecast with your profile." />
        <p className="mb-4 text-center text-sm text-muted-foreground">
          Same city, same week: Delhi, forecast AQI about <b className="num font-medium">{meanAqi ?? "…"}</b>{meanAqi && <> ({aqiCategory(meanAqi).name})</>}
        </p>
        <div className="grid gap-5 md:grid-cols-2">
          {people.map(({ key, ex }, i) => {
            const r = data?.[key];
            const level = r?.summary.highest_alert_level;
            const allSame = r && r.days.every((d) => d.risk_level === r.days[0].risk_level);
            return (
              <Reveal key={key} delay={i * 0.08} className="rounded-[12px] border bg-card p-6">
                <div className="flex items-center gap-3">
                  <span className="grid size-10 place-items-center rounded-full bg-muted text-muted-foreground"><User className="size-5" aria-hidden /></span>
                  <div><h3 className="font-semibold">{ex.name}</h3><span className="text-sm text-muted-foreground">{ex.summary}</span></div>
                </div>
                <div className="mt-3.5 flex flex-wrap gap-1.5">
                  {(key === "ramesh" ? ex.tags.slice(1) : ex.tags).map((t) => <span key={t} className="rounded-[5px] bg-muted px-2 py-0.5 text-xs text-muted-foreground">{t}</span>)}
                </div>
                <div className="mt-5 flex items-baseline gap-3 border-t pt-4">
                  {level && r ? <>
                    <b className="text-[26px] font-semibold" style={{ color: `color-mix(in srgb, ${RISK_COLOR[r.days[0].risk_level]} 80%, var(--foreground))` }}>{r.days[0].risk_level}</b>
                    <span className="text-[13px] text-muted-foreground">estimated risk {allSame ? "for all 7 days" : "on the first day"}{level !== "Low" ? ", with precautions" : ""}</span>
                  </> : <Skeleton className="h-8 w-60" />}
                </div>
              </Reveal>
            );
          })}
        </div>
      </div>
    </section>
  );
}

// ------------------------------------------------------------------ how it works

function HowItWorks() {
  const steps = [
    ["Pick your city", "See the air-quality forecast for the next 7 or 30 days, with PM2.5 and NO2."],
    ["Add your profile once", "Age, health conditions and daily exposure. Saved securely and reused on every visit."],
    ["See your risk day by day", "A risk level and confidence for each day, following the forecast curve."],
    ["Act on it", "Precautions for your risk level, and nearby hospitals with contact details when risk is high."],
  ];
  return (
    <section id="how" className="scroll-mt-16 border-y bg-page py-[clamp(56px,7vw,104px)]">
      <div className="shell">
        <SectionHead eyebrow="How it works" title="From forecast to a personal plan in four steps."
          text="The forecast is free to view without an account. Sign in to save your profile and keep a history of your estimates." />
        <Reveal className="grid overflow-hidden rounded-[12px] border bg-card sm:grid-cols-2 xl:grid-cols-4">
          {steps.map(([t, d], i) => (
            <div key={t} className="border-b p-7 sm:[&:nth-child(odd)]:border-r xl:border-b-0 xl:border-r xl:last:border-r-0">
              <span className="num text-[13px] font-semibold text-brand-ink">{String(i + 1).padStart(2, "0")}</span>
              <h3 className="mt-3 mb-2 font-semibold">{t}</h3>
              <p className="text-sm text-muted-foreground">{d}</p>
            </div>
          ))}
        </Reveal>
      </div>
    </section>
  );
}

// ------------------------------------------------------------------ features

function Features() {
  const items = [
    { icon: LineIcon, t: "7 and 30-day forecasts", d: "Daily AQI with the official CPCB categories, plus PM2.5 and NO2." },
    { icon: HeartPulse, t: "Personal risk estimate", d: "Risk level and score for each day, with confidence and uncertain days shown as a range." },
    { icon: ListChecks, t: "Precautions", d: "Practical advice matched to your risk level: masks, activity, indoor air." },
    { icon: MapPin, t: "Nearby hospitals", d: "When risk is high, a map of nearby hospitals with phone numbers and addresses." },
    { icon: History, t: "History", d: "Every estimate is saved to your account so you can look back and compare." },
    { icon: Table2, t: "City comparison", d: "All six cities side by side, with trends and the model behind each forecast." },
  ];
  return (
    <section id="features" className="scroll-mt-16 py-[clamp(56px,7vw,104px)]">
      <div className="shell">
        <SectionHead eyebrow="Features" title="Everything you need to plan around air quality." />
        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
          {items.map(({ icon: Icon, t, d }, i) => (
            <Reveal key={t} delay={(i % 3) * 0.06} className="rounded-[12px] border bg-card p-6">
              <span className="mb-4 grid size-[38px] place-items-center rounded-[9px] bg-brand-soft text-brand-ink"><Icon className="size-[18px]" aria-hidden /></span>
              <h3 className="font-semibold">{t}</h3>
              <p className="mt-1.5 text-sm text-muted-foreground">{d}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

// ------------------------------------------------------------------ models

function Models({ gains, range, f1 }: { gains: ReturnType<typeof improvements>; range: string; f1: string }) {
  const maxGain = Math.max(...gains.map((g) => -g.pct), 1);
  const stats = [
    ["6", "models compared: ARIMA, SARIMA, Holt-Winters, LSTM, XGBoost, Prophet"],
    ["6", "test periods per city, across different seasons"],
    [range, "lower error than the best baseline forecast"],
    [f1, "F1 score of the health-risk model on unseen data"],
  ];
  return (
    <section id="models" className="scroll-mt-16 border-y bg-page py-[clamp(56px,7vw,104px)]">
      <div className="shell grid items-start gap-12 lg:grid-cols-[5fr_7fr]">
        <Reveal>
          <Eyebrow>Behind the forecasts</Eyebrow>
          <H2>Models chosen by evidence, not guesswork.</H2>
          <p className="mt-4 max-w-xl text-[clamp(16px,1.1vw,18px)] text-muted-foreground">
            For each city, six forecasting models are tested on six separate 30-day periods and must beat simple baseline forecasts. The best-performing model on average is the one we use.
          </p>
          <div className="mt-8 grid grid-cols-2 gap-px overflow-hidden rounded-[12px] border bg-border">
            {stats.map(([v, l]) => (
              <div key={l} className="bg-card p-5"><b className="num block text-[30px] font-medium">{v}</b><span className="text-[13.5px] text-muted-foreground">{l}</span></div>
            ))}
          </div>
          <Link href="/models" className="mt-6 inline-flex h-10 items-center rounded-[7px] border border-border-strong bg-card px-4 text-sm font-medium hover:bg-muted">See the full leaderboard</Link>
        </Reveal>
        <Reveal delay={0.08}>
          <div className="overflow-hidden rounded-[12px] border bg-card">
            <table className="w-full text-sm">
              <thead className="bg-page text-left text-[12.5px] text-faint [&_th]:px-4 [&_th]:py-3 [&_th]:font-medium">
                <tr><th>City</th><th>Model in use</th><th className="text-right">Error vs baseline</th></tr>
              </thead>
              <tbody>
                {gains.length === 0 && <tr><td colSpan={3} className="p-4"><Skeleton className="h-60" /></td></tr>}
                {gains.map((g) => (
                  <tr key={g.city} className="border-t [&>td]:px-4 [&>td]:py-3.5">
                    <td>{g.city}</td><td>{g.model}</td>
                    <td className="text-right">
                      <span className="num">{g.pct > 0 ? "+" : "−"}{Math.abs(Math.round(g.pct))}%</span>
                      <span className="ml-2.5 inline-block h-1.5 w-[120px] overflow-hidden rounded-full bg-muted align-middle">
                        <i className="block h-full bg-brand" style={{ width: `${Math.max(0, -g.pct) / maxGain * 100}%` }} />
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-2.5 text-[13px] text-faint">Mean error over six 30-day test periods (RMSE), compared with the best naive forecast.</p>
        </Reveal>
      </div>
    </section>
  );
}

// ------------------------------------------------------------------ data and methodology

function DataSection() {
  const ranges = ["0–50", "51–100", "101–200", "201–300", "301–400", "401–500"];
  const short = ["Minimal impact.", "Minor discomfort for sensitive people.", "Discomfort for people with lung or heart disease.",
    "Discomfort for most people on long exposure.", "Respiratory illness on prolonged exposure.", "Affects healthy people; serious for the sick."];
  const method = [
    ["Six major cities", "Delhi, Bengaluru, Chennai, Hyderabad, Lucknow and Ahmedabad, chosen for the completeness of their monitoring records."],
    ["Cleaned and checked", "Short gaps are filled, faulty sensor readings are corrected, and seasonality is tested before modelling."],
    ["Personal risk model", "A neural network estimates risk from your profile and the forecast AQI, PM2.5 and NO2 for each day."],
  ];
  return (
    <section id="data" className="scroll-mt-16 py-[clamp(56px,7vw,104px)]">
      <div className="shell">
        <SectionHead eyebrow="Data and methodology" title="Built on official monitoring data."
          text="Forecasts are trained on daily readings from Central Pollution Control Board (CPCB) monitoring stations, and AQI follows the official CPCB National Air Quality Index." />
        <Reveal className="grid overflow-hidden rounded-[12px] border bg-card sm:grid-cols-3 xl:grid-cols-6">
          {AQI_CATEGORIES.map((c, i) => (
            <div key={c.key} className="border-b p-5 sm:border-r xl:border-b-0 xl:last:border-r-0">
              <div className="mb-4 h-1.5 rounded-full" style={{ background: c.color }} />
              <b className="block font-semibold">{c.name}</b>
              <span className="num text-[13px] text-faint">{ranges[i]}</span>
              <p className="mt-2.5 text-[13.5px] text-muted-foreground">{short[i]}</p>
            </div>
          ))}
        </Reveal>
        <div className="mt-7 grid gap-5 md:grid-cols-3">
          {method.map(([t, d]) => (
            <Reveal key={t} className="border-t-2 pt-5"><h3 className="font-semibold">{t}</h3><p className="mt-1.5 text-sm text-muted-foreground">{d}</p></Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

// ------------------------------------------------------------------ privacy + FAQ

function PrivacyFaq({ range }: { range: string }) {
  const checks = [
    ["Only you can see your data", "Your profile and history are protected so no one else can read them."],
    ["No account needed to browse", "Forecasts and city comparisons are free and public."],
    ["Delete anytime", "Remove individual estimates from your history whenever you like."],
  ];
  const faqs = [
    ["What is AQI?", "The Air Quality Index turns pollutant levels into one number from 0 to 500. Airware uses India's official CPCB scale, from Good to Severe."],
    ["How accurate are the forecasts?", `Each city's model was tested on six separate 30-day periods and beats simple baseline forecasts by ${range} on average. Accuracy is highest for the next few days.`],
    ["Is the health risk a medical diagnosis?", "No. It's an estimate for planning and decision support. Always consult a healthcare professional for medical advice."],
    ["Do I need an account?", "No, forecasts are free to view. An account lets you save your profile once and keep a history of your estimates."],
    ["Is it free?", "Yes."],
  ];
  return (
    <section className="border-y bg-page py-[clamp(56px,7vw,104px)]">
      <div className="shell grid gap-12 lg:grid-cols-2">
        <Reveal>
          <Eyebrow>Privacy</Eyebrow>
          <H2>Your health profile stays yours.</H2>
          <ul className="mt-5">
            {checks.map(([t, d]) => (
              <li key={t} className="flex gap-3 border-b py-3.5 last:border-b-0">
                <Check className="mt-0.5 size-[18px] shrink-0 text-brand" aria-hidden />
                <div><b className="font-medium">{t}</b><span className="block text-sm text-muted-foreground">{d}</span></div>
              </li>
            ))}
          </ul>
        </Reveal>
        <Reveal delay={0.08}>
          <div id="faq" className="scroll-mt-20"><Eyebrow>FAQ</Eyebrow></div>
          <H2 className="mb-5">Common questions</H2>
          {faqs.map(([q, a], i) => (
            <details key={q} open={i === 0} className="group border-b py-4 first:border-t">
              <summary className="flex cursor-pointer list-none justify-between gap-4 font-medium [&::-webkit-details-marker]:hidden">
                {q}<span className="text-xl leading-none text-faint group-open:hidden">+</span><span className="hidden text-xl leading-none text-faint group-open:inline">–</span>
              </summary>
              <p className="mt-2.5 max-w-2xl text-muted-foreground">{a}</p>
            </details>
          ))}
        </Reveal>
      </div>
    </section>
  );
}

// ------------------------------------------------------------------ final CTA

function FinalCta() {
  return (
    <section className="py-[clamp(56px,7vw,104px)]">
      <div className="shell">
        <Reveal className="flex flex-wrap items-center justify-between gap-8 rounded-[14px] bg-brand px-11 py-10 text-on-brand">
          <div>
            <h2 className="text-[clamp(26px,2.2vw,36px)] font-semibold tracking-tight">See the air in your city this week.</h2>
            <p className="mt-2 opacity-80">Free forecasts for six cities. Add your profile for a personal estimate.</p>
          </div>
          <Link href="/dashboard" className="flex h-[46px] items-center gap-2 rounded-[7px] bg-card px-5 font-medium text-foreground hover:bg-muted">
            Open the dashboard<ArrowRight className="size-4" aria-hidden />
          </Link>
        </Reveal>
      </div>
    </section>
  );
}

