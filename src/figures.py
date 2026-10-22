from pathlib import Path
import os, json

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(__file__).resolve().parents[1] / ".cache/matplotlib")
)
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Rectangle, Circle
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd
from .common import ROOT

BLACK = "#15191D"
SILVER = "#79858C"
TEAL = "#147D92"
ORANGE = "#BB4A26"
LIGHT = "#DCE3E6"
plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "text.color": BLACK,
        "axes.labelcolor": BLACK,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "axes.edgecolor": LIGHT,
        "xtick.color": SILVER,
        "ytick.color": BLACK,
        "axes.titlesize": 15,
        "axes.titleweight": "bold",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "svg.fonttype": "none",
        "svg.hashsalt": "basketball-portfolio",
    }
)


def save(fig, name, caption):
    fig.text(0.045, 0.025, caption, fontsize=9, color=SILVER)
    fig.savefig(
        ROOT / f"figures/{name}.png",
        dpi=180,
        bbox_inches="tight",
        metadata={"Software": None},
    )
    fig.savefig(
        ROOT / f"figures/{name}.svg",
        bbox_inches="tight",
        metadata={"Creator": None, "Date": None, "Description": caption},
    )
    svg = ROOT / f"figures/{name}.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
    plt.close(fig)


def court(ax):
    for p in [
        Rectangle((-25, -5.25), 50, 47, fill=False),
        Rectangle((-8, -5.25), 16, 19, fill=False),
        Circle((0, 0), 0.75, fill=False),
        Arc((0, 13.75), 12, 12, theta1=0, theta2=180),
        Arc((0, 0), 47.5, 47.5, theta1=22, theta2=158),
    ]:
        p.set_edgecolor(SILVER)
        p.set_linewidth(0.7)
        ax.add_patch(p)
    ax.plot([-22, -22], [-5.25, 8.9], color=SILVER, lw=0.7)
    ax.plot([22, 22], [-5.25, 8.9], color=SILVER, lw=0.7)
    ax.set_xlim(-25, 25)
    ax.set_ylim(-5.25, 35)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines["bottom"].set_visible(False)


COLORS = {"OKC": "#1876A3", "DEN": "#2D3C56", "HOU": "#BC4628", "MIN": "#218267"}
SHORT = {
    "Shai Gilgeous-Alexander": "Gilgeous-Alexander",
    "Jalen Williams": "Jalen Williams",
    "Chet Holmgren": "Holmgren",
    "Nikola Jokić": "Jokić",
    "Anthony Edwards": "Edwards",
    "Kevin Durant": "Durant",
}
ZONES = ["Rim", "Other paint", "Midrange", "Corner three", "Above-break three"]


