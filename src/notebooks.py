"""Create and execute the three review notebooks with the current Python environment."""

import os, sys, json
import nbformat as nb
from nbclient import NotebookClient
from .common import ROOT


def run():
    os.environ.setdefault("OMP_NUM_THREADS", "4")
    cache = ROOT / ".cache"
    cache.mkdir(exist_ok=True)
    for key, folder in [
        ("JUPYTER_RUNTIME_DIR", "runtime"),
        ("IPYTHONDIR", "ipython"),
        ("MPLCONFIGDIR", "matplotlib"),
    ]:
        p = cache / folder
        p.mkdir(exist_ok=True)
        os.environ[key] = str(p)
    spec = cache / "jupyter/kernels/research"
    spec.mkdir(parents=True, exist_ok=True)
    (spec / "kernel.json").write_text(
        json.dumps(
            {
                "argv": [
                    sys.executable,
                    "-m",
                    "ipykernel_launcher",
                    "-f",
                    "{connection_file}",
                ],
                "display_name": "Python 3",
                "language": "python",
            }
        )
    )
    os.environ["JUPYTER_PATH"] = str(cache / "jupyter")
    jobs = [
        (
            "01_sga_foul_channel",
            "foul_channel",
            "foul_channels",
            "foul_frequency",
            "foul_spurs",
        ),
        (
            "02_okc_shot_map",
            "shot_model",
            "defense_zone_profiles",
            "okc_conversion",
            "okc_spatial",
        ),
        (
            "03_western_glass",
            "glass_pressure",
            "glass_profiles",
            "glass_adjusted",
            "glass_rebounders",
        ),
    ]
    for stem, module, table, fig1, fig2 in jobs:
        article = (ROOT / f"reports/{stem}.md").read_text()
        book = nb.v4.new_notebook(
            metadata={
                "kernelspec": {
                    "name": "python3",
                    "display_name": "Python 3",
                    "language": "python",
                },
                "language_info": {"name": "python", "version": "3.12"},
            }
        )
        book.cells = [
            nb.v4.new_markdown_cell(article.split("##")[0]),
            nb.v4.new_code_cell(
                "from pathlib import Path\nimport os, sys\nroot = Path.cwd()\nif root.name == 'notebooks':\n    root = root.parent\nsys.path.insert(0, str(root))\nos.chdir(root)\nimport pandas as pd\nfrom IPython.display import display, Image\nfrom src import "
                + module
                + "\nsummary = "
                + module
                + ".run()\nfrom src import figures\nfigures.run()\nsummary"
            ),
            nb.v4.new_markdown_cell(
                "## Results\nThe following table is regenerated from the pinned inputs."
            ),
            nb.v4.new_code_cell(f"pd.read_csv('results/{table}.csv')"),
            nb.v4.new_code_cell(
                f"display(Image(filename='figures/{fig1}.png'))\ndisplay(Image(filename='figures/{fig2}.png'))"
            ),
        ]
        if module == "foul_channel":
            code = "d = pd.read_csv('data/scoring_chances.csv.gz')\nassert (d.points == d.fg_points + d.ft_points).all()\ndisplay(pd.read_csv('results/foul_coverage.csv'))\ndisplay(pd.read_csv('results/foul_review_queue.csv').head(8))"
            explanation = "## Reconcile scoring and inspect exclusions\nFree throws attached to made field goals remain part of the original chance. Unsupported trips are counted separately in the coverage report."
        elif module == "shot_model":
            code = "import json, numpy as np\nfrom src.statistics import loss\nd = pd.read_csv('data/shot_validation_rows.csv.gz')\nv = json.loads(Path('results/shot_validation.json').read_text())\nassert np.isclose(loss(d.made, d.probability).mean(), v['model_logloss'])\ndisplay(v)\ndisplay(pd.read_csv('results/shot_calibration.csv'))"
            explanation = "## Recalculate evaluation loss and inspect calibration\nThese predictions use the previous season for model training and shooter history. The current season provides held-out outcomes."
        else:
            code = "import json, numpy as np\nd = pd.read_csv('data/glass_holdout.csv.gz')\np = pd.read_csv('results/glass_profiles.csv')\nassert d.date.ge('2026-01-01').all()\nfor row in p.itertuples():\n    assert np.isclose(row.league_relative_residual, d.loc[d.team.eq(row.team), 'residual'].mean() - d.residual.mean())\ndisplay(json.loads(Path('results/glass_validation.json').read_text()))\ndisplay(pd.read_csv('results/glass_spurs_review.csv').head(8))"
            explanation = "## Separate forecasting from the historical comparison\nThe prediction score uses the frozen early-sample model. The descriptive team residual is centered on later league calibration."
        book.cells += [nb.v4.new_markdown_cell(explanation), nb.v4.new_code_cell(code)]
        book.cells += [
            nb.v4.new_markdown_cell(
                "## Interpretation and limits\nRead the complete accompanying article for denominators, uncertainty, model selection, and the basketball decisions this analysis cannot identify. The results here are historical research, not a claim of team deployment."
            )
        ]
        path = ROOT / f"notebooks/{stem}.ipynb"
        NotebookClient(
            book,
            timeout=600,
            kernel_name="research",
            resources={"metadata": {"path": str(ROOT)}},
        ).execute()
        for cell in book.cells:
            cell.metadata.pop("execution", None)
        nb.write(book, path)
        print(path.name, "executed", flush=True)


if __name__ == "__main__":
    run()
