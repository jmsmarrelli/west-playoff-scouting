-- Every row is an eligible event or scoring chance, not a possession.
DROP VIEW IF EXISTS scoring_channels;
CREATE VIEW scoring_channels AS
SELECT player, team, channel, COUNT(*) AS chances,
       COUNT(DISTINCT game_id) AS games,
       SUM(points) AS points, SUM(ft_points) AS ft_points
FROM scoring_chances GROUP BY player, team, channel;

DROP VIEW IF EXISTS defense_zone_summary;
CREATE VIEW defense_zone_summary AS
SELECT opponent AS defense, zone, COUNT(*) AS attempts,
       AVG(points) AS actual, AVG(expected_points) AS expected,
       AVG(residual) AS residual
FROM contender_shots GROUP BY opponent, zone;

DROP VIEW IF EXISTS glass_team_summary;
CREATE VIEW glass_team_summary AS
SELECT team, COUNT(*) AS chances, COUNT(DISTINCT game_id) AS games,
       SUM(oreb) AS offensive_rebounds, AVG(oreb) AS raw_rate,
       AVG(probability) AS expected_rate,
       AVG(residual) - (SELECT AVG(residual) FROM glass_holdout)
           AS league_relative_residual
FROM glass_holdout
WHERE team IN ('OKC','DEN','HOU','MIN') GROUP BY team;
