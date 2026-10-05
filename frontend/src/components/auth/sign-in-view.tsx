"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2, MailCheck } from "lucide-react";
import { Brand } from "@/components/layout/brand";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { Field, PrimaryButton, inputClass } from "@/components/forms";
import { useAuth } from "./auth-provider";
import { authConfigured, supabase } from "@/lib/supabase";
import { cn } from "@/lib/utils";

type Mode = "sign-in" | "sign-up";

/** Turns Supabase auth errors into plain sentences. */
function friendly(message: string): string {
  const m = message.toLowerCase();
  if (m.includes("invalid login")) return "That email and password don't match. Check them and try again.";
  if (m.includes("email not confirmed")) return "Confirm your email first. Open the link we sent you, then sign in.";
  if (m.includes("already registered") || m.includes("already been registered")) return "An account with this email already exists. Sign in instead.";
  if (m.includes("password") && m.includes("characters")) return "Use a password of at least 6 characters.";
  if (m.includes("rate limit")) return "Too many attempts. Wait a minute and try again.";
  if (m.includes("fetch")) return "Can't reach the sign-in service. Check your connection and try again.";
  return message;
}

/** Only allow redirects within this site. */
const safeNext = (next: string | null) => (next && next.startsWith("/") && !next.startsWith("//") ? next : "/risk");

export function SignInView() {
  const params = useSearchParams();
  const router = useRouter();
  const { session, loading } = useAuth();
  const next = safeNext(params.get("next"));
  const [mode, setMode] = useState<Mode>(params.get("mode") === "sign-up" ? "sign-up" : "sign-in");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const [sentTo, setSentTo] = useState<string>();

  // Already signed in (or just confirmed via the email link): continue.
  useEffect(() => {
    if (!loading && session) router.replace(next);
  }, [loading, session, next, router]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(undefined);
    if (!/^\S+@\S+\.\S+$/.test(email)) return setError("Enter a valid email address.");
    if (password.length < 6) return setError("Use a password of at least 6 characters.");
    setBusy(true);
    try {
      const auth = supabase().auth;
      if (mode === "sign-in") {
        const { error } = await auth.signInWithPassword({ email, password });
        if (error) return setError(friendly(error.message));
        router.replace(next);
      } else {
        const { data, error } = await auth.signUp({
          email, password, options: { emailRedirectTo: `${window.location.origin}/sign-in?next=${encodeURIComponent("/profile")}` },
        });
        if (error) return setError(friendly(error.message));
        if (data.session) router.replace("/profile");   // email confirmation turned off
        else setSentTo(email);
      }
    } catch (err) {
      setError(friendly((err as Error).message));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-page">
      <header className="shell flex h-[62px] items-center justify-between">
        <Brand />
        <ThemeToggle />
      </header>
      <main className="grid flex-1 place-items-center px-4 pb-16">
        <div className="w-full max-w-[420px] rounded-[12px] border bg-card p-7 shadow-[0_1px_2px_rgba(0,0,0,.04),0_20px_40px_-24px_rgba(10,30,40,.25)]">
          {sentTo ? (
            <div className="text-center">
              <span className="mx-auto grid size-11 place-items-center rounded-full bg-brand-soft text-brand-ink"><MailCheck className="size-5" aria-hidden /></span>
              <h1 className="mt-4 text-xl font-semibold">Check your email</h1>
              <p className="mt-2 text-sm text-muted-foreground">
                We sent a confirmation link to <b className="font-medium text-foreground">{sentTo}</b>. Open it to finish creating your account, then you&apos;ll set up your profile.
              </p>
              <button className="mt-6 text-sm font-medium text-brand-ink hover:underline" onClick={() => { setSentTo(undefined); setMode("sign-in"); }}>
                Back to sign in
              </button>
            </div>
          ) : (
            <>
              <h1 className="text-xl font-semibold">{mode === "sign-in" ? "Sign in to Airware" : "Create your account"}</h1>
              <p className="mt-1.5 text-sm text-muted-foreground">
                {mode === "sign-in" ? "See your personal risk and saved history." : "Save your health profile once and keep a history of your estimates."}
              </p>
              <div role="tablist" aria-label="Sign in or create account" className="mt-6 grid grid-cols-2 rounded-[8px] bg-muted p-1">
                {(["sign-in", "sign-up"] as Mode[]).map((m) => (
                  <button key={m} role="tab" type="button" aria-selected={mode === m} onClick={() => { setMode(m); setError(undefined); }}
                    className={cn("rounded-[6px] py-1.5 text-sm font-medium", mode === m ? "bg-card shadow-sm" : "text-muted-foreground hover:text-foreground")}>
                    {m === "sign-in" ? "Sign in" : "Create account"}
                  </button>
                ))}
              </div>
              {!authConfigured ? (
                <p className="mt-6 rounded-[8px] border border-dashed p-4 text-sm text-muted-foreground">
                  Sign-in isn&apos;t configured on this server. Add NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY to frontend/.env.local.
                </p>
              ) : (
                <form onSubmit={submit} noValidate className="mt-6 flex flex-col gap-4">
                  <Field label="Email" htmlFor="email">
                    <input id="email" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)}
                      placeholder="name@example.com" className={inputClass} required />
                  </Field>
                  <Field label="Password" htmlFor="password" hint={mode === "sign-up" ? "At least 6 characters." : undefined}>
                    <input id="password" type="password" autoComplete={mode === "sign-in" ? "current-password" : "new-password"}
                      value={password} onChange={(e) => setPassword(e.target.value)} className={inputClass} required />
                  </Field>
                  {error && <p className="rounded-[7px] bg-destructive/10 px-3 py-2 text-[13px] text-destructive" role="alert">{error}</p>}
                  <PrimaryButton type="submit" disabled={busy} className="mt-1 w-full">
                    {busy && <Loader2 className="size-4 animate-spin" aria-hidden />}
                    {mode === "sign-in" ? "Sign in" : "Create account"}
                  </PrimaryButton>
                </form>
              )}
              <p className="mt-6 text-center text-[13px] text-faint">
                Forecasts are free without an account. <Link href="/dashboard" className="font-medium text-brand-ink hover:underline">Open the dashboard</Link>
              </p>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
