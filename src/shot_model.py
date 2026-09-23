import json
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from .common import ROOT, shots, save_json, SEED
from .statistics import mean_ci, loss

TEAMS = ["OKC", "DEN", "HOU", "MIN"]


def zone_name(d):
    return d.SHOT_ZONE_BASIC.replace(
        {
            "Restricted Area": "Rim",
            "In The Paint (Non-RA)": "Other paint",
            "Mid-Range": "Midrange",
            "Left Corner 3": "Corner three",
            "Right Corner 3": "Corner three",
            "Above the Break 3": "Above-break three",
            "Backcourt": "Other",
        }
    )


def add_prior(d, prior):
    d = d.copy()
    counts = prior.groupby(["PLAYER_ID", "three"]).made.agg(["sum", "count"])
    league = prior.groupby("three").made.mean()
    counts["prior"] = (
        counts["sum"] + 100 * counts.index.get_level_values("three").map(league)
    ) / (counts["count"] + 100)
    keys = pd.MultiIndex.from_frame(d[["PLAYER_ID", "three"]])
    d["prior"] = counts.prior.reindex(keys).to_numpy()
    d["prior"] = d.prior.fillna(d.three.map(league))
    return d


def features(d):
    return np.column_stack(
        [
            d.SHOT_DISTANCE,
            d.LOC_X.abs() / 10,
            d.LOC_Y / 10,
            d.three.astype(int),
            d.prior,
        ]
    )


def clean(d):
    d = d[d.SHOT_DISTANCE.lt(40)].copy()
    d["zone"] = zone_name(d)
    conflict = (d.three & ~d.zone.isin(["Corner three", "Above-break three"])) | (
        ~d.three & ~d.zone.isin(["Rim", "Other paint", "Midrange"])
    )
    return d[~conflict].copy()


