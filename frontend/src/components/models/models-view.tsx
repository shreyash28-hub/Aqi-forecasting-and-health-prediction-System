"use client";

import { useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Check } from "lucide-react";
import { ErrorState, Panel, PanelTitle } from "@/components/common";
import { Skeleton } from "@/components/ui/skeleton";
import { useAsync } from "@/hooks/use-async";
import { api, type ForecastLeaderboard, type ForecastRankingRow, type HealthRankingRow } from "@/lib/api";
import { CITIES } from "@/lib/content";
import { RISK_COLOR, RISK_LEVELS } from "@/lib/aqi";
import { fmtDate } from "@/lib/format";
import { cn } from "@/lib/utils";

type Tab = "AQI" | "PM2.5" | "NO2" | "health";
const TABS: { value: Tab; label: string }[] = [
  { value: "AQI", label: "AQI forecast" }, { value: "PM2.5", label: "PM2.5 forecast" },
  { value: "NO2", label: "NO2 forecast" }, { value: "health", label: "Health risk" },
];

const FAMILY: Record<string, string> = {
  ARIMA: "Classical", SARIMA: "Classical", "Holt-Winters": "Classical", Prophet: "Additive trend + seasonality",
  XGBoost: "Machine learning", LSTM: "Deep learning", MLP: "Deep learning", "Random Forest": "Machine learning",
};
const UNIT: Record<string, string> = { AQI: "", "PM2.5": " µg/m³", NO2: " µg/m³" };

const f = (v: number | null | undefined, d = 1) => (v == null ? "–" : v.toFixed(d));
const pct = (v: number | null | undefined) => (v == null ? "–" : `${Math.round(v * 100)}%`);

export function ModelsView() {
  const params = useSearchParams(), router = useRouter(), path = usePathname();
  const tab = TABS.find((t) => t.value === params.get("tab"))?.value ?? "AQI";
  const setTab = (t: Tab) => router.replace(t === "AQI" ? path : `${path}?tab=${encodeURIComponent(t)}`, { scroll: false });
  return (
    <>
      <div className="flex flex-wrap items-end gap-4 pt-6 pb-4">
        <div>
          <h1 className="text-[26px] font-semibold tracking-tight">Models</h1>
          <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
            Every model is compared on the same held-out data, and the best one is selected automatically. Forecasting models must also beat a simple naive forecast.
          </p>
        </div>
      </div>
      <div role="tablist" aria-label="Model groups" className="mb-5 flex gap-1 border-b">
        {TABS.map((t) => (
          <button key={t.value} role="tab" aria-selected={tab === t.value} onClick={() => setTab(t.value)}
            className={cn("-mb-px border-b-2 px-3.5 py-2.5 text-sm font-medium transition-colors",
              tab === t.value ? "border-brand text-foreground" : "border-transparent text-muted-foreground hover:text-foreground")}>
            {t.label}
          </button>
        ))}
      </div>
      {tab === "health" ? <HealthBoard /> : <ForecastBoard key={tab} target={tab} />}
    </>
  );
}

// ------------------------------------------------------------------ forecasting

function ForecastBoard({ target }: { target: "AQI" | "PM2.5" | "NO2" }) {
  const board = useAsync((signal) => api.forecastLeaderboard(target, signal), [target]);
  const [city, setCity] = useState<string>("Delhi");
  if (board.error) return <ErrorState message={board.error.message} onRetry={board.retry} />;
  if (!board.data) return <BoardSkeleton />;
  const b = board.data, c = b.cities[city];

  return (
    <div className="grid grid-cols-12 gap-4">
      <div className="col-span-12 flex flex-wrap gap-2" role="tablist" aria-label="Cities">
        {CITIES.filter((x) => b.cities[x]).map((x) => (
          <button key={x} role="tab" aria-selected={x === city} onClick={() => setCity(x)}
            className={cn("flex items-center gap-2 rounded-[8px] border bg-card px-3.5 py-2 text-sm transition-colors hover:bg-muted",
              x === city && "border-brand shadow-[inset_0_0_0_1px_var(--brand)]")}>
            <b className="font-medium">{x}</b>
            <span className="text-[12.5px] text-muted-foreground">{b.cities[x].deployed_model}</span>
          </button>
        ))}
      </div>
      <SummaryTiles board={b} city={city} target={target} />
      <Panel className="col-span-12 lg:col-span-8">
        <PanelTitle sub={`${city} · mean over ${b.n_windows} test windows of ${b.horizon_days} days`}>Ranking</PanelTitle>
        <RankingTable rows={c.ranking} deployed={c.deployed_model} unit={UNIT[target]} />
      </Panel>
      <Panel delay={0.05} className="col-span-12 flex flex-col lg:col-span-4">
        <PanelTitle sub="lower is better">Mean RMSE</PanelTitle>
        <RmseBars rows={c.ranking} deployed={c.deployed_model} />
        <div className="mt-auto border-t pt-4">
          <h3 className="text-[13px] font-medium">Test windows</h3>
          <ul className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-[12.5px] text-muted-foreground">
            {c.windows.map((w) => <li key={w.window} className="num">{fmtDate(w.test_start)} – {fmtDate(w.test_end).slice(0, -5)}</li>)}
          </ul>
        </div>
      </Panel>
    </div>
  );
}

