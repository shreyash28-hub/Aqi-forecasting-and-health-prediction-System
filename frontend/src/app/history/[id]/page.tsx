"use client";

import { useParams } from "next/navigation";
import { AppHeader } from "@/components/layout/app-header";
import { AppFooter } from "@/components/layout/footer";
import { RequireAuth } from "@/components/auth/require-auth";
import { HistoryDetailView } from "@/components/history/history-view";

export default function HistoryRunPage() {
  const { id } = useParams<{ id: string }>();
  return (
    <div className="flex min-h-screen flex-col bg-page">
      <AppHeader />
      <main className="shell flex-1 pb-4">
        <RequireAuth>{(session) => <HistoryDetailView session={session} id={id} />}</RequireAuth>
      </main>
      <AppFooter />
    </div>
  );
}
