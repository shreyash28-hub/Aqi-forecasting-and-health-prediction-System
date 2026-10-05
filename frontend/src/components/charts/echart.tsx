"use client";

import { useEffect, useRef } from "react";
import * as echarts from "echarts/core";
import { LineChart } from "echarts/charts";
import { GridComponent, MarkAreaComponent, TooltipComponent, VisualMapComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import type { EChartsCoreOption } from "echarts/core";

echarts.use([LineChart, GridComponent, TooltipComponent, VisualMapComponent, MarkAreaComponent, CanvasRenderer]);

/** Minimal ECharts wrapper: one instance per element, resizes with its container. */
export function EChart({ option, className, ariaLabel }: { option: EChartsCoreOption; className?: string; ariaLabel?: string }) {
  const el = useRef<HTMLDivElement>(null);
  const chart = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!el.current) return;
    chart.current = echarts.init(el.current, undefined, { renderer: "canvas" });
    const ro = new ResizeObserver(() => chart.current?.resize());
    ro.observe(el.current);
    return () => { ro.disconnect(); chart.current?.dispose(); chart.current = null; };
  }, []);

  useEffect(() => {
    chart.current?.setOption(option, { notMerge: true });
  }, [option]);

  return <div ref={el} className={className} role="img" aria-label={ariaLabel} />;
}
