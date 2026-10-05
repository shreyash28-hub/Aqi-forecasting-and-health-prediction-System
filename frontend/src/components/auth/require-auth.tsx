"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import type { Session } from "@supabase/supabase-js";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "./auth-provider";

/** Renders children with the session once signed in; otherwise sends the user to sign in. */
export function RequireAuth({ children }: { children: (session: Session) => React.ReactNode }) {
  const { session, loading } = useAuth();
  const router = useRouter();
  const path = usePathname();

  useEffect(() => {
    if (!loading && !session) router.replace(`/sign-in?next=${encodeURIComponent(path)}`);
  }, [loading, session, path, router]);

  if (!session) {
    return (
      <div className="space-y-4 py-8" aria-busy="true">
        <Skeleton className="h-8 w-72" />
        <Skeleton className="h-64" />
      </div>
    );
  }
  return <>{children(session)}</>;
}
