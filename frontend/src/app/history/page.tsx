import type { Metadata } from "next";
import { ComingSoon } from "@/components/layout/coming-soon";

export const metadata: Metadata = { title: "History" };

export default function Page() {
  return <ComingSoon title="History" text="Your saved estimates will appear here once sign-in is connected." />;
}
