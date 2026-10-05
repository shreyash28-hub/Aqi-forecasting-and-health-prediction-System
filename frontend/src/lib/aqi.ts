import type { CSSProperties } from "react";
import type { RiskLevel } from "./api";

// CPCB National AQI categories. Colours mirror --color-aqi-* in globals.css; charts
// need the literal values because ECharts can't read CSS variables.
export const AQI_CATEGORIES = [
  { key: "good", name: "Good", min: 0, max: 50, color: "#2e9e5b",
    advice: "Minimal impact." },
  { key: "satisfactory", name: "Satisfactory", min: 51, max: 100, color: "#8cc152",
    advice: "Minor breathing discomfort possible for sensitive people." },
  { key: "moderate", name: "Moderate", min: 101, max: 200, color: "#e8b923",
    advice: "Breathing discomfort possible for people with lung or heart disease, children and older adults." },
  { key: "poor", name: "Poor", min: 201, max: 300, color: "#ea8a2e",
    advice: "Breathing discomfort for most people on prolonged exposure." },
  { key: "very-poor", name: "Very poor", min: 301, max: 400, color: "#d9453f",
    advice: "Respiratory illness possible on prolonged exposure." },
  { key: "severe", name: "Severe", min: 401, max: 500, color: "#8e2436",
    advice: "Affects healthy people and seriously impacts those with existing disease." },
] as const;

export type AqiCategory = (typeof AQI_CATEGORIES)[number];

export function aqiCategory(aqi: number): AqiCategory {
  return AQI_CATEGORIES.find((c) => Math.round(aqi) <= c.max) ?? AQI_CATEGORIES[AQI_CATEGORIES.length - 1];
}

/** Position (0-1) on a scale of six equal-width bands, placed within the AQI's own band. */
export function scalePosition(aqi: number): number {
  const edges = [0, 50, 100, 200, 300, 400, 500];
  const v = Math.min(Math.max(aqi, 0), 500);
  const band = Math.max(0, edges.findIndex((e, i) => i > 0 && v <= e) - 1);
  return (band + (v - edges[band]) / (edges[band + 1] - edges[band])) / 6;
}

export const RISK_LEVELS: RiskLevel[] = ["Low", "Moderate", "High", "Severe"];

export const RISK_COLOR: Record<RiskLevel, string> = {
  Low: "#2e9e5b",
  Moderate: "#e8b923",
  High: "#ea8a2e",
  Severe: "#d9453f",
};

/** Tinted chip background + readable text for a data colour (works in light and dark). */
export function chipStyle(color: string): CSSProperties {
  return {
    background: `color-mix(in srgb, ${color} 18%, transparent)`,
    color: `color-mix(in srgb, ${color} 72%, var(--foreground))`,
  };
}

// The model's raw risk score is unbounded (about 0-18). For display it is mapped to a
// 0-100 scale in which each risk level fills a quarter: Low 0-25, Moderate 25-50,
// High 50-75, Severe 75-100 (raw 1.0 / 1.8 / 2.8 are the level cut-offs; 6+ shows as 100).
const SCORE_KNOTS: Array<[number, number]> = [[0, 0], [1.0, 25], [1.8, 50], [2.8, 75], [6.0, 100]];

export function scoreToPoints(raw: number): number {
  const v = Math.max(raw, 0);
  for (let i = 1; i < SCORE_KNOTS.length; i++) {
    const [x0, y0] = SCORE_KNOTS[i - 1], [x1, y1] = SCORE_KNOTS[i];
    if (v <= x1) return Math.round(y0 + ((v - x0) / (x1 - x0)) * (y1 - y0));
  }
  return 100;
}
