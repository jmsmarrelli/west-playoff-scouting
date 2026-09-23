import json
import pandas as pd
from .common import ROOT, save_json
from .statistics import mean_ci


def run():
    d = pd.read_csv(ROOT / "data/scoring_chances.csv.gz")
    d["ft_only"] = d.channel.isin(
        ["Shooting-foul trip", "Nonshooting-foul trip"]
    ).astype(int)
    rows = []
    for (player, team), g in d.groupby(["player", "team"]):
        for metric in ["ft_only", "points", "ft_points"]:
            value, lo, hi = mean_ci(g, metric)
            rows.append(
                dict(
                    player=player,
                    team=team,
                    metric=metric,
                    chances=len(g),
                    games=g.game_id.nunique(),
                    estimate=value,
                    lower=lo,
                    upper=hi,
                )
            )
    pd.DataFrame(rows).to_csv(ROOT / "results/foul_profiles.csv", index=False)
    channels = (
        d.groupby(["player", "team", "channel"])
        .agg(
            chances=("points", "size"),
            points=("points", "sum"),
            ft_points=("ft_points", "sum"),
        )
        .reset_index()
    )
    channels["share"] = channels.chances / channels.groupby(
        ["player", "team"]
    ).chances.transform("sum")
    channels.to_csv(ROOT / "results/foul_channels.csv", index=False)
    a = pd.read_csv(ROOT / "results/free_throw_audit.csv")
    coverage = []
    for player, g in a.groupby("player"):
        coverage.append(
            dict(
                player=player,
                normal_fta=int(g.normal_attempts.sum()),
                retained_normal_fta=int(
                    g.loc[g.status.eq("retained"), "normal_attempts"].sum()
                ),
                special_fta=int(g.special_attempts.sum()),
                excluded_normal_clusters=int(
                    (g.normal_attempts.gt(0) & g.status.ne("retained")).sum()
                ),
            )
        )
    pd.DataFrame(coverage).to_csv(ROOT / "results/foul_coverage.csv", index=False)
    sga = d[d.player.eq("Shai Gilgeous-Alexander")]
    splits = []
    for name, g in [
        ("Versus San Antonio", sga[sga.opponent.eq("SAS")]),
        ("Other opponents", sga[~sga.opponent.eq("SAS")]),
    ]:
        for metric in ["ft_only", "points"]:
            v, lo, hi = mean_ci(g, metric)
            splits.append(
                dict(
                    sample=name,
                    metric=metric,
                    chances=len(g),
                    games=g.game_id.nunique(),
                    estimate=v,
                    lower=lo,
                    upper=hi,
                )
            )
    pd.DataFrame(splits).to_csv(ROOT / "results/foul_spurs_split.csv", index=False)
    sga[sga.ft_only.eq(1)].sort_values(["game_id", "event_id"]).head(15).to_csv(
        ROOT / "results/foul_review_queue.csv", index=False
    )
    summary = {
        "sga_chances": len(sga),
        "sga_games": sga.game_id.nunique(),
        "sga_ft_only_share": sga.ft_only.mean(),
        "sga_points_per_chance": sga.points.mean(),
        "sga_fg_points": int(sga.fg_points.sum()),
        "sga_ft_points": int(sga.ft_points.sum()),
        "sga_ft_point_share": sga.ft_points.sum() / sga.points.sum(),
        "coverage": coverage,
        "spurs_split": splits,
    }
    save_json("foul_summary.json", summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
