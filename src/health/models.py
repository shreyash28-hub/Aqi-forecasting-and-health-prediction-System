"""Model builders for health-risk classification and regression.

Every model is ``preprocessor -> estimator``. The preprocessor one-hot encodes the
categorical profile fields (fixed category lists, so unseen values fail loudly) and
standardises numeric fields (needed by the MLP, harmless for trees). Keeping the two
steps separate lets each estimator be saved in its native format.
"""
from __future__ import annotations

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier, XGBRegressor

from src.health.data import CATEGORIES

SEED = 42
MODEL_NAMES = ["Random Forest", "XGBoost", "MLP"]


def make_preprocessor(numeric: list[str], categorical: list[str]) -> ColumnTransformer:
    return ColumnTransformer([
        ("num", StandardScaler(), numeric),
        ("cat", OneHotEncoder(categories=[CATEGORIES[c] for c in categorical],
                              handle_unknown="error", sparse_output=False), categorical),
    ])


def make_estimator(task: str, name: str):
    if task == "classification":
        if name == "Random Forest":
            # Class imbalance is handled with balanced sample weights for all three models
            # (see balanced_weights), so no class_weight here.
            return RandomForestClassifier(n_estimators=400, min_samples_leaf=2, n_jobs=-1, random_state=SEED)
        if name == "XGBoost":
            return XGBClassifier(n_estimators=500, learning_rate=0.05, max_depth=5, subsample=0.8,
                                 colsample_bytree=0.8, objective="multi:softprob",
                                 eval_metric="mlogloss", n_jobs=1, random_state=SEED)
        if name == "MLP":
            return MLPClassifier(hidden_layer_sizes=(64, 32), alpha=1e-3, learning_rate_init=1e-3,
                                 max_iter=500, early_stopping=True, n_iter_no_change=20,
                                 random_state=SEED)
    elif task == "regression":
        if name == "Random Forest":
            return RandomForestRegressor(n_estimators=400, min_samples_leaf=2, n_jobs=-1, random_state=SEED)
        if name == "XGBoost":
            return XGBRegressor(n_estimators=500, learning_rate=0.05, max_depth=5, subsample=0.8,
                                colsample_bytree=0.8, n_jobs=1, random_state=SEED)
        if name == "MLP":
            return MLPRegressor(hidden_layer_sizes=(64, 32), alpha=1e-3, learning_rate_init=1e-3,
                                max_iter=500, early_stopping=True, n_iter_no_change=20,
                                random_state=SEED)
    raise ValueError(f"Unknown task/model: {task}/{name}")


def make_pipeline(task: str, name: str, numeric: list[str], categorical: list[str]) -> Pipeline:
    return Pipeline([("prep", make_preprocessor(numeric, categorical)),
                     ("est", make_estimator(task, name))])


def balanced_weights(y_codes: np.ndarray) -> np.ndarray:
    """Per-sample weights inversely proportional to class frequency (imbalanced levels)."""
    return compute_sample_weight("balanced", y_codes)
