"""Train, evaluate, select and save the health-risk models.

Tasks:
* classification: HealthRiskLevel (Low / Moderate / High / Severe), best by weighted F1
* regression:     HealthRiskScore, best by RMSE

Models: Random Forest, XGBoost, MLP (sklearn), each against a dummy baseline
(most-frequent class / mean score).

Protocol:
1. Stratified 80/20 split by risk level (same split for both tasks).
2. 5-fold stratified cross-validation on the 80% selects the best model per task and
   feature set (mean CV weighted F1 / RMSE). Classifiers use balanced sample weights.
3. Every model is refitted on the 80% and scored once on the untouched 20% test set.
4. Feature sets (profile + air): ``aqi_only``, ``aqi_pm25_no2`` and ``full`` (all five
   pollutants). ``aqi_pm25_no2`` is deployed as the primary model (PM2.5 and NO2 are
   forecast for every city); ``aqi_only`` is deployed as the fallback. ``full`` is
   reported for comparison only.
5. The boundary rule that reconciles classifier and regressor (see
   ``src.health.store``) is evaluated on the test split.
6. Each deployed winner is refitted on all rows, saved to ``models/health/``, reloaded
   and checked against the in-memory model.

Usage::

    python -m src.health.train

Outputs: reports/health/{metrics.csv, leaderboard.json, summary.md} and
reports/figures/health_confusion_matrix.png.
"""
from __future__ import annotations

import json
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.dummy import DummyClassifier, DummyRegressor  # noqa: E402
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score, mean_absolute_error,  # noqa: E402
                             mean_squared_error, precision_score, r2_score, recall_score)
from sklearn.model_selection import StratifiedKFold, train_test_split  # noqa: E402

from src.data_loader import PROJECT_ROOT  # noqa: E402
from src.health.data import (CLS_TARGET, DEPLOY_FEATURE_SETS, FEATURE_SETS, PRIMARY_FEATURE_SET,  # noqa: E402
                             REG_TARGET, RISK_LEVELS, RISK_SCORE_CUTS, load_health_dataset,
                             score_to_level)
from src.health.models import MODEL_NAMES, SEED, balanced_weights, make_pipeline  # noqa: E402
from src.health.store import (HEALTH_MODELS_DIR, load_health_predictor, reconcile,  # noqa: E402
                              save_health_model, write_registry)

OUT_DIR = PROJECT_ROOT / "reports" / "health"
FIG_DIR = PROJECT_ROOT / "reports" / "figures"
TEST_SIZE = 0.2
N_FOLDS = 5
TASKS = {"classification": ("f1_weighted", "max"), "regression": ("rmse", "min")}
ELEVATED = {RISK_LEVELS.index("High"), RISK_LEVELS.index("Severe")}  # triggers hospital map etc.


# --------------------------------------------------------------------------- metrics

def cls_metrics(y, yhat) -> dict:
    recalls = recall_score(y, yhat, labels=range(len(RISK_LEVELS)), average=None, zero_division=0)
    return {"accuracy": accuracy_score(y, yhat),
            "precision_weighted": precision_score(y, yhat, average="weighted", zero_division=0),
            "recall_weighted": recall_score(y, yhat, average="weighted", zero_division=0),
            "f1_weighted": f1_score(y, yhat, average="weighted", zero_division=0),
            **{f"recall_{lvl.lower()}": float(r) for lvl, r in zip(RISK_LEVELS, recalls)}}


def reg_metrics(y, yhat) -> dict:
    mse = mean_squared_error(y, yhat)
    return {"mse": mse, "rmse": float(np.sqrt(mse)), "mae": mean_absolute_error(y, yhat),
            "r2": r2_score(y, yhat),
            # How well the score, cut at the level boundaries, recovers the level.
            "level_accuracy_from_score": accuracy_score(score_to_level(y), score_to_level(yhat))}


# --------------------------------------------------------------------------- fitting

def build(task: str, name: str, feature_set: str):
    if name == "Baseline":
        from sklearn.pipeline import Pipeline
        from src.health.models import make_preprocessor
        est = DummyClassifier(strategy="most_frequent") if task == "classification" else DummyRegressor()
        return Pipeline([("prep", make_preprocessor(**FEATURE_SETS[feature_set])), ("est", est)])
    return make_pipeline(task, name, **FEATURE_SETS[feature_set])


def fit(task, name, feature_set, X, y):
    pipe = build(task, name, feature_set)
    params = {}
    if task == "classification" and name != "Baseline":
        params["est__sample_weight"] = balanced_weights(y)
    return pipe.fit(X, y, **params)


def predict(task, pipe, X):
    return pipe.predict(X).astype(int) if task == "classification" else np.clip(pipe.predict(X), 0, None)


