import type { Metadata } from "next";
import { ComingSoon } from "@/components/layout/coming-soon";

export const metadata: Metadata = { title: "Forecast" };

export default function Page() {
  return <ComingSoon title="Forecast" text="A detailed 30-day view of AQI, PM2.5 and NO2 for each city is being built. The dashboard already shows the 7 and 30-day forecast." />;
}