def run():
    d = pd.read_csv(ROOT / "results/foul_profiles.csv")
    d = d[d.metric.eq("ft_only")].sort_values("estimate", ascending=False)
    fig, ax = plt.subplots(figsize=(10, 5.3))
    fig.subplots_adjust(left=0.27, right=0.97, bottom=0.24, top=0.81)
    for i, (_, v) in enumerate(d.iterrows()):
        c = COLORS[v.team]
        ax.errorbar(
            v.estimate,
            i,
            xerr=[[v.estimate - v.lower], [v.upper - v.estimate]],
            fmt="o",
            color=c,
            capsize=4,
            ms=8,
        )
        ax.text(
            v.upper + 0.008,
            i,
            f"{v.estimate:.1%} · {int(v.chances):,} chances",
            va="center",
            fontsize=9,
        )
    ax.set_yticks(range(len(d)), d.player.map(SHORT))
    ax.invert_yaxis()
    ax.set_xlim(0, 0.27)
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.set_xlabel("Share of resolved scoring chances that are free-throw-only trips")
    ax.set_title(
        "SGA adds scoring chances that never become field goals", loc="left", pad=18
    )
    save(
        fig,
        "foul_frequency",
        "Audited 2025–26 games. Shooting and selected nonshooting foul trips; special free throws excluded. 95% game-bootstrap intervals.",
    )
    d = pd.read_csv(ROOT / "data/scoring_chances.csv.gz")
    s = d[d.player.eq("Shai Gilgeous-Alexander")]
    values = [
        s.fg_points.sum(),
        s.loc[s.channel.eq("And-one"), "ft_points"].sum(),
        s.loc[s.channel.eq("Shooting-foul trip"), "ft_points"].sum(),
        s.loc[s.channel.eq("Nonshooting-foul trip"), "ft_points"].sum(),
    ]
    values = np.array(values) / len(s) * 100
    fig, ax = plt.subplots(figsize=(10, 4.7))
    fig.subplots_adjust(left=0.24, right=0.96, bottom=0.24, top=0.80)
    names = [
        "Field goals",
        "And-one free throws",
        "Shooting-foul trips",
        "Nonshooting-foul trips",
    ]
    bars = ax.barh(
        names, values, color=[BLACK, SILVER, COLORS["OKC"], TEAL], height=0.6
    )
    for b, v in zip(bars, values):
        ax.text(v + 1, b.get_y() + b.get_height() / 2, f"{v:.1f}", va="center")
    ax.invert_yaxis()
    ax.set_xlim(0, 115)
    ax.set_xlabel("Points per 100 resolved scoring chances")
    ax.set_title(
        f"How SGA reaches {values.sum():.1f} points per 100 chances", loc="left", pad=18
    )
    save(
        fig,
        "foul_scoring",
        "Scoring channels add to the total. And-one points stay with the made field-goal chance; this is not points per possession.",
    )
    d = pd.read_csv(ROOT / "results/foul_spurs_split.csv")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.31, top=0.80, wspace=0.30)
    for ax, metric, title in [
        (axes[0], "ft_only", "Free-throw-only chance share"),
        (axes[1], "points", "Points per resolved chance"),
    ]:
        g = d[d.metric.eq(metric)]
        ax.errorbar(
            [0, 1],
            g.estimate,
            yerr=[g.estimate - g.lower, g.upper - g.estimate],
            fmt="o",
            capsize=5,
            ms=8,
            color=COLORS["OKC"],
        )
        ax.set_xticks([0, 1], ["Versus SAS\n4 games", "Other opponents\n64 games"])
        ax.set_xlim(-0.4, 1.4)
        ax.set_title(title, loc="left", fontsize=12, pad=18)
        if metric == "ft_only":
            ax.yaxis.set_major_formatter(PercentFormatter(1))
            ax.set_ylim(0, 0.23)
        else:
            ax.set_ylim(0.9, 1.55)
    save(
        fig,
        "foul_spurs",
        "SGA: 99 chances versus San Antonio and 1,477 elsewhere. Four-game matchup intervals cannot establish a repeatable defensive effect.",
    )
    d = pd.read_csv(ROOT / "results/defense_zone_profiles.csv")
    fig, ax = plt.subplots(figsize=(9.8, 5))
    fig.subplots_adjust(left=0.24, right=0.96, bottom=0.26, top=0.82)
    for label, c, offset in [("League", SILVER, -0.07), ("OKC", COLORS["OKC"], 0.07)]:
        g = d[d.defense.eq(label)].set_index("zone").reindex(ZONES)
        ax.scatter(g.share, np.arange(5) + offset, color=c, s=65, label=label)
    ax.set_yticks(range(5), ZONES)
    ax.invert_yaxis()
    ax.set_xlim(0, 0.43)
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.set_xlabel("Share of opponent field goal attempts")
    ax.set_title("OKC gives up a different mix of locations", loc="left", pad=18)
    ax.legend(frameon=False, loc="lower right")
    save(
        fig,
        "okc_location_mix",
        "2025–26 audited games, attempts below 40 feet and consistent zone labels. Shares describe observed shots, not open-shot availability.",
    )
    d = pd.read_csv(ROOT / "results/defense_zone_profiles.csv")
    d = d[d.defense.eq("OKC")].set_index("zone").reindex(ZONES)
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.subplots_adjust(left=0.25, right=0.96, bottom=0.24, top=0.82)
    for i, (_, v) in enumerate(d.iterrows()):
        ax.errorbar(
            v.residual * 100,
            i,
            xerr=[[(v.residual - v.lower) * 100], [(v.upper - v.residual) * 100]],
            fmt="o",
            capsize=4,
            ms=7,
            color=COLORS["OKC"],
        )
    ax.set_yticks(range(5), ZONES)
    ax.invert_yaxis()
    ax.axvline(0, color=LIGHT)
    ax.set_xlabel("Actual minus model expectation: FG points per 100 attempts")
    ax.set_title(
        "Shot location and shooter history leave part of the gap", loc="left", pad=18
    )
    save(
        fig,
        "okc_conversion",
        "Model trained on 2024–25; evaluated on 2025–26. 95% game-bootstrap intervals. No defender distance or coverage information.",
    )
    cells = pd.read_csv(ROOT / "results/okc_spatial_cells.csv")
    grid = cells.pivot(index="y", columns="x", values="difference")
    fig, ax = plt.subplots(figsize=(7.5, 6.7))
    fig.subplots_adjust(left=0.12, right=0.84, bottom=0.14, top=0.82)
    limit = max(abs(grid.to_numpy().min()), abs(grid.to_numpy().max()))
    im = ax.imshow(
        grid.to_numpy(),
        extent=[-25, 25, -5, 40],
        origin="lower",
        cmap="RdBu_r",
        vmin=-limit,
        vmax=limit,
        interpolation="nearest",
        alpha=0.85,
    )
    court(ax)
    ax.set_ylim(-5, 40)
    ax.set_xlim(-25, 25)
    ax.set_title(
        "Where OKC opponents take more—or fewer—shots", loc="left", fontsize=13, pad=20
    )
    bar = fig.colorbar(im, ax=ax, fraction=0.045, pad=0.04)
    bar.set_label("OKC minus league: attempts per 100 FGA", fontsize=9)
    save(
        fig,
        "okc_spatial",
        "5-foot cells; common total-attempt denominators. Positive = more attempts here against OKC.\nThe map is descriptive, not a coverage chart.",
    )
    d = pd.read_csv(ROOT / "results/glass_profiles.csv").sort_values(
        "league_relative_residual", ascending=False
    )
    fig, ax = plt.subplots(figsize=(10, 4.8))
    fig.subplots_adjust(left=0.15, right=0.97, bottom=0.25, top=0.81)
    for i, (_, v) in enumerate(d.iterrows()):
        ax.errorbar(
            v.league_relative_residual * 100,
            i,
            xerr=[
                [(v.league_relative_residual - v.lower) * 100],
                [(v.upper - v.league_relative_residual) * 100],
            ],
            fmt="o",
            color=COLORS[v.team],
            capsize=5,
            ms=9,
        )
        ax.text(
            v.league_relative_residual * 100,
            i + 0.20,
            f"{v.league_relative_residual*100:+.1f} pp · {int(v.chances):,} chances",
            ha="center",
            va="top",
            fontsize=9,
        )
    ax.set_yticks(range(4), d.team)
    ax.set_ylim(3.45, -0.5)
    ax.axvline(0, color=LIGHT)
    ax.set_xlabel(
        "Recovery above shot-context expectation, relative to the later league"
    )
    ax.set_title(
        "Houston creates the clearest live-rebound problem", loc="left", pad=18
    )
    save(
        fig,
        "glass_adjusted",
        "January onward. Percentage-point residual differences with 95% game-bootstrap intervals; recognized player rebounds only.",
    )
    d = pd.read_csv(ROOT / "results/glass_zone_profiles.csv")
    zones = ["Miss inside 5 feet", "Other missed two", "Missed three"]
    fig, ax = plt.subplots(figsize=(10, 4.8))
    fig.subplots_adjust(left=0.11, right=0.97, bottom=0.25, top=0.82)
    for i, team in enumerate(["HOU", "MIN", "DEN", "OKC"]):
        g = d[d.team.eq(team)].set_index("zone_group").reindex(zones)
        ax.plot(
            np.arange(3) + (i - 1.5) * 0.025,
            g.oreb_rate,
            "o-",
            color=COLORS[team],
            label=team,
            lw=1.8,
            ms=7,
        )
    ax.set_xticks(range(3), zones)
    ax.set_ylabel("Offensive-rebound recovery rate")
    ax.set_ylim(0.1, 0.55)
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_title("Recovery rates differ by missed-shot location", loc="left", pad=18)
    ax.legend(ncol=4, frameon=False, loc="upper right", fontsize=9)
    save(
        fig,
        "glass_locations",
        "Raw later-sample rates, grouped by missed-shot location. No player-position or box-out data are available.",
    )
    d = pd.read_csv(ROOT / "results/glass_rebounders.csv")
    d = d[d.team.eq("HOU")].nlargest(6, "offensive_rebounds")
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    fig.subplots_adjust(left=0.24, right=0.96, bottom=0.24, top=0.81)
    ax.barh(d.rebounder, d.offensive_rebounds, color=COLORS["HOU"], height=0.6)
    for i, v in enumerate(d.offensive_rebounds):
        ax.text(v + 1, i, str(v), va="center")
    ax.set_xlim(0, d.offensive_rebounds.max() * 1.2)
    ax.invert_yaxis()
    ax.set_xlabel("Recorded offensive rebounds in eligible later-sample chances")
    ax.set_title(
        "Houston’s leading offensive rebounders in this sample", loc="left", pad=18
    )
    save(
        fig,
        "glass_rebounders",
        "2025–26 personnel and January-onward sample. Counts are not opportunity-adjusted player ratings; refresh current rotations before use.",
    )
    from tools.feature_charts import main as feature_charts
    feature_charts()
    return 9


if __name__ == "__main__":
    print(run(), "figures exported")
