import { Suspense } from "react";
import type { Metadata } from "next";
import { ForecastView } from "@/components/forecast/forecast-view";

export const metadata: Metadata = { title: "Forecast" };

export default function ForecastPage() {
  // ForecastView reads ?city= from the URL, which needs a Suspense boundary.
  return (
    <Suspense fallback={<div className="min-h-screen bg-page" />}>
      <ForecastView />
    </Suspense>
  );
}
