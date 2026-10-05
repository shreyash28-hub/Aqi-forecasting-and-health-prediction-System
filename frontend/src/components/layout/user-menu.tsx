"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { History, LogOut, UserRound } from "lucide-react";
import { useAuth } from "@/components/auth/auth-provider";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";

/** "Sign in" when signed out; an account menu (profile, history, sign out) when signed in. */
export function UserMenu() {
  const { session, loading, signOut } = useAuth();
  const router = useRouter();

  if (loading) return <span className="h-9 w-[76px] rounded-[7px] border border-border-strong bg-card" aria-hidden />;
  if (!session) {
    return (
      <Link href="/sign-in" className="flex h-9 items-center rounded-[7px] border border-border-strong bg-card px-3.5 text-sm font-medium hover:bg-muted">
        Sign in
      </Link>
    );
  }
  const email = session.user.email ?? "Account";
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        aria-label="Account menu"
        className="flex h-9 items-center gap-2 rounded-[7px] border border-border-strong bg-card pr-3 pl-1.5 text-sm font-medium hover:bg-muted"
      >
        <span className="grid size-6 place-items-center rounded-full bg-brand-soft text-xs font-semibold text-brand-ink uppercase">{email[0]}</span>
        <span className="max-w-40 truncate">{email}</span>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-52">
        <DropdownMenuItem onClick={() => router.push("/profile")}><UserRound className="size-4" aria-hidden />Your profile</DropdownMenuItem>
        <DropdownMenuItem onClick={() => router.push("/history")}><History className="size-4" aria-hidden />History</DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={async () => { await signOut(); router.push("/"); }}><LogOut className="size-4" aria-hidden />Sign out</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
