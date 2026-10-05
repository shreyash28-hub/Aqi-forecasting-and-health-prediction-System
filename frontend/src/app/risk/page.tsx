import type { Metadata } from "next";
import { ComingSoon } from "@/components/layout/coming-soon";

export const metadata: Metadata = { title: "My risk" };

export default function Page() {
  return <ComingSoon title="My risk" text="Your personal day-by-day risk, based on your saved profile, is being built. The dashboard shows an example profile in the meantime." />;
}
