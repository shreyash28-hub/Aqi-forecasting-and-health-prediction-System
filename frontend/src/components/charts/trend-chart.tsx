"use client";

import { useMemo } from "react";
import type { EChartsCoreOption } from "echarts/core";
import { EChart } from "./echart";
import { AQI_CATEGORIES, aqiCategory } from "@/lib/aqi";
import { fmtDay, fmtDayMonth } from "@/lib/format";
import { useChartColors } from "@/components/theme/theme-provider";

export interface TrendPoint { date: string; value: number | null }

const BANDS = AQI_CATEGORIES.map((c, i) => ({ lo: i === 0 ? 0 : AQI_CATEGORIES[i - 1].max, hi: c.max, color: c.color }));

/**
 * Measured days (solid, neutral) running into the forecast (dashed), with today's readings
 * so far as a single marker. AQI: forecast coloured by CPCB category over faint category
 * bands. Pollutants: one colour, plus the national 24-hour standard as a reference line.
 */
export function TrendChart({ observed, forecast, today, metric, unit, color, standard, className }: {
  observed: TrendPoint[]; forecast: TrendPoint[]; today?: { date: string; value: number; hours: number } | null;
  metric: "aqi" | "pm25" | "no2"; unit: string; color?: string; standard?: number; className?: string;
}) {
  const c = useChartColors();
  const option = useMemo<EChartsCoreOption>(() => {
    const dates = [...new Set([...observed.map((p) => p.date), ...forecast.map((p) => p.date)])].sort();
    const at = (pts: TrendPoint[]) => {
      const m = new Map(pts.map((p) => [p.date, p.value]));
      return dates.map((d) => {
        const v = m.get(d);
        return v == null ? null : Math.round(v);
      });
    };
    const obs = at(observed), fc = at(forecast);
    const todayData = dates.map((d) => (today && d === today.date ? Math.round(today.value) : null));
    const values = [...obs, ...fc, ...todayData].filter((v): v is number => v != null);
    const isAqi = metric === "aqi";
    const span = Math.max(...values, standard ?? 0) - Math.min(...values);
    const pad = Math.max(span * 0.12, isAqi ? 15 : 5);
    const lo = Math.max(0, Math.floor((Math.min(...values) - pad) / 10) * 10);
    const hi = Math.ceil((Math.max(...values, standard ? standard * 1.08 : 0) + pad) / 10) * 10;
    const firstForecast = forecast[0]?.date;
    const lineColor = color ?? c.brand;

    const marks: object[] = [];
    if (firstForecast) {
      marks.push({ xAxis: fmtDayMonth(firstForecast), lineStyle: { color: c.axis, type: "solid", width: 1 },
        label: { formatter: "Today", position: "end", color: c.faint, fontSize: 11 } });
    }
    if (standard) {
      marks.push({ yAxis: standard, lineStyle: { color: c.faint, type: [4, 4], width: 1 },
        label: { formatter: `24-h standard ${standard}`, position: "insideStartTop", color: c.faint, fontSize: 11 } });
    }

    return {
      animationDuration: 700,
      grid: { left: 44, right: 18, top: 30, bottom: 28 },
      tooltip: {
        trigger: "axis",
        backgroundColor: c.surface,
        borderColor: c.axis,
        textStyle: { color: c.text, fontFamily: "var(--font-plex-sans), sans-serif", fontSize: 12 },
        formatter: (p: Array<{ dataIndex: number }>) => {
          const i = p[0].dataIndex;
          const rows: string[] = [];
          const fmt = (v: number) => `<b style="font-family:var(--font-plex-mono)">${v}</b>${isAqi ? ` · ${aqiCategory(v).name}` : ` ${unit}`}`;
          if (obs[i] != null) rows.push(`Measured ${fmt(obs[i]!)}`);
          if (todayData[i] != null) rows.push(`Today so far ${fmt(todayData[i]!)} <span style="opacity:.7">(${today!.hours} h)</span>`);
          if (fc[i] != null) rows.push(`Forecast ${fmt(fc[i]!)}`);
          if (!rows.length) rows.push("No complete reading");
          return `${fmtDay(dates[i])}<br/>${rows.join("<br/>")}`;
        },
      },
      xAxis: {
        type: "category",
        data: dates.map(fmtDayMonth),
        boundaryGap: false,
        axisLine: { lineStyle: { color: c.axis } },
        axisTick: { show: false },
        axisLabel: { color: c.faint, fontSize: 11, interval: Math.max(0, Math.ceil(dates.length / 9) - 1) },
      },
      yAxis: {
        type: "value", min: lo, max: hi,
        splitLine: { lineStyle: { color: c.grid } },
        axisLabel: { color: c.faint, fontFamily: "IBM Plex Mono, monospace", fontSize: 11 },
      },
      ...(isAqi ? {
        visualMap: {
          show: false, seriesIndex: 1, dimension: 1,
          pieces: AQI_CATEGORIES.map((cat, i) => ({ gt: i === 0 ? -1 : AQI_CATEGORIES[i - 1].max, lte: i === AQI_CATEGORIES.length - 1 ? 10000 : cat.max, color: cat.color })),
        },
      } : {}),
      series: [
        {
          name: "Measured", type: "line", data: obs, connectNulls: false, symbol: "circle", symbolSize: 3, showSymbol: false,
          lineStyle: { width: 2, color: c.muted }, itemStyle: { color: c.muted },
          markArea: isAqi ? {
            silent: true,
            data: BANDS.filter((b) => b.hi > lo && b.lo < hi).map((b) => [
              { yAxis: Math.max(b.lo, lo), itemStyle: { color: b.color, opacity: c.dark ? 0.07 : 0.06 } },
              { yAxis: Math.min(b.hi, hi) },
            ]),
          } : undefined,
        },
        {
          name: "Forecast", type: "line", data: fc, smooth: 0.3, symbol: "circle", symbolSize: 4, showSymbol: false,
          lineStyle: { width: 2.5, type: [6, 4], ...(isAqi ? {} : { color: lineColor }) },
          itemStyle: isAqi ? undefined : { color: lineColor },
          markLine: marks.length ? { silent: true, symbol: "none", data: marks } : undefined,
        },
        {
          name: "Today so far", type: "line", data: todayData, symbol: "diamond", symbolSize: 11,
          lineStyle: { width: 0 }, itemStyle: { color: c.text, borderColor: c.surface, borderWidth: 2 },
        },
      ],
    };
  }, [observed, forecast, today, metric, unit, color, standard, c]);

  return <EChart option={option} className={className} ariaLabel={`${metric.toUpperCase()} measured and forecast`} />;
}

/** Small key for the three series, in text colours (identity is carried by the line style). */
export function TrendLegend({ color }: { color?: string }) {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
      <span className="flex items-center gap-1.5"><i className="h-0.5 w-5 rounded bg-muted-foreground" />Measured</span>
      <span className="flex items-center gap-1.5">
        <i className="h-0 w-5 border-t-[2.5px] border-dashed" style={{ borderColor: color ?? "var(--brand)" }} />Forecast
      </span>
      <span className="flex items-center gap-1.5"><i className="size-2.5 rotate-45 bg-foreground" />Today so far</span>
    </div>
  );
}
