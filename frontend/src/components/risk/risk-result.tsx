"use client";

import Link from "next/link";
import { Hospital, UserRound } from "lucide-react";
import { ColorChip, Disclaimer, Panel, PanelTitle } from "@/components/common";
import { ForecastChart } from "@/components/charts/forecast-chart";
import { RiskScoreChart } from "@/components/charts/risk-score-chart";
import { PRECAUTION_ICON } from "@/components/dashboard/sections";
import { AQI_CATEGORIES, RISK_COLOR, RISK_LEVELS, aqiCategory, scoreToPoints } from "@/lib/aqi";
import { fmtDay, fmtDayMonth, fmtWeekday } from "@/lib/format";
import { DISCLAIMER, PRECAUTIONS } from "@/lib/content";
import type { HistoryDetail, RiskDay, RiskLevel, SavedRiskResponse } from "@/lib/api";
import { cn } from "@/lib/utils";

/** What the result view needs; built from a fresh run or a saved history run. */
export interface RiskResultData {
  city: string;
  horizon: number;
  origin_date: string;
  predicted_at: string;
  summary: SavedRiskResponse["summary"];
  days: RiskDay[];
  healthModels: Record<string, string>;
  forecastModels?: Record<string, string>;
  imputedFields?: string[];
}

export const fromRun = (r: SavedRiskResponse): RiskResultData => ({
  city: r.city, horizon: r.horizon, origin_date: r.origin_date, predicted_at: r.predicted_at, summary: r.summary,
  days: r.days, healthModels: { feature_set: r.feature_set, ...r.health_models }, imputedFields: r.imputed_fields,
});

export const fromHistory = (h: HistoryDetail): RiskResultData => ({
  city: h.city, horizon: h.horizon, origin_date: h.origin_date, predicted_at: h.predicted_at, summary: h.summary,
  days: h.days, healthModels: h.models.health, forecastModels: h.models.forecast,
});

const FIELD_LABEL: Record<string, string> = { bmi: "BMI", exercise_hours: "exercise hours", family_history: "family history" };
const FEATURE_SET: Record<string, string> = { aqi_pm25_no2: "AQI, PM2.5 and NO2", aqi_only: "AQI only" };

export function LevelChip({ level, children, className }: { level: RiskLevel; children?: React.ReactNode; className?: string }) {
  return <ColorChip color={RISK_COLOR[level]} className={className}>{children ?? level}</ColorChip>;
}

/** Stacked bar of how many days fall in each level, with a labelled legend. */
export function LevelMix({ counts, total, className }: { counts: Record<RiskLevel, number>; total: number; className?: string }) {
  return (
    <div className={className}>
      <div className="flex h-2.5 gap-[2px] overflow-hidden rounded-full" role="img"
        aria-label={RISK_LEVELS.map((l) => `${counts[l]} ${l}`).join(", ")}>
        {RISK_LEVELS.filter((l) => counts[l] > 0).map((l) => (
          <i key={l} style={{ width: `${(counts[l] / total) * 100}%`, background: RISK_COLOR[l] }} />
        ))}
      </div>
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[12.5px] text-muted-foreground">
        {RISK_LEVELS.map((l) => (
          <span key={l} className={cn("flex items-center gap-1.5", counts[l] === 0 && "text-faint")}>
            <i className="size-2.5 rounded-[2px]" style={{ background: RISK_COLOR[l], opacity: counts[l] ? 1 : 0.35 }} />
            {l} <b className="num font-medium text-foreground">{counts[l]}</b>
          </span>
        ))}
      </div>
    </div>
  );
}

