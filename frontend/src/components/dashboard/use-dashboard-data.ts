"use client";

import { api, type CityInfo, type ForecastResponse, type RiskResponse } from "@/lib/api";
import { CITIES, EXAMPLE_PROFILES } from "@/lib/content";
import { useAsync } from "@/hooks/use-async";

export interface CityForecasts {
  info: CityInfo[];
  /** 30-day forecast per city; shorter horizons are slices of it. */
  byCity: Record<string, ForecastResponse>;
}

/** All six cities' 30-day forecasts, loaded once and shared by tabs, chart and table. */
export function useCityForecasts() {
  return useAsync<CityForecasts>(async (signal) => {
    const [info, ...forecasts] = await Promise.all([
      api.cities(signal),
      ...CITIES.map((c) => api.forecast(c, 30, signal)),
    ]);
    return { info, byCity: Object.fromEntries(forecasts.map((f) => [f.city, f])) };
  }, []);
}

/** 7-day risk for the example profile in the selected city (until the user signs in). */
export function useExampleRisk(city: string) {
  return useAsync<RiskResponse>(
    (signal) => api.predictRisk({ city, horizon: 7, profile: EXAMPLE_PROFILES.ramesh.profile }, signal),
    [city],
  );
}