function SummaryTiles({ board, city, target }: { board: ForecastLeaderboard; city: string; target: string }) {
  const c = board.cities[city];
  const dep = c.ranking.find((r) => r.model === c.deployed_model)!;
  const base = c.ranking.find((r) => r.model === c.best_baseline)!;
  const gain = c.best_model_beats_baseline ? (1 - dep.mean_rmse / base.mean_rmse) * 100 : 0;
  const tiles = [
    { label: "Deployed model", value: c.deployed_model, sub: c.best_model_beats_baseline ? FAMILY[c.deployed_model] ?? "Model" : "No model beat the baseline, so the baseline is used" },
    { label: "Mean RMSE", value: f(dep.mean_rmse), sub: `± ${f(dep.std_rmse)} across windows${UNIT[target] ? ` ·${UNIT[target]}` : ""}`, mono: true },
    { label: "Better than naive forecast", value: c.best_model_beats_baseline ? `${gain.toFixed(0)}%` : "–", sub: `vs ${c.best_baseline} (RMSE ${f(base.mean_rmse)})`, mono: true },
    { label: "Mean absolute % error", value: `${f(dep.mean_mape)}%`, sub: `MAE ${f(dep.mean_mae)}${UNIT[target]}`, mono: true },
  ];
  return (
    <>
      {tiles.map((t, i) => (
        <Panel key={t.label} delay={i * 0.03} className="col-span-6 lg:col-span-3">
          <div className="text-[13px] text-muted-foreground">{t.label}</div>
          <div className={cn("mt-2 text-[26px] leading-tight font-medium tracking-tight", t.mono && "num")}>{t.value}</div>
          <div className="mt-1 text-[12.5px] text-faint">{t.sub}</div>
        </Panel>
      ))}
    </>
  );
}

