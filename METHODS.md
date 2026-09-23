# Methods and limitations

## Source freeze and game audit

The source manifest pins archive commit `e829d4678be1e075f99e5d41a1c5f97089be446b`. A season suffix denotes its starting year: `2025` means 2025–26. Shot files cover 2023–24 through 2025–26; the event feed covers 2025–26. The studies use regular-season records, including eligible overtime events.

The common audit checks unique event ordering; period clocks; monotone score sequences without implausible single-event jumps; complete agreement between shot and event records on every field goal’s event ID, player, value and outcome; and reconciliation of field goals plus made free throws with both final scores. It retains 1,212 of 1,230 games. `results/game_audit.csv` records every exclusion and reason. All 82 Oklahoma City games survive. Source errors can still pass an internally consistent audit.

## Scoring chances

The six-player cohort contains Gilgeous-Alexander, Jalen Williams, Holmgren, Jokić, Edwards and Durant. Every eligible field goal begins as a scoring chance. Ordinary free throws are grouped by game, period, exact source clock and shooter. A supported trip has the complete numbered sequence and one preceding opposing foul at that clock. Single shooting-foul free throws attach to one related made field goal. Complete two- or three-shot trips without a related field goal become separate chances for supported foul types.

Shot clocks in the location feed have whole-second resolution, so the field-goal link permits less than one second of difference from the event clock. Ambiguous ordinary trips are excluded together with related field goals. Technical, flagrant, clear-path and other special free throws are excluded. Nonshooting trips reflect source foul labels, without reconstructed bonus status. This is not a possession count or official true-shooting percentage. Turnovers do not enter the denominator.

The six players contribute 7,158 retained scoring chances. Coverage is exported by player, including ordinary attempts retained, special attempts and excluded ordinary clusters. SGA’s Spurs split has only four games; its intervals should not be taken as evidence of a persistent opponent effect.

## Shot-location reference

Attempts at least 40 feet from the basket and inconsistent zone/value labels are removed. The classifier learns 2024–25 make outcomes using distance, absolute horizontal location, vertical location, shot value and the player’s previous-season two- or three-point make rate. That rate is shrunk toward the previous league rate using 100 prior attempts. Players without that history receive the league rate. The training priors use 2023–24; evaluation priors use 2024–25. Evaluation outcomes never enter predictors.

A fixed gradient-boosted specification uses 90 iterations, 15 maximum leaves, minimum leaf size 200, learning rate 0.06 and L2 regularization 5. Early stopping is disabled. The comparator uses 2024–25 broad-zone make rates. No hyperparameter search was conducted on the evaluation season. Validation uses log loss, Brier score, a calibration table and game-clustered paired loss differences.

Expected field-goal points equal predicted make probability times shot value. The residual is actual minus expected points. It conditions on a shot having occurred and excludes turnover, foul and possession-value effects. A residual is not a causal defense rating, and model uncertainty is not fully captured by the reported sampling intervals.

The spatial chart uses fixed five-foot cells from x = −25 to 25 feet and y = −5 to 40 feet. Its denominator includes all eligible attempts in each sample, even any coordinates outside the displayed grid. Cells are descriptive; no multiple-testing claim is made.

## Rebound chances

For each missed field goal, the next relevant event must be a player rebound for a known team within zero to eight game-clock seconds. Another shot, foul, free throw, turnover, jump ball or period boundary prevents a link. Team rebounds, unresolved records and longer delays are excluded. The retained 100,211 rows represent 87.8% of considered misses. This denominator differs from an official offensive-rebound percentage. Repeated misses within a possession may contribute separate chances.

The recovery model trains on 40,553 chances before January 1, 2026, and evaluates 59,658 on or after that date. Features are missed-shot distance, absolute horizontal and vertical location, shot value, remaining period time divided by 720 and period capped at five. Team and player identity are absent. The fixed classifier uses 70 iterations, nine maximum leaves, minimum leaf size 200, learning rate 0.06 and L2 regularization 5, with early stopping disabled. Its comparator is the early sample’s overall recovery rate.

The team comparison subtracts the later league’s mean residual from the team’s mean residual. This descriptive centering uses later outcomes, which is appropriate for a historical comparison; it is not part of the out-of-time prediction score or a prospective forecast. A joint game bootstrap resamples both terms together. Rebounder totals use player IDs to resolve full names; counts do not adjust for minutes or opportunities. The model cannot observe crash assignments, ball trajectories, player positions or box-outs, and it does not measure the transition cost of sending extra rebounders.

## Uncertainty and interpretation

Intervals are percentile intervals from 2,000 bootstrap resamples of games, preserving event clustering within a game. All randomness uses seed 20260908. These are exploratory opponent studies with fixed historical models; intervals are not adjusted for multiple comparisons or selection of the questions, and do not include model-refitting uncertainty. Repeated player or team dependence across games is not separately modeled.

Review queues contain event IDs and sample definitions, not watched or tagged film. They support locating sequences for a subsequent review. Current rosters, injuries and tactics require a separate refresh. No postseason performance or future playoff pairing is inferred from these regular-season estimates.
