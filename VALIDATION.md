# Validation record

Completed September 10, 2026, with Python 3.12 and the dependency versions in `requirements.txt`.

## Reproduction performed

- Verified the SHA-256 checksum of all four pinned source archives and rebuilt the complete project from those files.
- Audited 1,230 source games; retained 1,212. Exclusion reasons are recorded per game. All 82 Oklahoma City games are retained.
- Reconstructed 7,158 scoring chances and 100,211 live rebound chances.
- Refit both historical models and exported their held-out probabilities, calibration or evaluation summaries, specifications and game-bootstrap intervals.
- Rebuilt the indexed SQLite database and reconciled its three SQL views with the Python summaries.
- Executed all three notebooks: 12 code cells total, no error outputs or unexecuted code cells.
- Passed all 19 automated tests. Coverage includes free-throw sequence rejection, scoring conservation, prior shrinkage, outcome exclusion from predictors, game eligibility, unique event links, rebound timing and player identity, chronological separation, prediction-loss reproduction, league centering and SQL reconciliation.
- Separately checked all 213 retained and-one field-goal links across the six players: every linked field goal precedes its free throw.

## Article and figure checks

Nine charts were inspected visually, including full player names, axes, confidence intervals, legends and court coordinates. PNG and SVG versions are included. Each standalone HTML article embeds its three PNGs and contains no scripts or externally hosted images.

## Limits that remain

The public data audit establishes internal agreement between two record formats, not independent official verification. Eighteen games fail the audit. Free-throw and rebound exclusions change the denominators from official season statistics.

The models use fixed public-data features. Shot conversion lacks contest and shot-clock information; recovery lacks player positions and box-out assignments. Sampling intervals condition on the fitted models and do not include refitting uncertainty. Team comparisons are descriptive, with no claim of a causal coaching effect.

The articles use 2025–26 regular-season results. Future opponent availability, rotations and playoff pairings are unknown here. Review queues identify events; no film has been coded.
