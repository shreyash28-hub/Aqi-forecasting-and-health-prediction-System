"use client";

import { AppHeader } from "@/components/layout/app-header";
import { AppFooter } from "@/components/layout/footer";
import { RequireAuth } from "@/components/auth/require-auth";
import { RiskView } from "@/components/risk/risk-view";

export default function RiskPage() {
  return (
    <div className="flex min-h-screen flex-col bg-page">
      <AppHeader />
      <main className="shell flex-1 pb-4">
        <RequireAuth>{(session) => <RiskView session={session} />}</RequireAuth>
      </main>
      <AppFooter />
    </div>
  );
}
