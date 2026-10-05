// Typed client for the FastAPI backend (src/api in the repo root).
// Base URL comes from NEXT_PUBLIC_API_URL (see .env.example); defaults to local dev.

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

export type RiskLevel = "Low" | "Moderate" | "High" | "Severe";

export interface CityInfo {
  city: string;
  origin_date: string;
  targets: Record<string, string>; // forecast target -> deployed model name
}

export interface ForecastDay {
  date: string;
  aqi: number;
  aqi_category: string;
  pm25?: number | null;
  no2?: number | null;
}

export interface ForecastResponse {
  city: string;
  horizon: number;
  origin_date: string;
  models: Record<string, { model: string; config: string; selection?: string | null }>;
  days: ForecastDay[];
}

export interface Profile {
  age: number;
  gender: "F" | "M";
  condition: "No Condition" | "Asthma" | "COPD" | "HeartDisease" | "Diabetes" | "Hypertension";
  smoker: boolean;
  occupation: "Homemaker" | "Indoor Worker" | "Outdoor Worker" | "Retired" | "Student";
  area_type: "Commercial" | "Industrial" | "Residential";
  mask_usage: "No" | "Sometimes" | "Yes";
  outdoor_hours: number;
  bmi?: number | null;
  exercise_hours?: number | null;
  family_history?: boolean | null;
}

export interface RiskDay extends ForecastDay {
  risk_level: RiskLevel;
  confidence: number;
  probabilities: Record<RiskLevel, number>;
  risk_score: number;
  score_level: RiskLevel;
  borderline: boolean;
  risk_range: string;
  alert_level: RiskLevel;
}

export interface RiskResponse {
  city: string;
  horizon: number;
  origin_date: string;
  feature_set: string;
  health_models: Record<string, string>;
  imputed_fields: string[];
  warnings: string[];
  disclaimer: string;
  summary: {
    highest_alert_level: RiskLevel;
    show_hospitals: boolean;
    borderline_days: number;
    days_by_level: Record<RiskLevel, number>;
  };
  days: RiskDay[];
}

export interface ForecastRankingRow {
  model: string; kind: "model" | "baseline";
  mean_rmse: number; std_rmse: number; mean_mae: number; mean_mape: number;
  mean_rank: number; win_rate: number; beat_baseline_rate: number; n_windows: number;
}

export interface ForecastLeaderboard {
  target: string;
  selection: string;
  n_windows: number;
  horizon_days: number;
  generated_at: string;
  cities: Record<string, {
    deployed_model: string;
    best_model: string;
    best_model_beats_baseline: boolean;
    best_baseline: string;
    windows: Array<{ window: number; test_start: string; test_end: string }>;
    ranking: ForecastRankingRow[];
  }>;
}

export interface HealthRankingRow {
  model: string; kind: string; feature_set: string; selected: boolean;
  cv: Record<string, number | null>; test: Record<string, number | null>;
}

export interface HealthLeaderboard {
  generated_at: string;
  primary_feature_set: string;
  boundary_rule: Record<string, Record<string, number>>;
  tasks: Record<"classification" | "regression", {
    target: string;
    selection_metric: string;
    selected: Record<string, string>;
    ranking: HealthRankingRow[];
  }>;
}

export interface SavedProfile extends Profile {
  city?: string | null;
  updated_at?: string | null;
}

export interface SavedRiskResponse extends RiskResponse {
  forecast_id: string;
  predicted_at: string;
}

export interface HistoryItem {
  forecast_id: string;
  city: string;
  horizon: number;
  origin_date: string;
  predicted_at: string;
  summary: RiskResponse["summary"];
}

export interface HistoryDetail extends HistoryItem {
  models: { forecast: Record<string, string>; health: Record<string, string> };
  days: RiskDay[];
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit & { signal?: AbortSignal }): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    });
  } catch (e) {
    if ((e as Error).name === "AbortError") throw e;
    throw new ApiError(0, "Can't reach the forecast service.");
  }
  if (res.status === 204) return undefined as T;
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {}
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  cities: (signal?: AbortSignal) => request<CityInfo[]>("/api/cities", { signal }),
  forecast: (city: string, horizon: number, signal?: AbortSignal) =>
    request<ForecastResponse>(`/api/forecast/${encodeURIComponent(city)}?horizon=${horizon}`, { signal }),
  predictRisk: (body: { city: string; horizon: number; profile: Profile }, signal?: AbortSignal) =>
    request<RiskResponse>("/api/risk/predict", { method: "POST", body: JSON.stringify(body), signal }),
  forecastLeaderboard: (target: "AQI" | "PM2.5" | "NO2" = "AQI", signal?: AbortSignal) =>
    request<ForecastLeaderboard>(`/api/leaderboard/forecast?target=${encodeURIComponent(target)}`, { signal }),
  healthLeaderboard: (signal?: AbortSignal) => request<HealthLeaderboard>("/api/leaderboard/health", { signal }),
};

/** Signed-in endpoints: the Supabase access token lets the backend apply row-level security. */
export function meApi(token: string) {
  const auth = { Authorization: `Bearer ${token}` };
  return {
    /** Resolves to null when the user hasn't saved a profile yet. */
    profile: async (signal?: AbortSignal) => {
      try {
        return await request<SavedProfile>("/api/me/profile", { headers: auth, signal });
      } catch (e) {
        if (e instanceof ApiError && e.status === 404) return null;
        throw e;
      }
    },
    saveProfile: (profile: SavedProfile) => {
      const { updated_at: _ignored, ...body } = profile;
      void _ignored;
      return request<SavedProfile>("/api/me/profile", { method: "PUT", headers: auth, body: JSON.stringify(body) });
    },
    runRisk: (body: { city?: string; horizon: number }, signal?: AbortSignal) =>
      request<SavedRiskResponse>("/api/me/risk", { method: "POST", headers: auth, body: JSON.stringify(body), signal }),
    history: (limit = 50, signal?: AbortSignal) => request<HistoryItem[]>(`/api/me/history?limit=${limit}`, { headers: auth, signal }),
    historyRun: (id: string, signal?: AbortSignal) => request<HistoryDetail>(`/api/me/history/${encodeURIComponent(id)}`, { headers: auth, signal }),
    deleteRun: (id: string) => request<void>(`/api/me/history/${encodeURIComponent(id)}`, { method: "DELETE", headers: auth }),
  };
}
