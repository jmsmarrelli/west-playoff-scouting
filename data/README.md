# Data dictionary

All bundled tables are derived from the pinned archives in `source_manifest.json`. Raw archives are retrieved with `python -m src.data fetch`. NBA game and event IDs are stored as integers; add leading zeroes when an external viewer expects a ten-digit NBA game ID.

| File | Row definition | Important fields |
| --- | --- | --- |
| `scoring_chances.csv.gz` | One supported scoring chance for a selected player | `game_id`, `event_id`, player/team/opponent, date, period, channel, `fg_points`, `ft_points`, total `points` |
| `rebound_chances.csv.gz` | One missed FG linked to a player rebound | Shot and rebound IDs/order, `seconds`, `rebound_seconds`, shooter and rebounder IDs/names, offense/opponent, binary `oreb`, location and shot value |
| `contender_shots.csv.gz` | One eligible FG against OKC, DEN, HOU or MIN | Original game/event/player IDs, offense `team`, defending `opponent`, zone, raw coordinates, `prior`, make `probability`, zone `baseline`, points and residual |
| `shot_validation_rows.csv.gz` | One league-wide held-out FG prediction | `game_id`, binary `made`, model and baseline probabilities, model-minus-baseline `loss_difference` |
| `glass_holdout.csv.gz` | One later-sample rebound chance | Rebound cohort fields plus predicted recovery probability, baseline, residual, paired loss difference and broad zone group |

`oreb` equals one when the rebounding team is the shooting team. `three` indicates a three-point field goal attempt. Shot-feed `LOC_X` and `LOC_Y` are in tenths of feet; rebound `x` and `y` are in feet. Remaining `seconds` refers to the period clock, not the shot clock. `event_id` in the scoring cohort identifies the field goal or the first free throw of a foul-only trip.

A residual is actual outcome minus predicted outcome: FG points for the shot model and a zero/one recovery indicator for the rebound model. The published rebound comparison additionally subtracts the later league’s mean residual. See `METHODS.md` at the repository root for the exact denominators and split dates.

The `results/` directory contains game, free-throw and rebound exclusion audits; player/channel and team/zone aggregates; model specifications and evaluations; review queues; and exported SQL views. Review queues contain identifiers to locate plays, not completed film observations.
