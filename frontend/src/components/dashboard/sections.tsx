"use client";

import Link from "next/link";
import { Activity, CalendarDays, Clock3, Home, LineChart as LineIcon, Phone, Shield, Wind, HeartPulse } from "lucide-react";
import { AqiScale, CategoryChip, Disclaimer, Panel, PanelTitle } from "@/components/common";
import { ForecastChart } from "@/components/charts/forecast-chart";
import { Sparkline } from "@/components/charts/sparkline";
import { Skeleton } from "@/components/ui/skeleton";
import { useChartColors } from "@/components/theme/theme-provider";
import { AQI_CATEGORIES, RISK_COLOR, aqiCategory, scoreToPoints } from "@/lib/aqi";
import { fmtDate, fmtDay, fmtDayMonth, fmtWeekday, round } from "@/lib/format";
import { DISCLAIMER, EXAMPLE_PROFILES, PRECAUTIONS, type Precaution } from "@/lib/content";
import type { ForecastDay, ForecastResponse, RiskResponse } from "@/lib/api";
import { cn } from "@/lib/utils";

// ------------------------------------------------------------------ page head

export function PageHead({ city, forecast, horizon, onHorizon }: {
  city: string; forecast?: ForecastResponse; horizon: number; onHorizon: (h: number) => void;
}) {
  return (
    <div className="flex flex-wrap items-end gap-6 pt-6 pb-4">
      <div>
        <h1 className="text-[26px] font-semibold tracking-tight">{city} air quality forecast</h1>
        <div className="mt-1 flex flex-wrap gap-4 text-sm text-muted-foreground">
          <span className="flex items-center gap-1.5"><CalendarDays className="size-4" aria-hidden />Issued {forecast ? fmtDate(forecast.origin_date) : "…"}</span>
          <span className="flex items-center gap-1.5"><LineIcon className="size-4" aria-hidden />Model: <b className="font-medium text-foreground">{forecast?.models.AQI?.model ?? "…"}</b></span>
          <span className="flex items-center gap-1.5"><Clock3 className="size-4" aria-hidden />CPCB monitoring stations</span>
        </div>
      </div>
      <div role="radiogroup" aria-label="Forecast horizon" className="ml-auto inline-flex overflow-hidden rounded-[7px] border border-border-strong bg-card">
        {[7, 30].map((h) => (
          <button
            key={h}
            role="radio"
            aria-checked={horizon === h}
            onClick={() => onHorizon(h)}
            className={cn("px-3.5 py-1.5 text-[13px] font-medium", horizon === h ? "bg-muted text-foreground" : "text-muted-foreground hover:text-foreground")}
          >
            {h} days
          </button>
        ))}
      </div>
    </div>
  );
}

// ------------------------------------------------------------------ city tabs

