import json
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from .common import ROOT, save_json, SEED
from .statistics import mean_ci, loss
from .shot_model import TEAMS


def features(d):
    return np.column_stack(
        [d.distance, d.x.abs(), d.y, d.three, d.seconds / 720, d.period.clip(upper=5)]
    )


def relative_residual(d, team, reps=2000):
    g = d.copy()
    g["target_n"] = g.team.eq(team).astype(int)
    g["target_sum"] = g.residual * g.target_n
    a = (
        g.groupby("game_id")
        .agg(
            target_sum=("target_sum", "sum"),
            target_n=("target_n", "sum"),
            all_sum=("residual", "sum"),
            all_n=("residual", "size"),
        )
        .to_numpy()
    )
    rng = np.random.default_rng(SEED)
    chosen = rng.integers(0, len(a), (reps, len(a)))
    v = a[chosen].sum(axis=1)
    estimates = v[:, 0] / v[:, 1] - v[:, 2] / v[:, 3]
    target = d[d.team.eq(team)]
    estimate = target.residual.mean() - d.residual.mean()
    return estimate, *np.quantile(estimates, [0.025, 0.975]).tolist()


def run():
    d = pd.read_csv(ROOT / "data/rebound_chances.csv.gz")
    train = d[d.date < "2026-01-01"]
    test = d[d.date >= "2026-01-01"].copy()
    model = HistGradientBoostingClassifier(
        max_iter=70,
        max_leaf_nodes=9,
        min_samples_leaf=200,
        learning_rate=0.06,
        l2_regularization=5,
        early_stopping=False,
        random_state=SEED,
    ).fit(features(train), train.oreb)
    test["probability"] = model.predict_proba(features(test))[:, 1]
    test["baseline"] = train.oreb.mean()
    test["residual"] = test.oreb - test.probability
    test["loss_difference"] = loss(test.oreb, test.probability) - loss(
        test.oreb, test.baseline
    )
    diff, lo, hi = mean_ci(test, "loss_difference")
    validation = {
        "train_chances": len(train),
        "test_chances": len(test),
        "model_logloss": float(loss(test.oreb, test.probability).mean()),
        "baseline_logloss": float(loss(test.oreb, test.baseline).mean()),
        "model_brier": float(((test.oreb - test.probability) ** 2).mean()),
        "baseline_brier": float(((test.oreb - test.baseline) ** 2).mean()),
        "loss_difference": diff,
        "lower": lo,
        "upper": hi,
        "later_league_oreb_rate": test.oreb.mean(),
        "later_league_residual": test.residual.mean(),
    }
    save_json("glass_validation.json", validation)
    rows = []
    for team in TEAMS:
        g = test[test.team.eq(team)]
        v, l, h = relative_residual(test, team)
        rows.append(
            dict(
                team=team,
                chances=len(g),
                games=g.game_id.nunique(),
                offensive_rebounds=int(g.oreb.sum()),
                raw_rate=g.oreb.mean(),
                expected_rate=g.probability.mean(),
                league_relative_residual=v,
                lower=l,
                upper=h,
            )
        )
    pd.DataFrame(rows).to_csv(ROOT / "results/glass_profiles.csv", index=False)
    test["zone_group"] = np.where(
        test.three,
        "Missed three",
        np.where(test.distance.lt(5), "Miss inside 5 feet", "Other missed two"),
    )
    test[test.team.isin(TEAMS)].groupby(["team", "zone_group"]).agg(
        chances=("oreb", "size"),
        oreb_rate=("oreb", "mean"),
        expected=("probability", "mean"),
    ).reset_index().to_csv(ROOT / "results/glass_zone_profiles.csv", index=False)
    players = (
        test[test.team.isin(TEAMS) & test.oreb.eq(1)]
        .groupby(["team", "rebounder"])
        .size()
        .rename("offensive_rebounds")
        .reset_index()
    )
    players.to_csv(ROOT / "results/glass_rebounders.csv", index=False)
    test.to_csv(ROOT / "data/glass_holdout.csv.gz", index=False)
    test[test.team.isin(TEAMS) & test.opponent.eq("SAS")].to_csv(
        ROOT / "results/glass_spurs_review.csv", index=False
    )
    save_json(
        "glass_model_spec.json",
        {
            "class": "HistGradientBoostingClassifier",
            "parameters": model.get_params(),
            "features": [
                "distance",
                "abs_x",
                "y",
                "three",
                "seconds/720",
                "period_clipped_at_5",
            ],
            "cutoff": "2026-01-01",
        },
    )
    summary = {"validation": validation, "teams": rows}
    save_json("glass_summary.json", summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
