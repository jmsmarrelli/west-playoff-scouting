"""Event, chronology, accounting and validation checks on the delivered cohorts."""

import json
import sqlite3
import unittest
import numpy as np
import pandas as pd
from src.common import ROOT, TEAM
from src.cohorts import clock_seconds, trip_result
from src.shot_model import add_prior, features, clean
from src.statistics import loss
from src import data


class ResearchChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scoring = pd.read_csv(ROOT / "data/scoring_chances.csv.gz")
        cls.rebounds = pd.read_csv(ROOT / "data/rebound_chances.csv.gz")
        cls.shots = pd.read_csv(ROOT / "data/contender_shots.csv.gz")
        cls.held = pd.read_csv(ROOT / "data/glass_holdout.csv.gz")
        cls.evaluation = pd.read_csv(ROOT / "data/shot_validation_rows.csv.gz")
        cls.audit = pd.read_csv(ROOT / "results/game_audit.csv")

    def test_fractional_clock(self):
        self.assertAlmostEqual(clock_seconds("PT1M02.75S"), 62.75)
        with self.assertRaises(ValueError):
            clock_seconds("1:02")

    def test_complete_trip_counts_makes(self):
        d = pd.DataFrame(
            {
                "subType": ["Free Throw 1 of 2", "Free Throw 2 of 2"],
                "description": ["MISS Player Free Throw", "Player Free Throw"],
            }
        )
        self.assertEqual(trip_result(d), (2, 1))

    def test_incomplete_or_duplicate_trip_rejected(self):
        for types in [
            ["Free Throw 2 of 2"],
            ["Free Throw 1 of 2", "Free Throw 1 of 2"],
            ["Free Throw 1 of 2", "Free Throw 2 of 3"],
        ]:
            d = pd.DataFrame({"subType": types, "description": ["Made"] * len(types)})
            self.assertIsNone(trip_result(d))

    def test_special_trip_rejected(self):
        self.assertIsNone(
            trip_result(
                pd.DataFrame(
                    {"subType": ["Free Throw Technical"], "description": ["Made"]}
                )
            )
        )

    def test_prior_shrinkage_and_unseen_player(self):
        prior = pd.DataFrame(
            {"PLAYER_ID": [1, 1, 2, 2], "three": [False] * 4, "made": [1, 0, 1, 1]}
        )
        now = pd.DataFrame({"PLAYER_ID": [1, 3], "three": [False, False]})
        actual = add_prior(now, prior).prior.to_numpy()
        np.testing.assert_allclose(actual, [(1 + 100 * 0.75) / 102, 0.75])

    def test_current_outcome_is_not_a_feature(self):
        d = self.shots.head(30).copy()
        original = features(d)
        d["made"] = 1 - d.made
        d["points"] = 999
        np.testing.assert_equal(features(d), original)

    def test_heaves_and_zone_conflicts_removed(self):
        d = pd.DataFrame(
            {
                "SHOT_DISTANCE": [39, 40, 20, 3],
                "SHOT_ZONE_BASIC": [
                    "Above the Break 3",
                    "Above the Break 3",
                    "Mid-Range",
                    "Restricted Area",
                ],
                "three": [True, True, True, False],
            }
        )
        self.assertEqual(clean(d).index.tolist(), [0, 3])

    def test_all_derived_events_use_audited_games(self):
        valid = set(self.audit.loc[self.audit.status.eq("valid"), "game_id"])
        for d, col in [
            (self.scoring, "game_id"),
            (self.rebounds, "game_id"),
            (self.shots, "GAME_ID"),
            (self.evaluation, "game_id"),
        ]:
            self.assertTrue(set(d[col]).issubset(valid))
        self.assertEqual(len(valid), 1212)

    def test_chance_and_rebound_keys_unique(self):
        for d in [self.scoring, self.rebounds, self.held]:
            self.assertFalse(d.duplicated(["game_id", "event_id"]).any())
        self.assertFalse(
            self.rebounds.duplicated(["game_id", "rebound_event_id"]).any()
        )
        self.assertFalse(self.shots.duplicated(["GAME_ID", "GAME_EVENT_ID"]).any())

    def test_rebound_sequence_and_player_identity(self):
        d = self.rebounds
        self.assertTrue((d.rebound_order > d.shot_order).all())
        self.assertTrue((d.seconds - d.rebound_seconds).between(0, 8).all())
        self.assertFalse(d.rebounder_id.isin(TEAM).any())
        self.assertTrue(d.rebounder_id.gt(0).all())
        self.assertTrue(d.oreb.isin([0, 1]).all())

    def test_scoring_point_conservation(self):
        d = self.scoring
        np.testing.assert_array_equal(d.points, d.fg_points + d.ft_points)
        self.assertTrue(d.points.between(0, 4).all())
        self.assertTrue(d.loc[d.channel.eq("Field goal"), "ft_points"].eq(0).all())
        self.assertTrue(d.loc[d.channel.str.endswith("trip"), "fg_points"].eq(0).all())
        self.assertTrue(d.loc[d.channel.eq("And-one"), "fg_points"].isin([2, 3]).all())

    def test_retained_free_throw_points_reconcile(self):
        a = pd.read_csv(ROOT / "results/free_throw_audit.csv").query(
            "status == 'retained'"
        )
        pd.testing.assert_series_equal(
            a.groupby("player").normal_ft_points.sum().sort_index(),
            self.scoring.groupby("player").ft_points.sum().sort_index(),
            check_names=False,
        )

    def test_foul_channel_denominators(self):
        a = pd.read_csv(ROOT / "results/foul_channels.csv")
        np.testing.assert_allclose(a.groupby("player").share.sum(), 1)
        pd.testing.assert_series_equal(
            a.groupby("player").chances.sum().sort_index(),
            self.scoring.groupby("player").size().sort_index(),
            check_names=False,
        )

    def test_shot_expected_value_and_residual(self):
        d = self.shots
        np.testing.assert_allclose(
            d.expected_points, d.probability * np.where(d.three, 3, 2)
        )
        np.testing.assert_allclose(d.residual, d.points - d.expected_points, atol=1e-14)
        self.assertTrue(d.probability.between(0, 1).all())

    def test_shot_validation_from_frozen_predictions(self):
        d = self.evaluation
        v = json.loads((ROOT / "results/shot_validation.json").read_text())
        self.assertEqual(len(d), v["test_attempts"])
        self.assertAlmostEqual(loss(d.made, d.probability).mean(), v["model_logloss"])
        self.assertAlmostEqual(loss(d.made, d.baseline).mean(), v["baseline_logloss"])
        np.testing.assert_allclose(
            d.loss_difference,
            loss(d.made, d.probability) - loss(d.made, d.baseline),
            atol=1e-14,
        )
        self.assertLess(v["upper"], 0)

    def test_rebound_time_split_and_baseline(self):
        d = self.held
        train = self.rebounds[self.rebounds.date < "2026-01-01"]
        self.assertTrue(d.date.ge("2026-01-01").all())
        self.assertEqual(len(d) + len(train), len(self.rebounds))
        self.assertFalse(
            set(zip(d.game_id, d.event_id)) & set(zip(train.game_id, train.event_id))
        )
        np.testing.assert_allclose(d.baseline, train.oreb.mean())

    def test_glass_validation_from_frozen_predictions(self):
        d = self.held
        v = json.loads((ROOT / "results/glass_validation.json").read_text())
        self.assertEqual(len(d), v["test_chances"])
        self.assertAlmostEqual(loss(d.oreb, d.probability).mean(), v["model_logloss"])
        self.assertAlmostEqual(loss(d.oreb, d.baseline).mean(), v["baseline_logloss"])
        np.testing.assert_allclose(d.residual, d.oreb - d.probability, atol=1e-14)
        self.assertLess(v["upper"], 0)

    def test_glass_league_centering(self):
        d = self.held
        p = pd.read_csv(ROOT / "results/glass_profiles.csv")
        for row in p.itertuples():
            g = d[d.team.eq(row.team)]
            self.assertAlmostEqual(
                row.league_relative_residual, g.residual.mean() - d.residual.mean()
            )
            self.assertEqual(row.offensive_rebounds, g.oreb.sum())

    def test_sql_reconciles_independent_groupings(self):
        data.database()
        with sqlite3.connect(ROOT / "data/research.sqlite") as con:
            total = con.execute(
                "SELECT SUM(chances),SUM(points) FROM scoring_channels"
            ).fetchone()
            self.assertEqual(total, (len(self.scoring), int(self.scoring.points.sum())))
            zones = pd.read_sql_query("SELECT * FROM defense_zone_summary", con)
            ref = pd.read_csv(ROOT / "results/defense_zone_profiles.csv")
            j = zones.merge(ref, on=["defense", "zone"], validate="one_to_one")
            self.assertEqual(len(j), len(zones))
            np.testing.assert_allclose(j.actual_x, j.actual_y)
            g = pd.read_sql_query("SELECT * FROM glass_team_summary ORDER BY team", con)
            ref = pd.read_csv(ROOT / "results/glass_profiles.csv").sort_values("team")
            np.testing.assert_allclose(
                g.league_relative_residual, ref.league_relative_residual
            )


if __name__ == "__main__":
    unittest.main()