export function CityTabs({ byCity, city, onSelect }: { byCity?: Record<string, ForecastResponse>; city: string; onSelect: (c: string) => void }) {
  const cities = byCity ? Object.values(byCity) : [];
  return (
    <div className="flex gap-2 overflow-x-auto pb-5" role="tablist" aria-label="Cities">
      {cities.length === 0 && Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-10 w-32 rounded-[8px]" />)}
      {cities.map((f) => {
        const aqi = f.days[0].aqi, on = f.city === city;
        return (
          <button
            key={f.city}
            role="tab"
            aria-selected={on}
            onClick={() => onSelect(f.city)}
            className={cn("flex items-center gap-2.5 rounded-[8px] border bg-card px-3.5 py-2 whitespace-nowrap transition-colors hover:bg-muted",
              on && "border-brand shadow-[inset_0_0_0_1px_var(--brand)]")}
          >
            <span className="size-2 rounded-full" style={{ background: aqiCategory(aqi).color }} aria-hidden />
            <b className="font-medium">{f.city}</b>
            <span className="num text-muted-foreground">{Math.round(aqi)}</span>
          </button>
        );
      })}
    </div>
  );
}

// ------------------------------------------------------------------ tomorrow card

export function TomorrowCard({ days, horizon }: { days?: ForecastDay[]; horizon: number }) {
  if (!days) return <Panel className="col-span-12 lg:col-span-4 wide:col-span-3"><Skeleton className="h-72" /></Panel>;
  const t = days[0], cat = aqiCategory(t.aqi), win = days.slice(0, horizon);
  const values = win.map((d) => d.aqi);
  const peak = win[values.indexOf(Math.max(...values))];
  return (
    <Panel className="col-span-12 lg:col-span-4 wide:col-span-3">
      <div className="text-[13px] text-muted-foreground">Tomorrow · {fmtDay(t.date)}</div>
      <div className="mt-2.5 flex items-end gap-3">
        <span className="num text-[64px] leading-none font-medium tracking-tighter">{Math.round(t.aqi)}</span>
        <CategoryChip aqi={t.aqi} className="mb-1.5" />
      </div>
      <AqiScale aqi={t.aqi} />
      <p className="mt-4 text-[13px] leading-relaxed text-muted-foreground">{cat.advice}</p>
      <dl className="mt-4 grid grid-cols-[1fr_auto] gap-x-3 gap-y-2 border-t pt-4 text-sm">
        <dt className="text-muted-foreground">Range, next {horizon} days</dt>
        <dd className="num text-right font-medium">{Math.round(Math.min(...values))}–{Math.round(Math.max(...values))}</dd>
        <dt className="text-muted-foreground">Peak day</dt>
        <dd className="text-right font-medium">{fmtDay(peak.date)}</dd>
        <dt className="text-muted-foreground">PM2.5 tomorrow</dt>
        <dd className="num text-right font-medium">{round(t.pm25)} µg/m³</dd>
      </dl>
    </Panel>
  );
}

// ------------------------------------------------------------------ forecast chart card

export function ForecastCard({ days, horizon }: { days?: ForecastDay[]; horizon: number }) {
  return (
    <Panel delay={0.05} className="col-span-12 flex flex-col lg:col-span-8 wide:col-span-9">
      <PanelTitle
        sub={`next ${horizon} days`}
        action={
          <div className="flex flex-wrap gap-3.5 text-xs text-muted-foreground">
            {AQI_CATEGORIES.map((c) => (
              <span key={c.key} className="flex items-center gap-1.5"><i className="size-2.5 rounded-[2px]" style={{ background: c.color }} />{c.name}</span>
            ))}
          </div>
        }
      >
        AQI forecast
      </PanelTitle>
      {days ? <ForecastChart days={days.slice(0, horizon)} className="mt-2 min-h-[300px] flex-1" /> : <Skeleton className="mt-3 min-h-[300px] flex-1" />}
    </Panel>
  );
}

// ------------------------------------------------------------------ pollutants

export function PollutantsCard({ days, horizon }: { days?: ForecastDay[]; horizon: number }) {
  const c = useChartColors();
  const rows = [
    { key: "pm25" as const, label: "PM2.5 · fine particles", color: c.brand },
    { key: "no2" as const, label: "NO2 · nitrogen dioxide", color: c.faint },
  ];
  return (
    <Panel delay={0.15} className="col-span-12 flex flex-col lg:col-span-6 wide:col-span-4">
      <PanelTitle sub="daily average, forecast">Pollutants</PanelTitle>
      {!days ? <Skeleton className="mt-4 h-40" /> : <div className="flex flex-1 flex-col justify-evenly">{rows.map((r) => {
        const vals = days.slice(0, horizon).map((d) => d[r.key] ?? 0);
        return (
          <div key={r.key} className="grid grid-cols-[1fr_auto] items-end border-b py-3.5 last:border-b-0">
            <div>
              <div className="text-[13px] text-muted-foreground">{r.label}</div>
              <div><span className="num text-[26px] font-medium">{round(days[0][r.key])}</span><span className="ml-1 text-xs text-faint">µg/m³ tomorrow</span></div>
            </div>
            <Sparkline values={vals} color={r.color} className="h-11 w-40" />
          </div>
        );
      })}</div>}
    </Panel>
  );
}

// ------------------------------------------------------------------ risk

export function RiskCard({ risk, loading }: { risk?: RiskResponse; loading: boolean }) {
  const ex = EXAMPLE_PROFILES.ramesh;
  return (
    <Panel delay={0.1} className="col-span-12 wide:col-span-5">
      <PanelTitle
        sub="next 7 days · example profile"
        action={<Link href="/risk" className="flex h-8 items-center rounded-[7px] bg-brand px-3 text-[13px] font-medium text-on-brand hover:brightness-110">Check my risk</Link>}
      >
        Your health risk
      </PanelTitle>
      <div className="mt-3.5 flex flex-wrap gap-1.5">
        {ex.tags.map((t) => <span key={t} className="rounded-[5px] bg-muted px-2 py-0.5 text-xs text-muted-foreground">{t}</span>)}
      </div>
      <div className={cn("mt-4 grid grid-cols-7 gap-2", loading && "opacity-60")}>
        {!risk && Array.from({ length: 7 }).map((_, i) => <Skeleton key={i} className="h-[104px]" />)}
        {risk?.days.slice(0, 7).map((d) => (
          <div key={d.date} className="rounded-[8px] border p-2.5" title={d.borderline ? "Borderline day: the estimate sits between two levels" : undefined}>
            <div className="text-xs text-muted-foreground">{fmtWeekday(d.date)}</div>
            <div className="text-[11.5px] text-faint">{fmtDayMonth(d.date)}</div>
            <div className="mt-2.5 text-[13px] leading-tight font-semibold">{d.risk_range.replace("-", "–​")}{d.borderline && <span className="text-faint">*</span>}</div>
            <div className="mt-2 h-1 overflow-hidden rounded-full bg-muted">
              <i className="block h-full" style={{ width: `${Math.round(d.confidence * 100)}%`, background: RISK_COLOR[d.risk_level] }} />
            </div>
            <div className="mt-1.5 text-[11.5px] text-faint"><span className="num">{Math.round(d.confidence * 100)}%</span> conf · <span className="num">{scoreToPoints(d.risk_score)}</span></div>
          </div>
        ))}
      </div>
      <Disclaimer className="mt-4">{DISCLAIMER}</Disclaimer>
    </Panel>
  );
}

// ------------------------------------------------------------------ precautions

export const PRECAUTION_ICON: Record<Precaution["icon"], React.ComponentType<{ className?: string }>> = {
  activity: Activity, mask: Shield, window: Wind, pulse: HeartPulse, home: Home, phone: Phone,
};

export function PrecautionsCard({ risk }: { risk?: RiskResponse }) {
  const level = risk?.summary.highest_alert_level;
  return (
    <Panel delay={0.2} className="col-span-12 lg:col-span-6 wide:col-span-3">
      <PanelTitle sub={level ? `for ${level.toLowerCase()} risk` : undefined}>Precautions</PanelTitle>
      {!level ? <Skeleton className="mt-4 h-48" /> : (
        <ul className="mt-1.5">
          {PRECAUTIONS[level].map((p) => {
            const Icon = PRECAUTION_ICON[p.icon];
            return (
              <li key={p.title} className="flex gap-3 border-b py-3 last:border-b-0">
                <span className="grid size-[30px] shrink-0 place-items-center rounded-[7px] bg-brand-soft text-brand-ink"><Icon className="size-4" aria-hidden /></span>
                <div className="leading-snug"><b className="block text-sm font-medium">{p.title}</b><span className="text-[13px] text-muted-foreground">{p.detail}</span></div>
              </li>
            );
          })}
        </ul>
      )}
    </Panel>
  );
}

// ------------------------------------------------------------------ all cities

export function CitiesTable({ byCity, onSelect }: { byCity?: Record<string, ForecastResponse>; onSelect: (c: string) => void }) {
  return (
    <Panel delay={0.25} className="col-span-12">
      <PanelTitle sub="tomorrow and next 7 days">All cities</PanelTitle>
      {!byCity ? <Skeleton className="mt-4 h-72" /> : (
        <div className="mt-3 overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="text-left text-xs text-faint [&>th]:border-b [&>th]:px-3 [&>th]:py-2 [&>th]:font-medium">
                <th>City</th><th className="text-right">AQI tomorrow</th><th>Category</th><th>7-day trend</th>
                <th className="text-right">7-day range</th><th className="text-right">PM2.5</th><th className="text-right">NO2</th><th>Forecast model</th>
              </tr>
            </thead>
            <tbody>
              {Object.values(byCity).map((f) => {
                const week = f.days.slice(0, 7), a = week.map((d) => d.aqi), t = f.days[0];
                return (
                  <tr key={f.city} onClick={() => onSelect(f.city)} className="cursor-pointer hover:bg-muted [&>td]:border-b [&>td]:px-3 [&>td]:py-2.5 last:[&>td]:border-b-0">
                    <td className="font-medium">{f.city}</td>
                    <td className="num text-right text-[15px]">{Math.round(t.aqi)}</td>
                    <td><CategoryChip aqi={t.aqi} /></td>
                    <td><Sparkline values={a} color={aqiCategory(t.aqi).color} className="h-7 w-44" /></td>
                    <td className="num text-right">{Math.round(Math.min(...a))}–{Math.round(Math.max(...a))}</td>
                    <td className="num text-right">{round(t.pm25)}</td>
                    <td className="num text-right">{round(t.no2)}</td>
                    <td className="text-muted-foreground">{f.models.AQI?.model}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  );
}

