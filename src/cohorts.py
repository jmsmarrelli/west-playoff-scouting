"""Audit league events and derive free-throw and live-rebound cohorts."""

import json, re
import numpy as np
import pandas as pd
from .common import ROOT, TEAM, shots, save_json

PLAYERS = {
    1628983: "Shai Gilgeous-Alexander",
    1631114: "Jalen Williams",
    1631096: "Chet Holmgren",
    203999: "Nikola Jokić",
    1630162: "Anthony Edwards",
    201142: "Kevin Durant",
}


def clock_seconds(value):
    m = re.fullmatch(r"PT(\d+)M([\d.]+)S", value)
    if not m:
        raise ValueError(value)
    return int(m[1]) * 60 + float(m[2])


def audit_games():
    s = shots(2025)
    sg = dict(tuple(s.groupby("GAME_ID")))
    raw = pd.read_csv(ROOT / "data/raw/nbastatsv3_2025.csv", low_memory=False)
    raw["seconds"] = raw.clock.map(clock_seconds)
    raw["teamId"] = np.where(
        raw.teamId.gt(0), raw.teamId, np.where(raw.personId.isin(TEAM), raw.personId, 0)
    )
    audits = []
    valid = []
    for game, g in raw.groupby("gameId"):
        if game not in sg:
            continue
        g = g.sort_values("actionId").copy()
        chart = sg[game]
        reasons = []
        if g.actionId.duplicated().any():
            reasons.append("duplicate order")
        for score in ["scoreHome", "scoreAway"]:
            g[score] = g[score].ffill().fillna(0)
            if g[score].diff().fillna(0).lt(0).any():
                reasons.append("score decreased")
            if g[score].diff().fillna(0).gt(4).any():
                reasons.append("score jump")
        for period, p in g.groupby("period"):
            if p.seconds.diff().fillna(0).gt(0.01).any():
                reasons.append("clock reversal")
            if (
                p.seconds.iloc[0] != (720 if period <= 4 else 300)
                or p.seconds.iloc[-1] != 0
            ):
                reasons.append("incomplete clock")
        fg = g[g.isFieldGoal.eq(1)]
        if fg.actionNumber.duplicated().any():
            reasons.append("duplicate FG event")
        else:
            j = fg.merge(
                chart,
                left_on="actionNumber",
                right_on="GAME_EVENT_ID",
                validate="one_to_one",
            )
            agree = (
                j.personId.eq(j.PLAYER_ID)
                & j.shotValue.eq(np.where(j.three, 3, 2))
                & j.shotResult.eq(np.where(j.made, "Made", "Missed"))
            )
            if len(j) != len(fg) or len(j) != len(chart) or not agree.all():
                reasons.append("shot feed disagreement")
        home = chart.HTM.iloc[0]
        away = chart.VTM.iloc[0]
        ft = g[
            g.actionType.eq("Free Throw")
            & ~g.description.str.startswith("MISS", na=False)
        ]
        for team, col in [(home, "scoreHome"), (away, "scoreAway")]:
            ident = next(k for k, v in TEAM.items() if v == team)
            points = (
                fg[fg.teamId.eq(ident)].shotValue
                * fg[fg.teamId.eq(ident)].shotResult.eq("Made")
            ).sum() + int(ft.teamId.eq(ident).sum())
            if points != g[col].iloc[-1]:
                reasons.append("scoring reconciliation")
        audits.append(
            dict(
                game_id=game,
                status="; ".join(sorted(set(reasons))) if reasons else "valid",
                home=home,
                away=away,
                date=str(chart.date.iloc[0].date()),
            )
        )
        if not reasons:
            g["date"] = str(chart.date.iloc[0].date())
            g["home"] = home
            g["away"] = away
            valid.append(g)
    pd.DataFrame(audits).to_csv(ROOT / "results/game_audit.csv", index=False)
    return pd.concat(valid), s


