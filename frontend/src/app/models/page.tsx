import { Suspense } from "react";
import type { Metadata } from "next";
import { AppHeader } from "@/components/layout/app-header";
import { AppFooter } from "@/components/layout/footer";
import { ModelsView } from "@/components/models/models-view";

export const metadata: Metadata = { title: "Models" };

export default function ModelsPage() {
  return (
    <div className="flex min-h-screen flex-col bg-page">
      <AppHeader />
      <main className="shell flex-1 pb-4">
        <Suspense><ModelsView /></Suspense>
      </main>
      <AppFooter />
    </div>
  );
}
