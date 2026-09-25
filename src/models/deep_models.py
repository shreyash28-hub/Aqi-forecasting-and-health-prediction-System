"""Simple LSTM forecaster (PyTorch), direct multi-output.

Takes the last ``LOOKBACK`` days and predicts all ``horizon`` days in one shot,
which avoids the error compounding of recursive forecasting.

Reproducibility: every run is fully seeded (torch + numpy), so a given seed always
gives the same forecast. The evaluation runs the LSTM once per seed in
``LSTM_SEEDS`` and averages the metrics, so a single lucky/unlucky initialisation
can't decide the ranking.
"""
from __future__ import annotations

import copy

import numpy as np
import pandas as pd
import torch
from torch import nn

LOOKBACK = 60
HIDDEN = 64
EPOCHS = 150
PATIENCE = 15
BATCH = 64
LR = 1e-3
VAL_FRACTION = 0.1
SEED = 42
LSTM_SEEDS = (42, 43, 44)


class LSTMForecaster(nn.Module):
    def __init__(self, horizon: int, n_features: int = 3, hidden: int = HIDDEN):
        super().__init__()
        self.lstm = nn.LSTM(n_features, hidden, batch_first=True)
        self.head = nn.Sequential(nn.Dropout(0.2), nn.Linear(hidden, horizon))

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.head(out[:, -1, :])


def _inputs(y_scaled: np.ndarray, index: pd.DatetimeIndex) -> np.ndarray:
    """Per-step inputs: scaled value + day-of-year sin/cos."""
    doy = index.dayofyear.to_numpy()
    return np.column_stack([y_scaled,
                            np.sin(2 * np.pi * doy / 365.25),
                            np.cos(2 * np.pi * doy / 365.25)]).astype(np.float32)


def _windows(feats: np.ndarray, target: np.ndarray, horizon: int):
    X, Y = [], []
    for i in range(LOOKBACK, len(target) - horizon + 1):
        X.append(feats[i - LOOKBACK:i])
        Y.append(target[i:i + horizon])
    return np.stack(X), np.stack(Y).astype(np.float32)


def fit_lstm(train: pd.Series, horizon: int, seed: int = SEED):
    """Train one seeded LSTM. Returns ``(model, scaler, config)``; ``scaler`` = {"mu", "sigma"}."""
    torch.set_num_threads(1)  # float reductions (and so results) depend on thread count
    torch.manual_seed(seed)
    np.random.seed(seed)

    mu, sigma = float(train.mean()), float(train.std())
    y = ((train - mu) / sigma).to_numpy(dtype=np.float32)
    feats = _inputs(y, train.index)
    X, Y = _windows(feats, y, horizon)

    # Chronological validation split for early stopping.
    n_val = max(1, int(len(X) * VAL_FRACTION))
    X_tr, Y_tr = torch.from_numpy(X[:-n_val]), torch.from_numpy(Y[:-n_val])
    X_va, Y_va = torch.from_numpy(X[-n_val:]), torch.from_numpy(Y[-n_val:])

    model = LSTMForecaster(horizon, n_features=feats.shape[1])
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    loss_fn = nn.MSELoss()
    best_loss, best_state, bad, epochs_run = np.inf, None, 0, 0
    for epoch in range(EPOCHS):
        model.train()
        perm = torch.randperm(len(X_tr))
        for i in range(0, len(perm), BATCH):
            idx = perm[i:i + BATCH]
            opt.zero_grad()
            loss_fn(model(X_tr[idx]), Y_tr[idx]).backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            val = loss_fn(model(X_va), Y_va).item()
        epochs_run = epoch + 1
        if val < best_loss - 1e-5:
            best_loss, best_state, bad = val, copy.deepcopy(model.state_dict()), 0
        else:
            bad += 1
            if bad >= PATIENCE:
                break
    model.load_state_dict(best_state)
    model.eval()
    config = (f"LSTM(1x{HIDDEN}) lookback={LOOKBACK}, direct {horizon}-step, "
              f"{epochs_run} epochs (early stop), seed={seed}")
    return model, {"mu": mu, "sigma": sigma}, config


def predict_lstm(model: LSTMForecaster, scaler: dict, history: pd.Series) -> np.ndarray:
    """Forecast the model's full horizon from the last ``LOOKBACK`` days of ``history``."""
    history = history.iloc[-LOOKBACK:]
    y = ((history - scaler["mu"]) / scaler["sigma"]).to_numpy(dtype=np.float32)
    feats = _inputs(y, history.index)
    model.eval()
    with torch.no_grad():
        pred = model(torch.from_numpy(feats[None])).numpy()[0]
    return pred * scaler["sigma"] + scaler["mu"]


def lstm_forecast(train: pd.Series, horizon: int, seed: int = SEED):
    model, scaler, config = fit_lstm(train, horizon, seed)
    return predict_lstm(model, scaler, train), config
