"use client";

import { useCallback } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { CalendarDays, Check, Clock3, Minus } from "lucide-react";
import { AppHeader } from "@/components/layout/app-header";
import { AppFooter } from "@/components/layout/footer";
import { CategoryChip, ErrorState, Panel, PanelTitle } from "@/components/common";
import { CityTabs } from "@/components/dashboard/sections";
import { useCityForecasts } from "@/components/dashboard/use-dashboard-data";
import { TrendChart, TrendLegend, type TrendPoint } from "@/components/charts/trend-chart";
import { Skeleton } from "@/components/ui/skeleton";
import { useChartColors } from "@/components/theme/theme-provider";
import { useAsync } from "@/hooks/use-async";
import { api, type ForecastDay, type ForecastLeaderboard, type ForecastResponse, type ObservedResponse } from "@/lib/api";
import { aqiCategory } from "@/lib/aqi";
import { CITIES } from "@/lib/content";
import { fmtDate, fmtDay, fmtDayMonth, relDay, round, timeOf } from "@/lib/format";

const PAST_DAYS = 30;
const TARGETS = [
  { key: "AQI", label: "AQI", unit: "" },
  { key: "PM2.5", label: "PM2.5", unit: "µg/m³" },
  { key: "NO2", label: "NO2", unit: "µg/m³" },
] as const;
type Boards = Record<(typeof TARGETS)[number]["key"], ForecastLeaderboard>;

/** City forecast in detail: the last 30 measured days running into the next 30 forecast days. */
export function ForecastView() {
  const params = useSearchParams();
  const router = useRouter();
  const path = usePathname();
  const city = CITIES.find((c) => c.toLowerCase() === (params.get("city") ?? "").toLowerCase()) ?? "Delhi";
  const setCity = useCallback((c: string) => {
    const sp = new URLSearchParams(params.toString());
    sp.set("city", c);
    router.replace(`${path}?${sp.toString()}`, { scroll: false });
  }, [params, path, router]);

  const forecasts = useCityForecasts();
  const observed = useAsync((signal) => api.observed(city, PAST_DAYS, signal), [city]);
  const boards = useAsync<Boards>(async (signal) => {
    const [aqi, pm25, no2] = await Promise.all(TARGETS.map((t) => api.forecastLeaderboard(t.key, signal)));
    return { AQI: aqi, "PM2.5": pm25, NO2: no2 };
  }, []);
  const fc = forecasts.data?.byCity[city];

  return (
    <div className="min-h-screen bg-page">
      <AppHeader city={city} onCityChange={setCity} />
      <main className="shell">
        <div className="pt-6 pb-4">
          <h1 className="text-[26px] font-semibold tracking-tight">{city}: the next 30 days</h1>
          <div className="mt-1 flex flex-wrap gap-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1.5"><CalendarDays className="size-4" aria-hidden />Issued {fc ? fmtDate(fc.origin_date) : "…"}</span>
            <span className="flex items-center gap-1.5"><Clock3 className="size-4" aria-hidden />
              {fc?.readings_as_of ? `Today updated with readings to ${timeOf(fc.readings_as_of)}` : "CPCB monitoring stations"}
            </span>
          </div>
        </div>
        {forecasts.error ? <ErrorState message={forecasts.error.message} onRetry={forecasts.retry} /> : (
          <>
            <CityTabs byCity={forecasts.data?.byCity} city={city} onSelect={setCity} />
            <div className="grid grid-cols-12 gap-4">
              <WeeksPanel days={fc?.days} />
              <ReliabilityPanel city={city} forecast={fc} boards={boards.data} error={boards.error?.message} />
              <TrendPanel metric="aqi" title="AQI" sub="last 30 days measured, next 30 forecast" fc={fc} obs={observed.data}
                obsError={observed.error?.message} className="col-span-12" height="h-[340px]" />
              <TrendPanel metric="pm25" title="PM2.5" sub="fine particles, µg/m³" fc={fc} obs={observed.data} standard={60}
                className="col-span-12 lg:col-span-6" />
              <TrendPanel metric="no2" title="NO2" sub="nitrogen dioxide, µg/m³" fc={fc} obs={observed.data} standard={80}
                className="col-span-12 lg:col-span-6" />
              <DayTable days={fc?.days} />
            </div>
          </>
        )}
      </main>
      <AppFooter />
    </div>
  );
}