def trip_result(frame):
    parsed = frame.subType.str.extract(r"^Free Throw (\d) of (\d)$")
    if parsed.isna().any().any():
        return None
    n = parsed[1].astype(int).unique()
    if len(n) != 1 or parsed[0].astype(int).tolist() != list(range(1, int(n[0]) + 1)):
        return None
    return int(n[0]), int((~frame.description.str.startswith("MISS", na=False)).sum())


def derive_chances(events, s):
    targets = s[
        s.PLAYER_ID.isin(PLAYERS) & s.GAME_ID.isin(events.gameId.unique())
    ].copy()
    rows = {}
    for _, v in targets.iterrows():
        rows[(v.GAME_ID, v.GAME_EVENT_ID)] = dict(
            game_id=int(v.GAME_ID),
            event_id=int(v.GAME_EVENT_ID),
            player_id=int(v.PLAYER_ID),
            player=PLAYERS[v.PLAYER_ID],
            team=v.team,
            opponent=v.opponent,
            date=str(v.date.date()),
            period=int(v.PERIOD),
            channel="Field goal",
            fg_points=int(v.points),
            ft_points=0,
            points=int(v.points),
            zone=v.SHOT_ZONE_BASIC,
        )
    ft = events[
        events.actionType.eq("Free Throw") & events.personId.isin(PLAYERS)
    ].copy()
    clocks = {
        (game, period, clock): g
        for (game, period, clock), g in events.groupby(["gameId", "period", "clock"])
        if g.actionType.eq("Free Throw").any()
    }
    audit = []
    for (game, period, clock, pid), g in ft.groupby(
        ["gameId", "period", "clock", "personId"]
    ):
        g = g.sort_values("actionId")
        block = clocks[(game, period, clock)]
        normal = g[g.subType.str.match(r"^Free Throw \d of \d$", na=False)]
        status = "special free throw"
        kind = None
        result = None
        related = targets[
            targets.GAME_ID.eq(game)
            & targets.PERIOD.eq(period)
            & targets.PLAYER_ID.eq(pid)
            & (targets.MINUTES_REMAINING * 60 + targets.SECONDS_REMAINING)
            .sub(clock_seconds(clock))
            .abs()
            .lt(1)
        ]
        if len(normal):
            result = trip_result(normal)
            prior = block[
                block.actionId.lt(normal.actionId.iloc[0])
                & block.actionType.eq("Foul")
                & block.teamId.ne(normal.teamId.iloc[0])
            ]
            if result is None:
                status = "incomplete or repeated FT sequence"
            elif len(prior) != 1:
                status = "ambiguous foul link"
            else:
                n, makes = result
                foul = prior.iloc[0].subType
                if (
                    n == 1
                    and foul == "Shooting"
                    and len(related) == 1
                    and related.made.iloc[0] == 1
                ):
                    key = (game, int(related.GAME_EVENT_ID.iloc[0]))
                    rows[key].update(
                        ft_points=makes,
                        points=rows[key]["fg_points"] + makes,
                        channel="And-one",
                    )
                    status = "retained"
                    kind = "And-one"
                elif (
                    n in [2, 3]
                    and len(related) == 0
                    and foul in ["Shooting", "Personal", "Loose Ball", "Personal Take"]
                ):
                    kind = (
                        "Shooting-foul trip"
                        if foul == "Shooting"
                        else "Nonshooting-foul trip"
                    )
                    event = int(normal.actionNumber.iloc[0])
                    team = TEAM[int(normal.teamId.iloc[0])]
                    opp = (
                        normal.away.iloc[0]
                        if team == normal.home.iloc[0]
                        else normal.home.iloc[0]
                    )
                    rows[(game, event)] = dict(
                        game_id=int(game),
                        event_id=event,
                        player_id=int(pid),
                        player=PLAYERS[pid],
                        team=team,
                        opponent=opp,
                        date=normal.date.iloc[0],
                        period=int(period),
                        channel=kind,
                        fg_points=0,
                        ft_points=makes,
                        points=makes,
                        zone="Free-throw trip",
                    )
                    status = "retained"
                else:
                    status = "unsupported foul or overlapping field goal"
            if status != "retained":
                for _, v in related.iterrows():
                    rows.pop((game, int(v.GAME_EVENT_ID)), None)
        audit.append(
            dict(
                game_id=game,
                period=period,
                clock=clock,
                player_id=pid,
                player=PLAYERS[pid],
                status=status,
                channel=kind,
                normal_attempts=len(normal),
                special_attempts=len(g) - len(normal),
                normal_ft_points=int(
                    (~normal.description.str.startswith("MISS", na=False)).sum()
                ),
            )
        )
    pd.DataFrame(audit).to_csv(ROOT / "results/free_throw_audit.csv", index=False)
    d = pd.DataFrame(rows.values())
    d.to_csv(ROOT / "data/scoring_chances.csv.gz", index=False)
    return d


