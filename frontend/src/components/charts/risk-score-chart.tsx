"use client";

import { useMemo } from "react";
import type { EChartsCoreOption } from "echarts/core";
import { EChart } from "./echart";
import { RISK_COLOR, RISK_LEVELS } from "@/lib/aqi";
import { fmtDay, fmtWeekday } from "@/lib/format";
import { useChartColors } from "@/components/theme/theme-provider";
import type { RiskDay } from "@/lib/api";

/** Score cut-offs between levels (same as the backend's score_to_level). */
export const SCORE_CUTS = [1.0, 1.8, 2.8];
const BANDS = [0, ...SCORE_CUTS, 5].slice(0, -1).map((lo, i, a) => ({ lo, hi: a[i + 1] ?? 5, level: RISK_LEVELS[i] }));

/** Daily risk score with the four risk-level bands behind it. */
export function RiskScoreChart({ days, className }: { days: RiskDay[]; className?: string }) {
  const c = useChartColors();
  const option = useMemo<EChartsCoreOption>(() => {
    const scores = days.map((d) => +d.risk_score.toFixed(2));
    const few = days.length <= 10;
    const hi = Math.max(3.4, Math.ceil((Math.max(...scores) + 0.3) * 2) / 2);
    return {
      animationDuration: 800,
      grid: { left: 42, right: 70, top: few ? 26 : 16, bottom: 28 },
      tooltip: {
        trigger: "axis",
        backgroundColor: c.surface,
        borderColor: c.axis,
        textStyle: { color: c.text, fontFamily: "var(--font-plex-sans), sans-serif", fontSize: 12 },
        formatter: (p: Array<{ dataIndex: number }>) => {
          const d = days[p[0].dataIndex];
          return `${fmtDay(d.date)}<br/><b>${d.risk_range}</b>${d.borderline ? " (borderline)" : ""}<br/>` +
            `Score <b style="font-family:var(--font-plex-mono)">${d.risk_score.toFixed(2)}</b> · ${Math.round(d.confidence * 100)}% confidence`;
        },
      },
      xAxis: {
        type: "category",
        data: days.map((d) => (few ? fmtDay(d.date) : fmtWeekday(d.date) + " " + d.date.slice(8, 10))),
        boundaryGap: few,
        axisLine: { lineStyle: { color: c.axis } },
        axisTick: { show: false },
        axisLabel: { color: c.faint, fontSize: 11, interval: few ? 0 : 3 },
      },
      yAxis: {
        type: "value", min: 0, max: hi, interval: 1,
        splitLine: { show: false },
        axisLabel: { color: c.faint, fontFamily: "IBM Plex Mono, monospace", fontSize: 11 },
      },
      series: [{
        type: "line", data: scores, smooth: 0.3, symbol: "circle", symbolSize: few ? 8 : 4,
        lineStyle: { width: 2, color: c.text }, itemStyle: { color: c.text, borderColor: c.surface, borderWidth: 2 },
        label: { show: few, position: "top", color: c.muted, fontFamily: "IBM Plex Mono, monospace", fontSize: 11, formatter: (p: { value: number }) => p.value.toFixed(1) },
        markArea: {
          silent: true,
          data: BANDS.filter((b) => b.lo < hi).map((b) => [
            { yAxis: b.lo, name: b.level, itemStyle: { color: RISK_COLOR[b.level], opacity: c.dark ? 0.12 : 0.1 },
              label: { show: true, position: "right", color: c.muted, fontSize: 11, distance: 8 } },
            { yAxis: Math.min(b.hi, hi) },
          ]),
        },
      }],
    };
  }, [days, c]);

  return <EChart option={option} className={className} ariaLabel="Daily risk score chart" />;
}
