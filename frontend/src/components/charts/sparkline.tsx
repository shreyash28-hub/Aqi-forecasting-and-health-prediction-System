"use client";

import { useMemo } from "react";
import type { EChartsCoreOption } from "echarts/core";
import { EChart } from "./echart";

/** Tiny trend line without axes. */
export function Sparkline({ values, color, className }: { values: number[]; color: string; className?: string }) {
  const option = useMemo<EChartsCoreOption>(() => ({
    animationDuration: 600,
    grid: { left: 2, right: 2, top: 4, bottom: 4 },
    xAxis: { type: "category", show: false, data: values.map((_, i) => i) },
    yAxis: { type: "value", show: false, scale: true },
    series: [{
      type: "line", data: values, smooth: true, symbol: "none", lineStyle: { width: 2, color },
      areaStyle: { color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: color + "33" }, { offset: 1, color: color + "00" }] } },
    }],
  }), [values, color]);
  return <EChart option={option} className={className} ariaLabel="Trend" />;
}