function RankingTable({ rows, deployed, unit }: { rows: ForecastRankingRow[]; deployed: string; unit: string }) {
  return (
    <div className="mt-3 overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="text-left text-xs text-faint [&>th]:border-b [&>th]:px-3 [&>th]:py-2 [&>th]:font-medium">
            <th className="w-8">#</th><th>Model</th><th>Type</th><th className="text-right">RMSE{unit}</th><th className="text-right">MAE</th>
            <th className="text-right">MAPE</th><th className="text-right">Mean rank</th><th className="text-right">Won windows</th><th className="text-right">Beat naive</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => {
            const dep = r.model === deployed, base = r.kind === "baseline";
            return (
              <tr key={r.model} className={cn("[&>td]:border-b [&>td]:px-3 [&>td]:py-2.5 last:[&>td]:border-b-0", dep && "bg-brand-soft/60", base && !dep && "text-muted-foreground")}>
                <td className="num text-faint">{i + 1}</td>
                <td className="font-medium">
                  <span className="flex items-center gap-2">{r.model}
                    {dep && <span className="inline-flex items-center gap-1 rounded-[5px] bg-brand px-1.5 py-px text-[11px] font-medium text-on-brand"><Check className="size-3" aria-hidden />Deployed</span>}
                  </span>
                </td>
                <td className="text-muted-foreground">{base ? "Baseline" : FAMILY[r.model] ?? "Model"}</td>
                <td className="num text-right">{f(r.mean_rmse)}</td>
                <td className="num text-right">{f(r.mean_mae)}</td>
                <td className="num text-right">{f(r.mean_mape)}%</td>
                <td className="num text-right">{f(r.mean_rank)}</td>
                <td className="num text-right">{Math.round(r.win_rate * r.n_windows)}/{r.n_windows}</td>
                <td className="num text-right">{base ? "–" : pct(r.beat_baseline_rate)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function RmseBars({ rows, deployed }: { rows: ForecastRankingRow[]; deployed: string }) {
  const max = Math.max(...rows.map((r) => r.mean_rmse));
  return (
    <ul className="mt-4 flex flex-col gap-2.5 pb-4">
      {rows.map((r) => {
        const dep = r.model === deployed, base = r.kind === "baseline";
        return (
          <li key={r.model} className="grid grid-cols-[130px_1fr_44px] items-center gap-3 text-[13px]" title={`${r.model}: mean RMSE ${f(r.mean_rmse)}`}>
            <span className={cn("truncate", dep ? "font-medium" : "text-muted-foreground")}>{r.model}</span>
            <span className="h-3 overflow-hidden rounded-r-[4px]">
              <i className={cn("block h-full rounded-r-[4px]", dep ? "bg-brand" : base ? "bg-border-strong" : "bg-faint/50")} style={{ width: `${(r.mean_rmse / max) * 100}%` }} />
            </span>
            <span className="num text-right">{f(r.mean_rmse)}</span>
          </li>
        );
      })}
    </ul>
  );
}

// ------------------------------------------------------------------ health

const FEATURE_SETS: { value: string; label: string; hint: string }[] = [
  { value: "aqi_pm25_no2", label: "Primary", hint: "Profile + AQI, PM2.5, NO2" },
  { value: "aqi_only", label: "Fallback", hint: "Profile + AQI only" },
];

function HealthBoard() {
  const board = useAsync((signal) => api.healthLeaderboard(signal), []);
  const [fs, setFs] = useState("aqi_pm25_no2");
  if (board.error) return <ErrorState message={board.error.message} onRetry={board.retry} />;
  if (!board.data) return <BoardSkeleton />;
  const b = board.data;
  const cls = b.tasks.classification.ranking.filter((r) => r.feature_set === fs);
  const reg = b.tasks.regression.ranking.filter((r) => r.feature_set === fs);
  const selCls = cls.find((r) => r.selected) ?? cls.find((r) => r.model === b.tasks.classification.selected[fs]);

  return (
    <div className="grid grid-cols-12 gap-4">
      <div className="col-span-12 flex flex-wrap items-center gap-3">
        <div role="radiogroup" aria-label="Feature set" className="inline-flex overflow-hidden rounded-[7px] border border-border-strong bg-card">
          {FEATURE_SETS.map((s) => (
            <button key={s.value} role="radio" aria-checked={fs === s.value} onClick={() => setFs(s.value)}
              className={cn("px-3.5 py-1.5 text-[13px] font-medium", fs === s.value ? "bg-muted text-foreground" : "text-muted-foreground hover:text-foreground")}>
              {s.label}
            </button>
          ))}
        </div>
        <span className="text-[13px] text-muted-foreground">{FEATURE_SETS.find((s) => s.value === fs)!.hint}. The fallback is used when PM2.5 or NO2 forecasts are unavailable.</span>
      </div>

      <Panel className="col-span-12 lg:col-span-6">
        <PanelTitle sub="risk level · selected by weighted F1">Classification</PanelTitle>
        <HealthTable rows={cls} cols={[
          ["Weighted F1 (CV)", (r) => f(r.cv.f1_weighted_mean, 3)], ["Weighted F1", (r) => f(r.test.f1_weighted, 3)],
          ["Accuracy", (r) => f(r.test.accuracy, 3)], ["Precision", (r) => f(r.test.precision_weighted, 3)], ["Recall", (r) => f(r.test.recall_weighted, 3)],
        ]} />
      </Panel>
      <Panel delay={0.05} className="col-span-12 lg:col-span-6">
        <PanelTitle sub="risk score · selected by RMSE">Regression</PanelTitle>
        <HealthTable rows={reg} cols={[
          ["RMSE (CV)", (r) => f(r.cv.rmse_mean, 3)], ["RMSE", (r) => f(r.test.rmse, 3)], ["MAE", (r) => f(r.test.mae, 3)],
          ["R²", (r) => f(r.test.r2, 3)], ["Level from score", (r) => pct(r.test.level_accuracy_from_score)],
        ]} />
      </Panel>

      {selCls && (
        <Panel delay={0.1} className="col-span-12 flex flex-col lg:col-span-6">
          <PanelTitle sub={`${selCls.model}, test set`}>Recall by risk level</PanelTitle>
          <p className="mt-1 text-[13px] text-muted-foreground">Share of people at each true level that the model placed correctly. The classes are imbalanced, so each is checked separately.</p>
          <ul className="mt-4 flex flex-1 flex-col justify-around gap-3">
            {RISK_LEVELS.map((l) => {
              const v = selCls.test[`recall_${l.toLowerCase()}`] ?? 0;
              return (
                <li key={l} className="grid grid-cols-[90px_1fr_48px] items-center gap-3 text-[13px]">
                  <span className="flex items-center gap-2"><i className="size-2.5 rounded-[2px]" style={{ background: RISK_COLOR[l] }} />{l}</span>
                  <span className="h-3 overflow-hidden rounded-r-[4px] bg-muted"><i className="block h-full rounded-r-[4px]" style={{ width: `${v * 100}%`, background: RISK_COLOR[l] }} /></span>
                  <span className="num text-right">{pct(v)}</span>
                </li>
              );
            })}
          </ul>
        </Panel>
      )}
      <BoundaryPanel rule={b.boundary_rule[fs]} />
    </div>
  );
}

function HealthTable({ rows, cols }: { rows: HealthRankingRow[]; cols: [string, (r: HealthRankingRow) => string][] }) {
  return (
    <div className="mt-3 overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="text-left text-xs text-faint [&>th]:border-b [&>th]:px-3 [&>th]:py-2 [&>th]:font-medium">
            <th>Model</th>{cols.map(([h]) => <th key={h} className="text-right">{h}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.model} className={cn("[&>td]:border-b [&>td]:px-3 [&>td]:py-2.5 last:[&>td]:border-b-0", r.selected && "bg-brand-soft/60", r.kind === "baseline" && "text-muted-foreground")}>
              <td className="font-medium">
                <span className="flex items-center gap-2 whitespace-nowrap">{r.kind === "baseline" ? "Baseline (majority)" : r.model}
                  {r.selected && <span className="inline-flex items-center gap-1 rounded-[5px] bg-brand px-1.5 py-px text-[11px] font-medium text-on-brand"><Check className="size-3" aria-hidden />Selected</span>}
                </span>
              </td>
              {cols.map(([h, get]) => <td key={h} className="num text-right">{get(r)}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function BoundaryPanel({ rule }: { rule?: Record<string, number> }) {
  if (!rule) return null;
  const rows: [string, string][] = [
    ["Days on a level boundary", pct(rule.borderline_share)],
    ["Accuracy when both models agree", pct(rule.accuracy_when_models_agree)],
    ["True level inside the shown range (borderline days)", pct(rule.true_level_within_range_when_borderline)],
    ["High/Severe caught, level only", pct(rule.elevated_recall_classifier_only)],
    ["High/Severe caught, with boundary rule", pct(rule.elevated_recall_alert_level)],
    ["False High/Severe alerts, with boundary rule", pct(rule.false_elevated_rate_alert_level)],
  ];
  return (
    <Panel delay={0.12} className="col-span-12 lg:col-span-6">
      <PanelTitle sub="test set">Borderline days</PanelTitle>
      <p className="mt-1 text-[13px] text-muted-foreground">
        The risk level comes from the classifier. When the risk score points to a different level, the day is shown as a range and precautions follow the higher level.
      </p>
      <dl className="mt-3 grid grid-cols-[1fr_auto] gap-x-4 text-sm">
        {rows.map(([k, v]) => (
          <div key={k} className="contents [&>*]:border-b [&>*]:py-2 [&:last-child>*]:border-b-0">
            <dt className="text-muted-foreground">{k}</dt><dd className="num text-right font-medium">{v}</dd>
          </div>
        ))}
      </dl>
    </Panel>
  );
}

function BoardSkeleton() {
  return (
    <div className="grid grid-cols-12 gap-4" aria-busy="true">
      <Skeleton className="col-span-12 h-10" />
      {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="col-span-3 h-28" />)}
      <Skeleton className="col-span-8 h-[420px]" />
      <Skeleton className="col-span-4 h-[420px]" />
    </div>
  );
}

