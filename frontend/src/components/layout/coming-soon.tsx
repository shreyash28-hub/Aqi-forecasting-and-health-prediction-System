import Link from "next/link";
import { AppHeader } from "./app-header";
import { AppFooter } from "./footer";

/** Temporary page for routes in the nav that are built in the next step. */
export function ComingSoon({ title, text }: { title: string; text: string }) {
  return (
    <div className="flex min-h-screen flex-col bg-page">
      <AppHeader />
      <main className="shell flex-1 py-10">
        <h1 className="text-[26px] font-semibold tracking-tight">{title}</h1>
        <div className="mt-6 max-w-2xl rounded-[10px] border bg-card p-6">
          <p className="text-muted-foreground">{text}</p>
          <Link href="/dashboard" className="mt-5 inline-flex h-9 items-center rounded-[7px] bg-brand px-4 text-sm font-medium text-on-brand hover:brightness-110">
            Go to the dashboard
          </Link>
        </div>
      </main>
      <AppFooter />
    </div>
  );
}