def run():
    old = clean(shots(2023))
    train = add_prior(clean(shots(2024)), old)
    test = add_prior(clean(shots(2025)), clean(shots(2024)))
    audited = pd.read_csv(ROOT / "results/game_audit.csv")
    test = test[
        test.GAME_ID.isin(audited.loc[audited.status.eq("valid"), "game_id"])
    ].copy()
    model = HistGradientBoostingClassifier(
        max_iter=90,
        max_leaf_nodes=15,
        min_samples_leaf=200,
        learning_rate=0.06,
        l2_regularization=5,
        early_stopping=False,
        random_state=SEED,
    ).fit(features(train), train.made)
    test["probability"] = model.predict_proba(features(test))[:, 1]
    base = train.groupby("zone").made.mean()
    test["baseline"] = test.zone.map(base)
    test["value"] = np.where(test.three, 3, 2)
    test["expected_points"] = test.probability * test.value
    test["residual"] = test.points - test.expected_points
    test["game_id"] = test.GAME_ID
    test["loss_difference"] = loss(test.made, test.probability) - loss(
        test.made, test.baseline
    )
    v, lo, hi = mean_ci(test, "loss_difference")
    validation = {
        "training_attempts": len(train),
        "test_attempts": len(test),
        "test_games": test.GAME_ID.nunique(),
        "model_logloss": float(loss(test.made, test.probability).mean()),
        "baseline_logloss": float(loss(test.made, test.baseline).mean()),
        "model_brier": float(((test.made - test.probability) ** 2).mean()),
        "baseline_brier": float(((test.made - test.baseline) ** 2).mean()),
        "loss_difference": v,
        "lower": lo,
        "upper": hi,
        "training_season": "2024-25",
        "test_season": "2025-26",
    }
    save_json("shot_validation.json", validation)
    xb = np.arange(-25, 26, 5)
    yb = np.arange(-5, 41, 5)
    league_grid = (
        np.histogram2d(test.LOC_X / 10, test.LOC_Y / 10, bins=[xb, yb])[0]
        / len(test)
        * 100
    )
    okc = test[test.opponent.eq("OKC")]
    okc_grid = (
        np.histogram2d(okc.LOC_X / 10, okc.LOC_Y / 10, bins=[xb, yb])[0]
        / len(okc)
        * 100
    )
    cells = []
    for i in range(len(xb) - 1):
        for j in range(len(yb) - 1):
            cells.append(
                dict(
                    x=(xb[i] + xb[i + 1]) / 2,
                    y=(yb[j] + yb[j + 1]) / 2,
                    league_per100=league_grid[i, j],
                    okc_per100=okc_grid[i, j],
                    difference=okc_grid[i, j] - league_grid[i, j],
                )
            )
    pd.DataFrame(cells).to_csv(ROOT / "results/okc_spatial_cells.csv", index=False)
    test["prob_bin"] = pd.cut(
        test.probability, bins=np.linspace(0, 1, 11), include_lowest=True
    )
    test.groupby("prob_bin", observed=True).agg(
        attempts=("made", "size"),
        predicted=("probability", "mean"),
        observed=("made", "mean"),
    ).reset_index().to_csv(ROOT / "results/shot_calibration.csv", index=False)
    rows = []
    zones = []
    for opponent in TEAMS + ["League"]:
        g = test if opponent == "League" else test[test.opponent.eq(opponent)]
        residual, rl, rh = mean_ci(g, "residual")
        rows.append(
            dict(
                defense=opponent,
                attempts=len(g),
                games=g.GAME_ID.nunique(),
                actual=g.points.mean(),
                expected=g.expected_points.mean(),
                residual=residual,
                lower=rl,
                upper=rh,
                corner_share=g.zone.eq("Corner three").mean(),
                rim_share=g.zone.eq("Rim").mean(),
            )
        )
        for zone, z in g.groupby("zone"):
            rv, l, h = mean_ci(z, "residual")
            zones.append(
                dict(
                    defense=opponent,
                    zone=zone,
                    attempts=len(z),
                    share=len(z) / len(g),
                    actual=z.points.mean(),
                    expected=z.expected_points.mean(),
                    residual=rv,
                    lower=l,
                    upper=h,
                )
            )
    pd.DataFrame(rows).to_csv(ROOT / "results/defense_shot_profiles.csv", index=False)
    pd.DataFrame(zones).to_csv(ROOT / "results/defense_zone_profiles.csv", index=False)
    cols = [
        "GAME_ID",
        "GAME_EVENT_ID",
        "date",
        "PLAYER_ID",
        "PLAYER_NAME",
        "team",
        "opponent",
        "zone",
        "SHOT_DISTANCE",
        "LOC_X",
        "LOC_Y",
        "three",
        "made",
        "points",
        "prior",
        "probability",
        "baseline",
        "expected_points",
        "residual",
    ]
    test[test.opponent.isin(TEAMS)][cols].to_csv(
        ROOT / "data/contender_shots.csv.gz", index=False
    )
    # Evaluation rows keep the frozen probabilities so published validation is inspectable.
    test[["game_id", "made", "probability", "baseline", "loss_difference"]].to_csv(
        ROOT / "data/shot_validation_rows.csv.gz", index=False
    )
    q = test[test.opponent.eq("OKC") & test.team.eq("SAS")]
    split = []
    for zone, g in q.groupby("zone"):
        split.append(
            dict(
                zone=zone,
                attempts=len(g),
                games=g.GAME_ID.nunique(),
                actual=g.points.mean(),
                expected=g.expected_points.mean(),
                share=len(g) / len(q),
            )
        )
    pd.DataFrame(split).to_csv(ROOT / "results/spurs_okc_shots.csv", index=False)
    q[q.zone.eq("Corner three")][cols].head(15).to_csv(
        ROOT / "results/shot_review_queue.csv", index=False
    )
    save_json(
        "shot_model_spec.json",
        {
            "class": "HistGradientBoostingClassifier",
            "parameters": model.get_params(),
            "features": [
                "distance",
                "abs_x_feet",
                "y_feet",
                "three",
                "prior_player_2_or_3_make_rate",
            ],
            "prior_strength": 100,
            "training_prior_season": "2023-24",
            "evaluation_prior_season": "2024-25",
        },
    )
    summary = {
        "validation": validation,
        "teams": rows,
        "spurs_vs_okc_attempts": len(q),
        "spurs_vs_okc_games": q.GAME_ID.nunique(),
    }
    save_json("shot_summary.json", summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
