"""Editorial scouting figures from committed result tables; no model refit.

Run with python -m tools.feature_charts. Color denotes location-frequency
differences, never defensive pressure or the probability that a shot goes in.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.patches import Arc, Rectangle, Circle
from .chart_style import canvas, finish, stat, note, tidy, TEAL, ORANGE, MUTED, INK, GRID, PAPER

ROOT = Path(__file__).resolve().parents[1]


def glass():
    d = pd.read_csv(ROOT / "results/glass_profiles.csv").sort_values("league_relative_residual", ascending=False).reset_index(drop=True)
    fig = canvas("04 / Western scouting", "Houston stands out on the offensive glass",
                 "January–April 2026 · recovery above recorded shot-context expectation, relative to the later league")
    ax = fig.add_axes([.20, .26, .48, .46])
    names = {"HOU": "Houston", "MIN": "Minnesota", "OKC": "Oklahoma City", "DEN": "Denver"}
    for i, r in d.iterrows():
        v, lo, hi = np.array([r.league_relative_residual, r.lower, r.upper]) * 100
        color = ORANGE if r.team == "HOU" else TEAL
        ax.hlines(i, lo, hi, color=color, lw=3)
        ax.scatter(v, i, s=110, color=color, zorder=3)
        ax.text(v, i-.24, f"{v:+.1f} pp", ha="center", color=color, fontsize=17, weight="bold")
        ax.text(v, i+.24, f"{int(r.chances):,} chances · {int(r.games)} games", ha="center", color=MUTED, fontsize=10)
    ax.set_yticks(range(len(d)), [names[t] for t in d.team])
    ax.set_ylim(len(d)-.35, -.65)
    ax.set_xlim(-6.8, 11)
    ax.set_xticks([-5, 0, 5, 10])
    ax.axvline(0, color=GRID, lw=1.2)
    ax.set_xlabel("League-relative rebound residual (percentage points)", labelpad=14)
    tidy(ax)
    h = d[d.team.eq("HOU")].iloc[0]
    stat(fig, .75, .68, f"{h.raw_rate:.1%}", "Houston’s observed recovery rate", color=ORANGE)
    stat(fig, .75, .54, f"{h.expected_rate:.1%}", "Houston’s shot-context expectation")
    note(fig, .75, .43, "Build a review queue", "Prioritize Houston misses. Tag the first contact, weak-side position and who releases in transition.", width=30)
    note(fig, .75, .23, "Still unobserved", "Box-outs, assignments and player positioning.", width=30)
    finish(fig, ROOT / "figures/glass_adjusted",
           "Source: results/glass_profiles.csv · Recognized player rebounds only. Model trained before January; evaluated on later games.",
           "Lines: 95% game-bootstrap intervals. Residual = observed − expected − later-league residual; not a causal team effect.")


def court(ax):
    # Feet relative to the hoop; preserve the geometry used by the source grid.
    for patch in [Rectangle((-25, -5.25), 50, 47, fill=False),
                  Rectangle((-8, -5.25), 16, 19, fill=False),
                  Circle((0, 0), .75, fill=False),
                  Arc((0, 13.75), 12, 12, theta1=0, theta2=180),
                  Arc((0, 13.75), 12, 12, theta1=180, theta2=360, linestyle="--"),
                  Arc((0, 0), 8, 8, theta1=0, theta2=180),
                  Arc((0, 0), 47.5, 47.5, theta1=22.13, theta2=157.87)]:
        patch.set_edgecolor(INK); patch.set_linewidth(.85); patch.set_zorder(5); ax.add_patch(patch)
    ax.plot([-3, 3], [-.75, -.75], color=INK, lw=1.1, zorder=5)
    for x in [-22, 22]:
        ax.plot([x, x], [-5.25, 8.95], color=INK, lw=.85, zorder=5)
    ax.set(xlim=(-26, 26), ylim=(-6.25, 42.75), aspect="equal")
    ax.axis("off")


def spatial():
    d = pd.read_csv(ROOT / "results/okc_spatial_cells.csv")
    meta = json.loads((ROOT / "results/shot_summary.json").read_text())
    okc = next(t for t in meta["teams"] if t["defense"] == "OKC")
    if d.duplicated(["x", "y"]).any() or not np.isfinite(d.select_dtypes("number")).all().all():
        raise ValueError("Spatial cells must be unique and finite")
    np.testing.assert_allclose(d.difference, d.okc_per100-d.league_per100, atol=1e-12)
    fig = canvas("Court geography / Descriptive scouting", "Where opponents shoot against Oklahoma City",
                 "2025–26 regular season · each square is a 5-foot cell · color compares frequency with the league", 9.5)
    ax = fig.add_axes([.045, .23, .535, .54])
    grid = d.pivot(index="y", columns="x", values="difference").sort_index().sort_index(axis=1)
    limit = np.ceil(np.abs(d.difference).max()*2)/2
    cmap = LinearSegmentedColormap.from_list("frequency", [TEAL, PAPER, ORANGE])
    im = ax.imshow(grid.to_numpy(), origin="lower", extent=[-25,25,-5,40],
                   interpolation="nearest", cmap=cmap, norm=TwoSlopeNorm(0, -limit, limit))
    court(ax)
    cb = fig.colorbar(im, cax=fig.add_axes([.13, .193, .35, .016]), orientation="horizontal")
    cb.outline.set_visible(False)
    cb.set_ticks([-limit, 0, limit], labels=[f"{limit:g} fewer", "Same", f"{limit:g} more"])
    cb.ax.tick_params(length=0, labelsize=9)
    cb.set_label("Attempts in the cell per 100 total FGA", fontsize=9, labelpad=6)
    stat(fig, .625, .70, f"{okc['attempts']:,}", f"opponent attempts · {okc['games']} games")
    note(fig, .625, .58, "Read the geography", "Orange means opponents take a larger share of their shots in that cell against OKC. Teal means a smaller share.", width=43)
    note(fig, .625, .395, "Turn a map into a question", "Which actions produce the extra corner attempts? Review those possessions before attributing the pattern to a coverage choice.", width=43)
    note(fig, .625, .23, "No measure of openness", "These records do not show defender distance or rotations.", width=43)
    finish(fig, ROOT / "figures/okc_spatial",
           "Source: results/okc_spatial_cells.csv · Consistent zone labels; attempts below 40 feet. Denominators include all eligible attempts.",
           "No smoothing. Cells outside the displayed grid are not renormalized. Color shows shot frequency, not efficiency or a causal effect.")


def main():
    glass()
    spatial()


if __name__ == "__main__":
    main()
