import { Suspense } from "react";
import type { Metadata } from "next";
import { DashboardView } from "@/components/dashboard/dashboard-view";

export const metadata: Metadata = { title: "Dashboard" };

export default function DashboardPage() {
  // DashboardView reads ?city= and ?h= from the URL, which needs a Suspense boundary.
  return (
    <Suspense fallback={<div className="min-h-screen bg-page" />}>
      <DashboardView />
    </Suspense>
  );
}