def derive_rebounds(events, s):
    lookup = s.set_index(["GAME_ID", "GAME_EVENT_ID"])
    names = s.drop_duplicates("PLAYER_ID").set_index("PLAYER_ID").PLAYER_NAME.to_dict()
    rows = []
    audit = []
    for (game, period), p in events.groupby(["gameId", "period"]):
        p = p.sort_values("actionId").reset_index(drop=True)
        for i, e in p[p.isFieldGoal.eq(1) & p.shotResult.eq("Missed")].iterrows():
            nxt = p.iloc[i + 1 :]
            relevant = nxt[
                nxt.actionType.isin(
                    ["Rebound", "Foul", "Free Throw", "Turnover", "Jump Ball", "period"]
                )
                | nxt.isFieldGoal.eq(1)
            ]
            status = "no resolved rebound"
            r = None
            if len(relevant):
                v = relevant.iloc[0]
                if (
                    v.actionType == "Rebound"
                    and v.personId > 0
                    and v.personId not in TEAM
                ):
                    if v.teamId in TEAM and 0 <= e.seconds - v.seconds <= 8:
                        r = v
                        status = "retained"
                    else:
                        status = "unresolved team or delayed rebound"
                elif v.actionType == "Rebound":
                    status = "team rebound"
                else:
                    status = "intervening " + str(v.actionType)
            audit.append(
                dict(game_id=int(game), event_id=int(e.actionNumber), status=status)
            )
            if r is None:
                continue
            shot = lookup.loc[(game, e.actionNumber)]
            row = dict(
                game_id=int(game),
                event_id=int(e.actionNumber),
                rebound_event_id=int(r.actionNumber),
                date=shot.date.strftime("%Y-%m-%d"),
                team=shot.team,
                opponent=shot.opponent,
                player_id=int(shot.PLAYER_ID),
                player=shot.PLAYER_NAME,
                rebounder_id=int(r.personId),
                rebounder=names.get(r.personId, str(r.playerName)),
                rebound_seconds=float(r.seconds),
                shot_order=int(e.actionId),
                rebound_order=int(r.actionId),
                oreb=int(r.teamId == e.teamId),
                seconds=float(e.seconds),
                period=int(period),
                distance=float(shot.SHOT_DISTANCE),
                x=float(shot.LOC_X) / 10,
                y=float(shot.LOC_Y) / 10,
                three=int(shot.three),
                zone=shot.SHOT_ZONE_BASIC,
            )
            rows.append(row)
    pd.DataFrame(audit).to_csv(ROOT / "results/rebound_event_audit.csv.gz", index=False)
    d = pd.DataFrame(rows)
    d.to_csv(ROOT / "data/rebound_chances.csv.gz", index=False)
    return d


def run():
    e, s = audit_games()
    c = derive_chances(e, s)
    r = derive_rebounds(e, s)
    summary = {
        "source_games": s.GAME_ID.nunique(),
        "audited_games": e.gameId.nunique(),
        "scoring_chances": len(c),
        "rebound_chances": len(r),
        "first_date": e.date.min(),
        "last_date": e.date.max(),
    }
    save_json("cohort_summary.json", summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