export function RiskResult({ data, busy = false }: { data: RiskResultData; busy?: boolean }) {
  const { summary, days } = data;
  const level = summary.highest_alert_level;
  const firstAlert = days.find((d) => d.alert_level === level);
  const scores = days.map((d) => scoreToPoints(d.risk_score));

  return (
    <div className={cn("grid grid-cols-12 gap-4 transition-opacity", busy && "pointer-events-none opacity-60")} aria-busy={busy}>
      {summary.show_hospitals && (
        <div className="col-span-12 flex items-start gap-3 rounded-[10px] border p-4" style={{ borderColor: RISK_COLOR[level], background: `color-mix(in srgb, ${RISK_COLOR[level]} 8%, var(--card))` }}>
          <Hospital className="mt-0.5 size-5 shrink-0" style={{ color: RISK_COLOR[level] }} aria-hidden />
          <div className="text-sm">
            <b className="font-semibold">Your estimated risk reaches {level} {firstAlert ? `on ${fmtDay(firstAlert.date)}` : ""}.</b>{" "}
            <span className="text-muted-foreground">Follow the precautions below and keep the phone number of your nearest hospital handy. A map of nearby hospitals with contact details is coming soon.</span>
          </div>
        </div>
      )}

      {/* summary */}
      <Panel className="col-span-12 flex flex-col lg:col-span-4 wide:col-span-3">
        <div className="text-[13px] text-muted-foreground">Highest risk, next {data.horizon} days</div>
        <div className="mt-2.5 flex items-center gap-3">
          <span className="text-[34px] leading-none font-semibold tracking-tight" style={{ color: `color-mix(in srgb, ${RISK_COLOR[level]} 75%, var(--foreground))` }}>{level}</span>
        </div>
        {firstAlert && (
          <p className="mt-2 text-[13px] text-muted-foreground">
            {summary.days_by_level[level] > 0
              ? `First reached on ${fmtDay(firstAlert.date)}`
              : `Upper end of a borderline range, first on ${fmtDay(firstAlert.date)}`}
          </p>
        )}
        <LevelMix counts={summary.days_by_level} total={days.length} className="mt-5" />
        <dl className="mt-5 grid grid-cols-[1fr_auto] gap-x-3 gap-y-2 border-t pt-4 text-sm">
          <dt className="text-muted-foreground">Risk score range (of 100)</dt>
          <dd className="num text-right font-medium">{Math.min(...scores)}–{Math.max(...scores)} <span className="text-faint">/ 100</span></dd>
          <dt className="text-muted-foreground">Borderline days</dt>
          <dd className="num text-right font-medium">{summary.borderline_days}</dd>
          <dt className="text-muted-foreground">City</dt>
          <dd className="text-right font-medium">{data.city}</dd>
        </dl>
      </Panel>

      {/* day by day */}
      <Panel delay={0.05} className="col-span-12 flex flex-col lg:col-span-8 wide:col-span-9">
        <PanelTitle sub={`${fmtDayMonth(days[0].date)} – ${fmtDayMonth(days[days.length - 1].date)}`}>Day by day</PanelTitle>
        <div className={cn("mt-4 grid gap-2", days.length <= 7 ? "flex-1 grid-cols-7" : "grid-cols-6 wide:grid-cols-10")}>
          {days.map((d) => <DayCard key={d.date} day={d} compact={days.length > 7} />)}
        </div>
        {summary.borderline_days > 0 && (
          <p className="mt-3 text-[12.5px] text-faint">* Borderline day: the estimate sits between two levels, so a range is shown. Precautions follow the higher level.</p>
        )}
      </Panel>

      {/* charts */}
      <Panel delay={0.1} className="col-span-12 flex flex-col lg:col-span-6">
        <PanelTitle sub="daily score, with level bands">Risk score</PanelTitle>
        <RiskScoreChart days={days} className="mt-2 h-[280px]" />
      </Panel>
      <Panel delay={0.12} className="col-span-12 flex flex-col lg:col-span-6">
        <PanelTitle
          sub={`${data.city}, forecast`}
          action={<div className="hidden flex-wrap gap-3 text-xs text-muted-foreground wide:flex">
            {AQI_CATEGORIES.map((c) => <span key={c.key} className="flex items-center gap-1.5"><i className="size-2.5 rounded-[2px]" style={{ background: c.color }} />{c.name}</span>)}
          </div>}
        >
          Air quality
        </PanelTitle>
        <ForecastChart days={days} className="mt-2 h-[280px]" />
      </Panel>

      {/* precautions + about */}
      <Panel delay={0.15} className="col-span-12 lg:col-span-6">
        <PanelTitle sub={`for ${level.toLowerCase()} risk`}>Precautions</PanelTitle>
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
      </Panel>
      <Panel delay={0.18} className="col-span-12 flex flex-col lg:col-span-6">
        <PanelTitle>About this estimate</PanelTitle>
        <dl className="mt-3 grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-sm">
          <dt className="text-muted-foreground">Risk level model</dt><dd className="font-medium">{data.healthModels.classification ?? "–"}</dd>
          <dt className="text-muted-foreground">Risk score model</dt><dd className="font-medium">{data.healthModels.regression ?? "–"}</dd>
          <dt className="text-muted-foreground">Air inputs</dt><dd className="font-medium">{FEATURE_SET[data.healthModels.feature_set] ?? data.healthModels.feature_set ?? "–"}</dd>
          {data.forecastModels && <>
            <dt className="text-muted-foreground">Forecast models</dt>
            <dd className="font-medium">{Object.entries(data.forecastModels).map(([t, m]) => `${t}: ${m}`).join(" · ")}</dd>
          </>}
          <dt className="text-muted-foreground">Calculated</dt>
          <dd className="font-medium">{new Date(data.predicted_at).toLocaleString("en-GB", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" })}</dd>
        </dl>
        {data.imputedFields && data.imputedFields.length > 0 && (
          <p className="mt-4 flex gap-2 rounded-[8px] bg-muted p-3 text-[13px] text-muted-foreground">
            <UserRound className="mt-px size-4 shrink-0" aria-hidden />
            <span>Typical values were used for {data.imputedFields.map((f) => FIELD_LABEL[f] ?? f).join(", ")}.{" "}
              <Link href="/profile" className="font-medium text-brand-ink hover:underline">Complete your profile</Link> for a more personal estimate.</span>
          </p>
        )}
        <Disclaimer className="mt-auto pt-4">{DISCLAIMER}</Disclaimer>
      </Panel>
    </div>
  );
}

function DayCard({ day: d, compact }: { day: RiskDay; compact: boolean }) {
  const pct = Math.round(d.confidence * 100);
  const cat = aqiCategory(d.aqi);
  return (
    <div className={cn("flex flex-col rounded-[8px] border", compact ? "p-2" : "p-3")}
      title={`${fmtDay(d.date)} · AQI ${Math.round(d.aqi)} (${cat.name}) · score ${scoreToPoints(d.risk_score)}/100${d.borderline ? " · borderline" : ""}`}>
      <div className="flex items-baseline justify-between gap-1">
        <span className="text-xs text-muted-foreground">{fmtWeekday(d.date)}</span>
        <span className="text-[11.5px] text-faint">{fmtDayMonth(d.date)}</span>
      </div>
      <div className={cn("leading-tight font-semibold", compact ? "mt-1.5 text-[12.5px]" : "mt-3 text-[15px]")}>
        {d.risk_range.replace("-", "–​")}{d.borderline && <span className="text-faint">*</span>}
      </div>
      <div className="mt-2 h-1 overflow-hidden rounded-full bg-muted">
        <i className="block h-full" style={{ width: `${pct}%`, background: RISK_COLOR[d.alert_level] }} />
      </div>
      {compact ? (
        <div className="mt-1.5 text-[11px] text-faint"><span className="num">{pct}%</span> · AQI <span className="num">{Math.round(d.aqi)}</span></div>
      ) : (
        <>
          <div className="mt-1.5 text-[11.5px] text-faint"><span className="num">{pct}%</span> confidence</div>
          <div className="mt-auto flex items-end justify-between gap-1 border-t pt-2.5">
            <div>
              <div className="text-[11px] text-faint">AQI</div>
              <div className="flex items-center gap-1.5"><i className="size-2 rounded-full" style={{ background: cat.color }} aria-hidden /><span className="num text-[13px] font-medium">{Math.round(d.aqi)}</span></div>
            </div>
            <div className="text-right">
              <div className="text-[11px] text-faint">Score</div>
              <div className="num text-[13px] font-medium">{scoreToPoints(d.risk_score)}<span className="text-faint">/100</span></div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
