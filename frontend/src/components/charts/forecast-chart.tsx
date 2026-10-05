"use client";

import { useMemo } from "react";
import type { EChartsCoreOption } from "echarts/core";
import { EChart } from "./echart";
import { AQI_CATEGORIES, aqiCategory } from "@/lib/aqi";
import { fmtDay, fmtWeekday } from "@/lib/format";
import { useChartColors } from "@/components/theme/theme-provider";
import type { ForecastDay } from "@/lib/api";

const BANDS = AQI_CATEGORIES.map((c, i) => ({ lo: i === 0 ? 0 : AQI_CATEGORIES[i - 1].max, hi: c.max, color: c.color }));

/** Daily AQI line coloured by CPCB category, with faint category bands behind it. */
export function ForecastChart({ days, compact = false, className }: { days: ForecastDay[]; compact?: boolean; className?: string }) {
  const c = useChartColors();
  const option = useMemo<EChartsCoreOption>(() => {
    const values = days.map((d) => Math.round(d.aqi));
    const few = days.length <= 10;
    const lo = Math.max(0, Math.floor((Math.min(...values) - 25) / 10) * 10);
    const hi = Math.ceil((Math.max(...values) + 25) / 10) * 10;
    return {
      animationDuration: 800,
      animationEasing: "cubicOut",
      grid: { left: 42, right: 18, top: few ? 26 : 16, bottom: 28 },
      tooltip: {
        trigger: "axis",
        backgroundColor: c.surface,
        borderColor: c.axis,
        textStyle: { color: c.text, fontFamily: "var(--font-plex-sans), sans-serif", fontSize: 12 },
        formatter: (p: Array<{ dataIndex: number; value: number }>) => {
          const d = days[p[0].dataIndex];
          const cat = aqiCategory(d.aqi);
          return `${fmtDay(d.date)}<br/><b style="font-family:var(--font-plex-mono)">AQI ${Math.round(d.aqi)}</b> · ${cat.name}` +
            (d.pm25 != null ? `<br/>PM2.5 ${Math.round(d.pm25)} · NO2 ${Math.round(d.no2 ?? 0)} µg/m³` : "");
        },
      },
      xAxis: {
        type: "category",
        data: days.map((d) => (compact || !few ? fmtWeekday(d.date) + (few ? "" : " " + d.date.slice(8, 10)) : fmtDay(d.date))),
        boundaryGap: few,
        axisLine: { lineStyle: { color: c.axis } },
        axisTick: { show: false },
        axisLabel: { color: c.faint, fontSize: 11, interval: few ? 0 : 3 },
      },
      yAxis: {
        type: "value", min: lo, max: hi,
        splitLine: { lineStyle: { color: c.grid } },
        axisLabel: { color: c.faint, fontFamily: "IBM Plex Mono, monospace", fontSize: 11 },
      },
      visualMap: {
        show: false, dimension: 1,
        pieces: AQI_CATEGORIES.map((cat, i) => ({ gt: i === 0 ? -1 : AQI_CATEGORIES[i - 1].max, lte: i === AQI_CATEGORIES.length - 1 ? 10000 : cat.max, color: cat.color })),
      },
      series: [{
        type: "line", data: values, smooth: 0.35, symbol: "circle", symbolSize: few ? 7 : 4,
        lineStyle: { width: 2.5 }, areaStyle: { opacity: 0.1 },
        label: { show: few, position: "top", color: c.muted, fontFamily: "IBM Plex Mono, monospace", fontSize: 11 },
        markArea: {
          silent: true,
          data: BANDS.filter((b) => b.hi > lo && b.lo < hi).map((b) => [
            { yAxis: Math.max(b.lo, lo), itemStyle: { color: b.color, opacity: c.dark ? 0.07 : 0.06 } },
            { yAxis: Math.min(b.hi, hi) },
          ]),
        },
      }],
    };
  }, [days, compact, c]);

  return <EChart option={option} className={className} ariaLabel="AQI forecast chart" />;
}
