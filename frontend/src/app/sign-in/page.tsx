import type { Metadata } from "next";
import { ComingSoon } from "@/components/layout/coming-soon";

export const metadata: Metadata = { title: "Sign in" };

export default function Page() {
  return <ComingSoon title="Sign in" text="Email sign-in with your Airware account is being connected." />;
}
