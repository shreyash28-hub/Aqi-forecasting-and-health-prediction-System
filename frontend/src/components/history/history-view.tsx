"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, ChevronRight, History as HistoryIcon, Loader2, Trash2 } from "lucide-react";
import type { Session } from "@supabase/supabase-js";
import { ErrorState, Panel } from "@/components/common";
import { PrimaryButton, SecondaryButton } from "@/components/forms";
import { Skeleton } from "@/components/ui/skeleton";
import { useAsync } from "@/hooks/use-async";
import { meApi, type HistoryItem } from "@/lib/api";
import { fmtDayMonth } from "@/lib/format";
import { LevelChip, LevelMix, RiskResult, fromHistory } from "@/components/risk/risk-result";

const fmtWhen = (iso: string) =>
  new Date(iso).toLocaleString("en-GB", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });

const forecastSpan = (h: { origin_date: string; horizon: number }) => {
  const start = new Date(`${h.origin_date}T00:00:00`);
  const first = new Date(start), last = new Date(start);
  first.setDate(start.getDate() + 1);
  last.setDate(start.getDate() + h.horizon);
  const iso = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  return `${fmtDayMonth(iso(first))} – ${fmtDayMonth(iso(last))}`;
};

// ------------------------------------------------------------------ list

export function HistoryList({ session }: { session: Session }) {
  const runs = useAsync((signal) => meApi(session.access_token).history(100, signal), [session.user.id]);
  const [removed, setRemoved] = useState<string[]>([]);
  const items = runs.data?.filter((r) => !removed.includes(r.forecast_id));

  return (
    <>
      <div className="flex flex-wrap items-end gap-4 pt-6 pb-4">
        <div>
          <h1 className="text-[26px] font-semibold tracking-tight">History</h1>
          <p className="mt-1 text-sm text-muted-foreground">Every estimate you calculate is saved here, newest first.</p>
        </div>
        <Link href="/risk" className="ml-auto flex h-9 items-center rounded-[7px] bg-brand px-4 text-sm font-medium text-on-brand hover:brightness-110">New estimate</Link>
      </div>
      {runs.error ? <ErrorState message={runs.error.message} onRetry={runs.retry} />
        : !items ? <Skeleton className="h-[420px]" />
        : items.length === 0 ? <EmptyHistory />
        : (
          <Panel className="p-0 lg:p-0">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="text-left text-xs text-faint [&>th]:border-b [&>th]:px-5 [&>th]:py-3 [&>th]:font-medium">
                  <th>Calculated</th><th>City</th><th>Forecast days</th><th>Highest risk</th><th className="w-[34%]">Days by level</th><th className="text-right">Borderline</th><th><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody>
                {items.map((r) => (
                  <HistoryRow key={r.forecast_id} run={r} token={session.access_token} onDeleted={() => setRemoved((x) => [...x, r.forecast_id])} />
                ))}
              </tbody>
            </table>
          </Panel>
        )}
    </>
  );
}

function HistoryRow({ run: r, token, onDeleted }: { run: HistoryItem; token: string; onDeleted: () => void }) {
  const router = useRouter();
  const href = `/history/${r.forecast_id}`;
  return (
    <tr onClick={() => router.push(href)} className="cursor-pointer hover:bg-muted [&>td]:border-b [&>td]:px-5 [&>td]:py-3 last:[&>td]:border-b-0">
      <td><Link href={href} className="font-medium hover:underline" onClick={(e) => e.stopPropagation()}>{fmtWhen(r.predicted_at)}</Link></td>
      <td>{r.city}</td>
      <td className="text-muted-foreground">{r.horizon} days · {forecastSpan(r)}</td>
      <td><LevelChip level={r.summary.highest_alert_level} /></td>
      <td><LevelMix counts={r.summary.days_by_level} total={r.horizon} /></td>
      <td className="num text-right">{r.summary.borderline_days}</td>
      <td className="text-right" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-end gap-1">
          <DeleteButton id={r.forecast_id} token={token} onDeleted={onDeleted} compact />
          <ChevronRight className="size-4 text-faint" aria-hidden />
        </div>
      </td>
    </tr>
  );
}

