import type { Metadata } from "next";
import { ComingSoon } from "@/components/layout/coming-soon";

export const metadata: Metadata = { title: "Models" };

export default function Page() {
  return <ComingSoon title="Models" text="The full model leaderboard for forecasting and health-risk models is being built." />;
}
