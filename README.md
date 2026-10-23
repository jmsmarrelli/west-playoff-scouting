# Western playoff scouting

[Read the basketball decision brief](reports/00_decision_brief.md) · [Visual design and rebuild](tools/VISUALS.md)

Joseph Smarrelli · September 2026

Three opponent studies for San Antonio preparation, with particular attention to Oklahoma City. Scouting priorities follow the [August Western Conference rankings](https://www.nba.com/news/offseason-power-rankings-west-2026). These are 2025–26 regular-season benchmarks, not a projected bracket or a current-rotation report.

## The studies

| Study | Basketball question | Main method |
| --- | --- | --- |
| [The part of SGA’s offense a shot chart misses](reports/01_sga_foul_channel.md) | How much scoring occurs on foul trips with no field goal attempt? | Event-linked free-throw reconstruction and game bootstrap |
| [The shots Oklahoma City allows](reports/02_okc_shot_map.md) | Where do opponents shoot, and how does conversion compare with location and shooter history? | Previous-season gradient boosting, shooter priors, calibration and spatial comparison |
| [The rebounding plan should change with the opponent](reports/03_western_glass.md) | Which opponents recover more misses after accounting for shot context? | Live-rebound reconstruction, chronological validation and league-centered residuals |

The package contains three executed notebooks, three standalone HTML articles, nine charts in PNG and SVG, audited event cohorts, model evaluation rows, source checksums, SQL summaries and automated checks. The rebounding comparison covers OKC, Denver, Houston and Minnesota. Selection is a scouting scope, not an assertion that these are the only potential opponents.

## Reproduce

Use Python 3.12. From the repository root:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
OMP_NUM_THREADS=4 python -m src.run_all --fetch
python -m unittest discover -s tests -v
OMP_NUM_THREADS=4 python -m src.notebooks
```

`--fetch` downloads four pinned archives, verifies SHA-256 hashes, and extracts only CSV members. Raw files are deliberately excluded from this distribution. Subsequent rebuilds can omit `--fetch`. The full run creates an indexed local SQLite database; SQL summaries are also included as portable CSVs. The notebooks rerun each study after the shared cohort build. No credentials or private feed are required.

For a quick check of the included derived data, install the requirements and run the tests; no raw download is necessary. CI follows that path, while a full source rebuild is documented in [VALIDATION.md](VALIDATION.md).

## Reading the results

The strongest historical distinction in the four-team rebound comparison belongs to Houston. The OKC studies separate free-throw scoring from field-goal efficiency, and shot location from conversion relative to a limited public-data model. Each article explains its denominator, uncertainty and the film review needed before making a coaching change.

A lower modeled residual is not an isolated defender effect. Free-throw chances and rebound chances are not possessions. The models omit tracking information and do not estimate causal effects of coverage choices. Current personnel, availability and tactics must be checked before applying these completed-season results to a future matchup.

See [METHODS.md](METHODS.md) for data rules and [VALIDATION.md](VALIDATION.md) for the checks performed.

## Source and rights

Input records come from the [pinned NBA data archive](https://github.com/shufinskiy/nba_data/tree/e829d4678be1e075f99e5d41a1c5f97089be446b). The source manifest specifies every file, URL and checksum. These are public records redistributed by a third party; the game audit checks consistency, not independent official certification. Code is MIT licensed. Source data remain subject to their original owners’ terms. No team affiliation or proprietary data access is claimed.

## Current review

See [current validation](VALIDATION_CURRENT.md) for executed checks and unresolved rebuild requirements, and [provenance](PROVENANCE.md) for AI assistance. [Portfolio navigation](https://github.com/jmsmarrelli/basketball-analytics).