function EmptyHistory() {
  return (
    <Panel className="flex flex-col items-center py-16 text-center">
      <span className="grid size-11 place-items-center rounded-full bg-brand-soft text-brand-ink"><HistoryIcon className="size-5" aria-hidden /></span>
      <h2 className="mt-4 text-base font-semibold">No saved estimates yet</h2>
      <p className="mt-1 max-w-sm text-sm text-muted-foreground">Open My risk to calculate your first estimate. It will be saved here so you can look back at it.</p>
      <Link href="/risk" className="mt-5 flex h-9 items-center rounded-[7px] bg-brand px-4 text-sm font-medium text-on-brand hover:brightness-110">Check my risk</Link>
    </Panel>
  );
}

/** Delete with an inline confirmation step. */
function DeleteButton({ id, token, onDeleted, compact = false }: { id: string; token: string; onDeleted: () => void; compact?: boolean }) {
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string>();

  async function remove() {
    setBusy(true);
    setError(undefined);
    try {
      await meApi(token).deleteRun(id);
      onDeleted();
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
    }
  }

  if (!confirming) {
    return compact ? (
      <button onClick={() => setConfirming(true)} aria-label="Delete this estimate" title="Delete"
        className="grid size-8 place-items-center rounded-[7px] text-faint hover:bg-card hover:text-destructive">
        <Trash2 className="size-4" aria-hidden />
      </button>
    ) : (
      <SecondaryButton onClick={() => setConfirming(true)} className="h-9"><Trash2 className="size-4" aria-hidden />Delete</SecondaryButton>
    );
  }
  return (
    <span className="flex items-center gap-2 whitespace-nowrap">
      <span className="text-[13px] text-muted-foreground">{error ? "Couldn't delete." : "Delete this estimate?"}</span>
      <button onClick={remove} disabled={busy}
        className="inline-flex h-8 items-center gap-1.5 rounded-[7px] bg-destructive px-3 text-[13px] font-medium text-white hover:brightness-110 disabled:opacity-60">
        {busy && <Loader2 className="size-3.5 animate-spin" aria-hidden />}Delete
      </button>
      <button onClick={() => setConfirming(false)} className="h-8 rounded-[7px] px-2 text-[13px] font-medium text-muted-foreground hover:bg-muted">Cancel</button>
    </span>
  );
}

// ------------------------------------------------------------------ detail

export function HistoryDetailView({ session, id }: { session: Session; id: string }) {
  const router = useRouter();
  const run = useAsync((signal) => meApi(session.access_token).historyRun(id, signal), [session.user.id, id]);
  const notFound = run.error && "status" in run.error && [404, 422].includes((run.error as { status: number }).status);

  return (
    <>
      <div className="flex flex-wrap items-end gap-4 pt-6 pb-4">
        <div>
          <Link href="/history" className="flex items-center gap-1 text-[13px] font-medium text-muted-foreground hover:text-foreground"><ArrowLeft className="size-3.5" aria-hidden />History</Link>
          <h1 className="mt-1.5 text-[26px] font-semibold tracking-tight">
            {run.data ? `${run.data.city}, ${run.data.horizon}-day estimate` : "Saved estimate"}
          </h1>
          {run.data && <p className="mt-1 text-sm text-muted-foreground">Calculated {fmtWhen(run.data.predicted_at)} · {forecastSpan(run.data)}</p>}
        </div>
        {run.data && (
          <div className="ml-auto flex items-center gap-2.5">
            <DeleteButton id={id} token={session.access_token} onDeleted={() => router.replace("/history")} />
            <Link href="/risk" className="flex h-9 items-center rounded-[7px] bg-brand px-4 text-sm font-medium text-on-brand hover:brightness-110">New estimate</Link>
          </div>
        )}
      </div>
      {notFound ? (
        <Panel className="py-12 text-center">
          <h2 className="text-base font-semibold">This estimate isn&apos;t available</h2>
          <p className="mt-1 text-sm text-muted-foreground">It may have been deleted.</p>
          <PrimaryButton className="mt-5" onClick={() => router.push("/history")}>Back to history</PrimaryButton>
        </Panel>
      ) : run.error ? <ErrorState message={run.error.message} onRetry={run.retry} />
        : !run.data ? <Skeleton className="h-[520px]" />
        : <RiskResult data={fromHistory(run.data)} />}
    </>
  );
}
