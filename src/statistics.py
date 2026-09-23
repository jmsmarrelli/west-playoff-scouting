"""Small, explicit estimators with game-level resampling."""

import numpy as np
import pandas as pd
from .common import SEED


def mean_ci(d, value, reps=2000):
    g = d.groupby("game_id")[value].agg(["sum", "count"]).to_numpy()
    rng = np.random.default_rng(SEED)
    chosen = rng.integers(0, len(g), (reps, len(g)))
    a = g[chosen].sum(axis=1)
    return (
        float(d[value].mean()),
        *np.quantile(a[:, 0] / a[:, 1], [0.025, 0.975]).tolist(),
    )


def loss(y, p):
    p = np.clip(np.asarray(p), 1e-6, 1 - 1e-6)
    y = np.asarray(y)
    return -(y * np.log(p) + (1 - y) * np.log1p(-p))