def evaluate(task, name, feature_set, X_tr, y_tr, X_te, y_te, strata_tr) -> tuple[dict, object]:
    metric_fn = cls_metrics if task == "classification" else reg_metrics
    t0 = time.perf_counter()
    folds = []
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
    for tr_idx, va_idx in skf.split(X_tr, strata_tr):
        pipe = fit(task, name, feature_set, X_tr.iloc[tr_idx], y_tr[tr_idx])
        folds.append(metric_fn(y_tr[va_idx], predict(task, pipe, X_tr.iloc[va_idx])))
    cv = pd.DataFrame(folds)
    pipe = fit(task, name, feature_set, X_tr, y_tr)
    test = metric_fn(y_te, predict(task, pipe, X_te))
    row = {"task": task, "feature_set": feature_set, "model": name,
           "kind": "baseline" if name == "Baseline" else "model",
           **{f"cv_{k}_mean": v for k, v in cv.mean().items()},
           **{f"cv_{k}_std": v for k, v in cv.std().items()},
           **{f"test_{k}": v for k, v in test.items()},
           "runtime_s": round(time.perf_counter() - t0, 1)}
    return row, pipe


# --------------------------------------------------------------------------- reporting

def plot_confusion(y_true, y_pred, title: str):
    cm = confusion_matrix(y_true, y_pred, labels=range(len(RISK_LEVELS)))
    share = cm / cm.sum(axis=1, keepdims=True)
    fig, ax = plt.subplots(figsize=(5.2, 4.4))
    ax.imshow(share, cmap="Blues", vmin=0, vmax=1)
    for i in range(len(RISK_LEVELS)):
        for j in range(len(RISK_LEVELS)):
            ax.text(j, i, f"{cm[i, j]}\n{share[i, j]:.0%}", ha="center", va="center", fontsize=8,
                    color="white" if share[i, j] > 0.6 else "black")
    ax.set_xticks(range(len(RISK_LEVELS)), RISK_LEVELS)
    ax.set_yticks(range(len(RISK_LEVELS)), RISK_LEVELS)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(title, fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "health_confusion_matrix.png", dpi=120)
    plt.close(fig)
    return cm


def _fmt(v, pct=False):
    return "-" if pd.isna(v) else (f"{v:.1%}" if pct else f"{v:.3f}")


def boundary_rule_report(y_true: np.ndarray, clf_idx: np.ndarray, score: np.ndarray) -> dict:
    """How the reconciliation rule behaves on held-out data."""
    rec = reconcile(clf_idx, score)
    border = rec["borderline"].to_numpy()
    alert_idx = np.array([RISK_LEVELS.index(v) for v in rec["alert_level"]])
    lo = np.minimum(clf_idx, alert_idx)
    true_elev = np.isin(y_true, list(ELEVATED))
    clf_elev, alert_elev = np.isin(clf_idx, list(ELEVATED)), np.isin(alert_idx, list(ELEVATED))
    return {
        "borderline_share": float(border.mean()),
        "accuracy_when_models_agree": float((clf_idx == y_true)[~border].mean()),
        "accuracy_when_borderline": float((clf_idx == y_true)[border].mean()) if border.any() else None,
        "true_level_within_range_when_borderline":
            float(((y_true >= lo) & (y_true <= alert_idx))[border].mean()) if border.any() else None,
        "elevated_recall_classifier_only": float(clf_elev[true_elev].mean()),
        "elevated_recall_alert_level": float(alert_elev[true_elev].mean()),
        "false_elevated_rate_classifier_only": float(clf_elev[~true_elev].mean()),
        "false_elevated_rate_alert_level": float(alert_elev[~true_elev].mean()),
    }


