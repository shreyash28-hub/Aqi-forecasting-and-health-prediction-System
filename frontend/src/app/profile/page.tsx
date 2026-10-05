"use client";

import { AppHeader } from "@/components/layout/app-header";
import { AppFooter } from "@/components/layout/footer";
import { RequireAuth } from "@/components/auth/require-auth";
import { ProfileWizard } from "@/components/profile/profile-wizard";

export default function ProfilePage() {
  return (
    <div className="flex min-h-screen flex-col bg-page">
      <AppHeader />
      <main className="shell flex-1 py-8">
        <div className="mx-auto max-w-[980px]">
          <h1 className="text-[26px] font-semibold tracking-tight">Your health profile</h1>
          <p className="mt-1 mb-6 text-sm text-muted-foreground">Filled in once and reused for every estimate. You can change it any time.</p>
          <RequireAuth>{(session) => <ProfileWizard session={session} />}</RequireAuth>
        </div>
      </main>
      <AppFooter />
    </div>
  );
}
