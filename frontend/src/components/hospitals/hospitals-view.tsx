"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { AppHeader } from "@/components/layout/app-header";
import { AppFooter } from "@/components/layout/footer";
import { CITIES } from "@/lib/content";
import { HospitalsPanel } from "./hospitals-panel";

/** Public page: hospitals near a city centre (or the visitor's location), with contact details. */
export function HospitalsView() {
  const params = useSearchParams();
  const router = useRouter();
  const path = usePathname();
  const city = CITIES.find((c) => c.toLowerCase() === (params.get("city") ?? "").toLowerCase()) ?? "Delhi";
  const setCity = (c: string) => router.replace(`${path}?city=${encodeURIComponent(c)}`, { scroll: false });

  return (
    <div className="flex min-h-screen flex-col bg-page">
      <AppHeader city={city} onCityChange={setCity} />
      <main className="shell flex-1 pb-4">
        <div className="pt-6 pb-4">
          <h1 className="text-[26px] font-semibold tracking-tight">Hospitals in {city}</h1>
          <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
            Phone numbers, addresses and directions for hospitals near you, so you can call ahead when air quality puts your health at risk.
          </p>
        </div>
        <HospitalsPanel key={city} city={city} />
      </main>
      <AppFooter />
    </div>
  );
}