def write_summary(metrics: pd.DataFrame, board: dict):
    L = ["# Health-risk models: evaluation summary", "",
         f"Generated {board['generated_at']}. {board['n_rows']} rows; stratified "
         f"{int((1 - TEST_SIZE) * 100)}/{int(TEST_SIZE * 100)} train/test split; model selection by "
         f"{N_FOLDS}-fold stratified CV on the training split; test metrics from one fit on the "
         "training split. Classifiers use balanced sample weights.", "",
         f"Deployed: `{PRIMARY_FEATURE_SET}` (profile + AQI, PM2.5, NO2) as the primary model and "
         "`aqi_only` as the fallback for cities without pollutant forecasts. `full` (all five "
         "pollutants) is shown for comparison.", "",
         "Estimated risk for decision support only, not a medical diagnosis.", ""]
    for task, (metric, _) in TASKS.items():
        t = board["tasks"][task]
        sel = ", ".join(f"`{fs}` → **{m}**" for fs, m in t["selected"].items())
        L += [f"## {task.capitalize()}: {t['target']}", "",
              f"Selected by mean CV {metric.replace('_', ' ')}: {sel}.", ""]
        m = metrics[metrics["task"] == task]
        if task == "classification":
            cols = [("cv_f1_weighted_mean", "CV weighted F1"), ("cv_f1_weighted_std", "± std"),
                    ("test_f1_weighted", "Test F1 (w)"), ("test_accuracy", "Test acc."),
                    ("test_precision_weighted", "Test prec. (w)"), ("test_recall_weighted", "Test rec. (w)")] + \
                   [(f"test_recall_{lvl.lower()}", f"Recall {lvl}") for lvl in RISK_LEVELS]
        else:
            cols = [("cv_rmse_mean", "CV RMSE"), ("cv_rmse_std", "± std"), ("test_rmse", "Test RMSE"),
                    ("test_mse", "Test MSE"), ("test_mae", "Test MAE"), ("test_r2", "Test R²"),
                    ("test_level_accuracy_from_score", "Level acc. from score")]
        for fs in FEATURE_SETS:
            sub = m[m["feature_set"] == fs]
            tag = {PRIMARY_FEATURE_SET: " (deployed: primary)", "aqi_only": " (deployed: fallback)"}.get(fs, "")
            L += [f"### Feature set `{fs}`{tag}", "",
                  "| Model | " + " | ".join(c[1] for c in cols) + " |",
                  "|---|" + "---|" * len(cols)]
            for _, r in sub.iterrows():
                name = f"**{r['model']}**" if t["selected"].get(fs) == r["model"] else r["model"]
                L.append(f"| {name} | " + " | ".join(_fmt(r[c]) for c, _ in cols) + " |")
            L.append("")

    L += ["## Boundary rule (test split)", "",
          f"The classifier gives the headline level. When the predicted score (cut at {RISK_SCORE_CUTS}) "
          "implies a different level, the day is flagged *borderline*, shown as a range "
          "(e.g. Moderate-High), and the higher level is used for alerts (hospital map, precautions).", "",
          "| | " + " | ".join(f"`{fs}`" for fs in board["boundary_rule"]) + " |",
          "|---|" + "---|" * len(board["boundary_rule"])]
    rows = [("borderline_share", "Days flagged borderline"),
            ("accuracy_when_models_agree", "Level accuracy when models agree"),
            ("accuracy_when_borderline", "Level accuracy when borderline"),
            ("true_level_within_range_when_borderline", "True level inside the shown range (borderline days)"),
            ("elevated_recall_classifier_only", "High/Severe caught: classifier alone"),
            ("elevated_recall_alert_level", "High/Severe caught: alert level"),
            ("false_elevated_rate_classifier_only", "Low/Moderate alerted as High+: classifier alone"),
            ("false_elevated_rate_alert_level", "Low/Moderate alerted as High+: alert level")]
    for key, label in rows:
        L.append(f"| {label} | " + " | ".join(_fmt(b[key], pct=True) for b in board["boundary_rule"].values()) + " |")
    L += ["", f"## Confusion matrix (selected `{PRIMARY_FEATURE_SET}` classifier, test split)", "",
          "![confusion matrix](../figures/health_confusion_matrix.png)", ""]
    (OUT_DIR / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- main

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    df = load_health_dataset()
    y_cls = df[CLS_TARGET].map({lvl: i for i, lvl in enumerate(RISK_LEVELS)}).to_numpy()
    y_reg = df[REG_TARGET].to_numpy(dtype=float)
    idx_tr, idx_te = train_test_split(np.arange(len(df)), test_size=TEST_SIZE, stratify=y_cls,
                                      random_state=SEED)
    X_tr, X_te = df.iloc[idx_tr].reset_index(drop=True), df.iloc[idx_te].reset_index(drop=True)
    print(f"{len(df)} rows -> train {len(idx_tr)}, test {len(idx_te)}")

    rows, fitted = [], {}
    for task in TASKS:
        y = y_cls if task == "classification" else y_reg
        for fs in FEATURE_SETS:
            for name in ["Baseline", *MODEL_NAMES]:
                row, pipe = evaluate(task, name, fs, X_tr, y[idx_tr], X_te, y[idx_te], y_cls[idx_tr])
                rows.append(row)
                fitted[(task, fs, name)] = pipe
                key = "f1_weighted" if task == "classification" else "rmse"
                print(f"  {task:<14} {fs:<12} {name:<13} CV {key}={row[f'cv_{key}_mean']:.4f} "
                      f"(±{row[f'cv_{key}_std']:.4f})  test={row[f'test_{key}']:.4f}  [{row['runtime_s']}s]")
    metrics = pd.DataFrame(rows)

    # Selection per task and deployed feature set, by mean CV metric.
    best = {}
    for task, (metric, direction) in TASKS.items():
        for fs in DEPLOY_FEATURE_SETS:
            cand = metrics[(metrics["task"] == task) & (metrics["feature_set"] == fs) & (metrics["kind"] == "model")]
            col = f"cv_{metric}_mean"
            best[(task, fs)] = cand.loc[cand[col].idxmax() if direction == "max" else cand[col].idxmin(), "model"]
    metrics["selected"] = [best.get((r.task, r.feature_set)) == r.model for r in metrics.itertuples()]

    # Boundary rule on the test split, per deployed feature set (train-split models).
    boundary = {}
    for fs in DEPLOY_FEATURE_SETS:
        clf_idx = fitted[("classification", fs, best[("classification", fs)])].predict(X_te).astype(int)
        score = np.clip(fitted[("regression", fs, best[("regression", fs)])].predict(X_te), 0, None)
        boundary[fs] = boundary_rule_report(y_cls[idx_te], clf_idx, score)
        if fs == PRIMARY_FEATURE_SET:
            cm = plot_confusion(y_cls[idx_te], clf_idx, f"{best[('classification', fs)]} ({fs}), test split")

    # Refit deployed winners on all rows, save, reload, verify.
    for task in TASKS:  # clear the pre-variant flat layout (models/health/<task>/*.joblib)
        for old in (HEALTH_MODELS_DIR / task).glob("*"):
            if old.is_file():
                old.unlink()
    metas = []
    for task, (metric, _) in TASKS.items():
        y = y_cls if task == "classification" else y_reg
        for fs in DEPLOY_FEATURE_SETS:
            name = best[(task, fs)]
            pipe = fit(task, name, fs, df, y)
            r = metrics[(metrics["task"] == task) & (metrics["feature_set"] == fs) & metrics["selected"]].iloc[0]
            meta = save_health_model(task, fs, name, pipe, {
                "target": CLS_TARGET if task == "classification" else REG_TARGET,
                "features": FEATURE_SETS[fs],
                **({"classes": RISK_LEVELS} if task == "classification" else {}),
                "selection": f"best mean {N_FOLDS}-fold CV {metric} among {MODEL_NAMES} on {fs}",
                "cv": {k[3:]: float(v) for k, v in r.items() if str(k).startswith("cv_")},
                "test": {k[5:]: float(v) for k, v in r.items() if str(k).startswith("test_")},
                "n_train_final": len(df),
                "evaluation_split": {"test_size": TEST_SIZE, "stratified_by": CLS_TARGET, "seed": SEED},
            })
            metas.append(meta)
            fitted[(task, fs, "final")] = pipe
    write_registry(metas, {"boundary_rule_test": boundary})

    predictor = load_health_predictor()
    for (task, fs), loaded in predictor.models.items():
        mem = fitted[(task, fs, "final")]
        Z = loaded.transform(X_te)
        same = (np.allclose(loaded.est.predict_proba(Z), mem.predict_proba(X_te), atol=1e-6)
                if task == "classification" else np.allclose(loaded.est.predict(Z), mem.predict(X_te), atol=1e-6))
        assert same, f"reloaded {task}/{fs} model does not reproduce the trained model"
    print("Reload check passed: all saved models reproduce the in-memory models.")

    board = {
        "generated_at": pd.Timestamp.now(tz="UTC").isoformat(timespec="seconds"),
        "n_rows": len(df), "n_train": len(idx_tr), "n_test": len(idx_te), "cv_folds": N_FOLDS,
        "primary_feature_set": PRIMARY_FEATURE_SET, "deploy_feature_sets": DEPLOY_FEATURE_SETS,
        "risk_score_cuts": RISK_SCORE_CUTS, "boundary_rule": boundary,
        "confusion_matrix_test_primary": cm.tolist(),
        "tasks": {task: {"target": CLS_TARGET if task == "classification" else REG_TARGET,
                         "selection_metric": metric,
                         "selected": {fs: best[(task, fs)] for fs in DEPLOY_FEATURE_SETS},
                         "ranking": json.loads(metrics[metrics["task"] == task].to_json(orient="records"))}
                  for task, (metric, _) in TASKS.items()},
    }
    metrics.to_csv(OUT_DIR / "metrics.csv", index=False)
    (OUT_DIR / "leaderboard.json").write_text(json.dumps(board, indent=2), encoding="utf-8")
    write_summary(metrics, board)
    for fs in DEPLOY_FEATURE_SETS:
        b = boundary[fs]
        print(f"{fs:<12} clf={best[('classification', fs)]}, reg={best[('regression', fs)]}; "
              f"borderline {b['borderline_share']:.1%}; High/Severe caught {b['elevated_recall_classifier_only']:.1%}"
              f" -> {b['elevated_recall_alert_level']:.1%} with alert level")
    print("Wrote reports/health/ and models/health/")


if __name__ == "__main__":
    main()
