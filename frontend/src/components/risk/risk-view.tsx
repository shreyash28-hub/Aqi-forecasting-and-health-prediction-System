"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Loader2, Pencil, RefreshCw } from "lucide-react";
import type { Session } from "@supabase/supabase-js";
import { ErrorState } from "@/components/common";
import { PrimaryButton } from "@/components/forms";
import { Skeleton } from "@/components/ui/skeleton";
import { useAsync } from "@/hooks/use-async";
import { meApi, type SavedProfile } from "@/lib/api";
import { CITIES } from "@/lib/content";
import { cn } from "@/lib/utils";
import { RiskResult, fromHistory, fromRun, type RiskResultData } from "./risk-result";

const CONDITION_LABEL: Record<string, string> = { "No Condition": "No condition", HeartDisease: "Heart disease", Hypertension: "High blood pressure" };

/**
 * Loads the saved profile and the latest estimate. A new estimate (saved to history)
 * is only calculated when there is none yet or the profile changed since the last one.
 */
async function loadInitial(token: string, signal: AbortSignal): Promise<{ profile: SavedProfile | null; result?: RiskResultData }> {
  const me = meApi(token);
  const profile = await me.profile(signal);
  if (!profile) return { profile };
  const [latest] = await me.history(1, signal);
  const stale = !latest || (profile.updated_at && Date.parse(profile.updated_at) > Date.parse(latest.predicted_at));
  if (!stale) return { profile, result: fromHistory(await me.historyRun(latest.forecast_id, signal)) };
  return { profile, result: fromRun(await me.runRisk({ horizon: 7 }, signal)) };
}

export function RiskView({ session }: { session: Session }) {
  const router = useRouter();
  const init = useAsync((signal) => loadInitial(session.access_token, signal), [session.user.id]);
  const noProfile = init.data && !init.data.profile;

  useEffect(() => {
    if (noProfile) router.replace("/profile");
  }, [noProfile, router]);

  if (init.error) return <ErrorState message={init.error.message} onRetry={init.retry} />;
  if (!init.data?.profile || !init.data.result) return <RiskSkeleton />;
  return <RiskBody token={session.access_token} profile={init.data.profile} initial={init.data.result} />;
}

function RiskBody({ token, profile, initial }: { token: string; profile: SavedProfile; initial: RiskResultData }) {
  const [result, setResult] = useState(initial);
  const [city, setCity] = useState(initial.city);
  const [horizon, setHorizon] = useState(initial.horizon);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();
  const changed = city !== result.city || horizon !== result.horizon;

  async function update() {
    setBusy(true);
    setError(undefined);
    try {
      setResult(fromRun(await meApi(token).runRisk({ city, horizon })));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const tags = [
    `${profile.age} yrs`, CONDITION_LABEL[profile.condition] ?? profile.condition, profile.smoker ? "Smoker" : "Non-smoker",
    profile.occupation, `${profile.area_type} area`, `${profile.outdoor_hours} h outdoors/day`,
    profile.mask_usage === "Yes" ? "Wears a mask" : profile.mask_usage === "Sometimes" ? "Mask sometimes" : "No mask",
  ];

  return (
    <>
      <div className="flex flex-wrap items-end gap-x-6 gap-y-4 pt-6 pb-4">
        <div className="min-w-0">
          <h1 className="text-[26px] font-semibold tracking-tight">Your health risk</h1>
          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            {tags.map((t) => <span key={t} className="rounded-[5px] bg-muted px-2 py-0.5 text-xs text-muted-foreground">{t}</span>)}
            <Link href="/profile" className="ml-1 flex items-center gap-1 text-[13px] font-medium text-brand-ink hover:underline"><Pencil className="size-3.5" aria-hidden />Edit profile</Link>
          </div>
        </div>
        <div className="ml-auto flex flex-wrap items-center gap-2.5">
          <label className="sr-only" htmlFor="risk-city">City</label>
          <select id="risk-city" value={city} onChange={(e) => setCity(e.target.value)}
            className="h-9 rounded-[7px] border border-border-strong bg-card px-2.5 text-sm font-medium">
            {CITIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <div role="radiogroup" aria-label="Forecast horizon" className="inline-flex overflow-hidden rounded-[7px] border border-border-strong bg-card">
            {[7, 30].map((h) => (
              <button key={h} role="radio" aria-checked={horizon === h} onClick={() => setHorizon(h)}
                className={cn("px-3.5 py-1.5 text-[13px] font-medium", horizon === h ? "bg-muted text-foreground" : "text-muted-foreground hover:text-foreground")}>
                {h} days
              </button>
            ))}
          </div>
          <PrimaryButton onClick={update} disabled={busy} className="h-9 px-4">
            {busy ? <Loader2 className="size-4 animate-spin" aria-hidden /> : <RefreshCw className="size-4" aria-hidden />}
            {changed ? "Show estimate" : "Recalculate"}
          </PrimaryButton>
        </div>
      </div>
      {error && <p className="mb-4 rounded-[7px] bg-destructive/10 px-3 py-2 text-[13px] text-destructive" role="alert">Couldn&apos;t calculate the estimate: {error}</p>}
      <RiskResult data={result} busy={busy} />
    </>
  );
}

function RiskSkeleton() {
  return (
    <div className="pt-6" aria-busy="true">
      <Skeleton className="h-8 w-64" />
      <Skeleton className="mt-3 h-5 w-[520px]" />
      <div className="mt-6 grid grid-cols-12 gap-4">
        <Skeleton className="col-span-4 h-[300px] wide:col-span-3" />
        <Skeleton className="col-span-8 h-[300px] wide:col-span-9" />
        <Skeleton className="col-span-6 h-[320px]" />
        <Skeleton className="col-span-6 h-[320px]" />
      </div>
    </div>
  );
}