// ------------------------------------------------------------------ week by week

function WeeksPanel({ days }: { days?: ForecastDay[] }) {
  const weeks = days ? [days.slice(0, 7), days.slice(7, 14), days.slice(14, 21), days.slice(21)].filter((w) => w.length) : [];
  const names = ["This week", "Next week", "Week 3", "Week 4"];
  return (
    <Panel className="col-span-12 lg:col-span-8">
      <PanelTitle sub="average AQI, worst day and Poor-or-worse days">Week by week</PanelTitle>
      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
        {!days && Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-[112px]" />)}
        {weeks.map((w, i) => {
          const avg = w.reduce((s, d) => s + d.aqi, 0) / w.length;
          const worst = w.reduce((a, b) => (b.aqi > a.aqi ? b : a));
          const poor = w.filter((d) => Math.round(d.aqi) > 200).length;
          return (
            <div key={i} className="rounded-[8px] border p-3.5">
              <div className="flex items-baseline justify-between gap-2 text-[13px]">
                <span className="font-medium">{names[i]}</span>
                <span className="text-faint">{fmtDayMonth(w[0].date)} – {fmtDayMonth(w[w.length - 1].date)}</span>
              </div>
              <div className="mt-2 flex items-center gap-2.5">
                <span className="num text-[30px] leading-none font-medium tracking-tight">{Math.round(avg)}</span>
                <CategoryChip aqi={avg} />
              </div>
              <div className="mt-2.5 flex flex-wrap justify-between gap-x-3 text-[12.5px] text-muted-foreground">
                <span>Worst <b className="font-medium text-foreground">{fmtDay(worst.date)}</b> · <span className="num">{Math.round(worst.aqi)}</span></span>
                <span><span className="num font-medium text-foreground">{poor}</span> of {w.length} days Poor or worse</span>
              </div>
            </div>
          );
        })}
      </div>
    </Panel>
  );
}

// ------------------------------------------------------------------ reliability

function ReliabilityPanel({ city, forecast, boards, error }: { city: string; forecast?: ForecastResponse; boards?: Boards; error?: string }) {
  return (
    <Panel delay={0.05} className="col-span-12 flex flex-col lg:col-span-4">
      <PanelTitle sub="tested on past 30-day periods">How reliable is this?</PanelTitle>
      {error ? <p className="mt-4 text-sm text-muted-foreground">Model results could not be loaded.</p> : (
        <dl className="mt-3 flex-1 divide-y">
          {TARGETS.map((t) => {
            const b = boards?.[t.key]?.cities[city];
            const row = b?.ranking.find((r) => r.model === b.deployed_model);
            const base = b?.ranking.find((r) => r.model === b.best_baseline);
            const beats = row && base && row.kind === "model" && row.mean_rmse < base.mean_rmse;
            return (
              <div key={t.key} className="grid grid-cols-[1fr_auto] gap-x-3 py-2.5">
                <dt className="text-sm font-medium">{t.label} <span className="font-normal text-muted-foreground">· {forecast?.models[t.key]?.model ?? "…"}</span></dt>
                <dd className="num text-right text-sm">{row ? `±${Math.round(row.mean_rmse)}${t.unit ? ` ${t.unit}` : ""}` : <Skeleton className="h-4 w-14" />}</dd>
                <dd className="col-span-2 mt-0.5 flex items-center gap-1.5 text-[12.5px] text-muted-foreground">
                  {!row ? <Skeleton className="h-3.5 w-40" /> : beats ? (
                    <><Check className="size-3.5 text-[#2e9e5b]" aria-hidden />{Math.round(100 * (1 - row.mean_rmse / base!.mean_rmse))}% smaller error than a naive guess</>
                  ) : (
                    <><Minus className="size-3.5" aria-hidden />Uses the naive guess: no model beat it here</>
                  )}
                </dd>
              </div>
            );
          })}
        </dl>
      )}
      <p className="mt-3 border-t pt-3 text-[12.5px] leading-relaxed text-faint">
        ± is the typical error (RMSE) over {boards?.AQI.n_windows ?? 5} past 30-day test periods. Days further ahead are less certain;
        today and the next two days also use today&apos;s station readings. <Link href="/models" className="text-brand-ink hover:underline">All models</Link>
      </p>
    </Panel>
  );
}

// ------------------------------------------------------------------ trend charts

function TrendPanel({ metric, title, sub, fc, obs, obsError, standard, className, height = "h-[260px]" }: {
  metric: "aqi" | "pm25" | "no2"; title: string; sub: string; fc?: ForecastResponse; obs?: ObservedResponse;
  obsError?: string; standard?: number; className?: string; height?: string;
}) {
  const c = useChartColors();
  const color = metric === "no2" ? c.muted : undefined;
  const forecast: TrendPoint[] = fc?.days.map((d) => ({ date: d.date, value: metric === "aqi" ? d.aqi : d[metric] ?? null })) ?? [];
  const observed: TrendPoint[] = obs?.days.map((d) => ({ date: d.date, value: d[metric] })) ?? [];
  const t = obs?.today_so_far;
  const today = t && t[metric] != null ? { date: t.date, value: t[metric]!, hours: t.hours } : null;
  const ready = fc && (obs || obsError);
  return (
    <Panel delay={0.1} className={className}>
      <PanelTitle sub={sub} action={<TrendLegend color={metric === "aqi" ? aqiCategory(fc?.days[0].aqi ?? 0).color : color} />}>{title}</PanelTitle>
      {!ready ? <Skeleton className={`mt-3 ${height}`} /> : (
        <TrendChart observed={observed} forecast={forecast} today={today} metric={metric}
          unit={metric === "aqi" ? "" : "µg/m³"} color={color} standard={standard} className={`mt-2 ${height}`} />
      )}
      {standard && <p className="mt-1 text-[12px] text-faint">Dashed grey line: India&apos;s 24-hour air quality standard ({standard} µg/m³).</p>}
    </Panel>
  );
}

// ------------------------------------------------------------------ day by day

function DayTable({ days }: { days?: ForecastDay[] }) {
  const half = days ? Math.ceil(days.length / 2) : 15;
  const parts = days ? [days.slice(0, half), days.slice(half)] : [];
  return (
    <Panel delay={0.15} className="col-span-12">
      <PanelTitle sub="daily averages, forecast">Day by day</PanelTitle>
      {!days ? <Skeleton className="mt-4 h-[520px]" /> : (
        <div className="mt-3 grid gap-x-8 lg:grid-cols-2">
          {parts.map((rows, i) => (
            <table key={i} className="w-full text-sm">
              <thead className={i === 1 ? "max-lg:hidden" : undefined}>
                <tr className="border-b text-left text-[12px] text-faint">
                  <th className="py-2 font-medium">Day</th>
                  <th className="py-2 text-right font-medium">AQI</th>
                  <th className="py-2 pl-3 font-medium">Category</th>
                  <th className="py-2 text-right font-medium">PM2.5</th>
                  <th className="py-2 text-right font-medium">NO2</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((d) => (
                  <tr key={d.date} className="border-b last:border-b-0">
                    <td className="py-[7px]">{relDay(d.date) === fmtDay(d.date) ? fmtDay(d.date) : <>{relDay(d.date)} <span className="text-faint">· {fmtDayMonth(d.date)}</span></>}</td>
                    <td className="num py-[7px] text-right font-medium">{Math.round(d.aqi)}</td>
                    <td className="py-[7px] pl-3"><CategoryChip aqi={d.aqi} className="h-[22px] text-[12px]" /></td>
                    <td className="num py-[7px] text-right text-muted-foreground">{round(d.pm25)}</td>
                    <td className="num py-[7px] text-right text-muted-foreground">{round(d.no2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ))}
        </div>
      )}
      <p className="mt-3 text-[12px] text-faint">AQI on India&apos;s CPCB scale; PM2.5 and NO2 in µg/m³.</p>
    </Panel>
  );
}
