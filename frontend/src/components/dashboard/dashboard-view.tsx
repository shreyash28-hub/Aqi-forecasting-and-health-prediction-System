"use client";

import { useCallback, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { AppHeader } from "@/components/layout/app-header";
import { AppFooter } from "@/components/layout/footer";
import { ErrorState } from "@/components/common";
import { CITIES } from "@/lib/content";
import { useCityForecasts, useExampleRisk } from "./use-dashboard-data";
import { CitiesTable, CityTabs, ForecastCard, PageHead, PollutantsCard, PrecautionsCard, RiskCard, TomorrowCard } from "./sections";

export function DashboardView() {
  const params = useSearchParams();
  const router = useRouter();
  const path = usePathname();
  const city = CITIES.find((c) => c.toLowerCase() === (params.get("city") ?? "").toLowerCase()) ?? "Delhi";
  const horizon = params.get("h") === "30" ? 30 : 7;

  const setParams = useCallback((next: { city?: string; h?: number }) => {
    const sp = new URLSearchParams(params.toString());
    if (next.city) sp.set("city", next.city);
    if (next.h) sp.set("h", String(next.h));
    router.replace(`${path}?${sp.toString()}`, { scroll: false });
  }, [params, path, router]);

  const forecasts = useCityForecasts();
  const risk = useExampleRisk(city);
  const selected = forecasts.data?.byCity[city];
  // Day whose precautions are shown; ignored once the city's days no longer include it.
  const [riskDay, setRiskDay] = useState<string>();

  return (
    <div className="min-h-screen bg-page">
      <AppHeader city={city} onCityChange={(c) => setParams({ city: c })} />
      <main className="shell">
        <PageHead city={city} forecast={selected} horizon={horizon} onHorizon={(h) => setParams({ h })} />
        {forecasts.error ? (
          <ErrorState message={forecasts.error.message} onRetry={forecasts.retry} />
        ) : (
          <>
            <CityTabs byCity={forecasts.data?.byCity} city={city} onSelect={(c) => setParams({ city: c })} />
            <div className="grid grid-cols-12 gap-4">
              <TomorrowCard days={selected?.days} horizon={horizon} />
              <ForecastCard days={selected?.days} horizon={horizon} />
              {risk.error ? (
                <ErrorState className="col-span-12" message={risk.error.message} onRetry={risk.retry} />
              ) : (
                <>
                  <RiskCard risk={risk.data} loading={risk.loading} selected={riskDay} onSelect={setRiskDay} />
                  <PollutantsCard days={selected?.days} horizon={horizon} />
                  <PrecautionsCard risk={risk.data} selected={riskDay} onSelect={setRiskDay} />
                </>
              )}
              <CitiesTable byCity={forecasts.data?.byCity} onSelect={(c) => { setParams({ city: c }); window.scrollTo({ top: 0, behavior: "smooth" }); }} />
            </div>
          </>
        )}
      </main>
      <AppFooter />
    </div>
  );
}
