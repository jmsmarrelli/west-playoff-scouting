# Decision brief: make the rebounding plan opponent-specific

AI-assisted synthesis of the existing study, October 22, 2026. This proposes a scouting review; it does not claim completed film coding or an implemented game plan.

**Decision:** allocate the first rebounding review block to Houston. Investigate the mechanism before prescribing which players should stay home or release.

![Western opponents compared with shot-context expectations and uncertainty](../figures/glass_adjusted.png)

**Evidence:** Houston recovers 34.1% of eligible player-rebound chances against a shot-context expectation of 26.9%. Its league-relative residual is +7.6 percentage points, with a 95% interval of +5.6 to +9.6, from 2,048 chances in 50 later-sample games. The 7.6-point figure is not simply 34.1 minus 26.9: it also subtracts the later league's −0.42-point residual. The chronological rebound model improves log loss from 0.57926 to 0.57401 on 59,658 later chances.

**Proposed next step:** stratify Houston misses by shot location and lineup, then code first contact, weak-side position, rebound trajectory and transition release responsibility. Review matched examples with and without an offensive rebound. Use the recorded rebounder counts to find examples, not to claim opportunity-adjusted individual skill. Refresh personnel before operational use; this is a 2025–26 study.

**What would change the recommendation:** a materially different result once team/dead-ball rebounds are accounted for, failure to transfer to a later season, or film showing that the apparent team effect is concentrated in a narrow personnel configuration. Player positioning and box-outs are absent from these data.

**Companion map:** the [OKC shot geography study](02_okc_shot_map.md) offers another review question. Its colors show differences in attempt frequency per 100 total field-goal attempts; they do not show defensive pressure, openness or shot value. Keep location and conversion claims separate.

Sources: [full rebounding study](03_western_glass.md), [team results](../results/glass_profiles.csv), [validation](../results/glass_validation.json), and [execution limits](../VALIDATION_CURRENT.md).
