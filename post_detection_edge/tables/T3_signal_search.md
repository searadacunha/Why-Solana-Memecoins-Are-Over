# T3. Signal search in TRAIN, selection in VALIDATION (TEST sealed)

Regenerate: `python3 post_detection_edge/code/an_40_signals.py`. Rates are complete-case (observed windows), entry at P0 (spot). Wilson 95 % intervals. A rule's N is the number of alerts it selects with an observed window.

## Target 2x@5m

Base rate: TRAIN 14.0 % (39/279) [10.4-18.5], VALIDATION 18.2 % (121/665) [15.4-21.3].
Rule search: 487 atoms, 161030 rules evaluated, 59633 distinct rules with TRAIN support >= 20.

### Rules with a high TRAIN hit rate

| TRAIN rate | rules | of which N >= 40 | median N | best VAL rate among them (N) | VAL rate pooled over all of them |
|---|---:|---:|---:|---|---|
| 90-100 % | 0 | 0 | - | - | - |
| 80-90 % | 0 | 0 | - | - | - |
| 70-80 % | 0 | 0 | - | - | - |
| >= 60 % | 5 | 0 | 20 | 12.6 % (87) | 18.0 % (27/150) [12.7-24.9] (alert-rule pairs, overlapping) |

Largest-N rules at >= 60 % in TRAIN (the full list is in derived/rules_2x@5m.json):

| rule | N train | TP | FP | TRAIN rate | N val | VAL rate | TEST rate |
|---|---:|---:|---:|---|---:|---|---|
| ticket_median > 20.12 AND max_share <= 0.2535 AND p0 <= 3.854e-07 SOL | 21 | 13 | 8 | 61.9 % | 17 | 23.5 % (4/17) [9.6-47.3] | sealed |
| ticket_median > 20.12 AND hhi <= 0.25 AND p0 <= 3.854e-07 SOL | 20 | 13 | 7 | 65.0 % | 13 | 7.7 % (1/13) [1.4-33.3] | sealed |
| ticket_mean <= 19.84 AND ticket_min > 6.453 AND dow == 5 | 20 | 12 | 8 | 60.0 % | 14 | 28.6 % (4/14) [11.7-54.6] | sealed |
| max_share > 0.2516 AND hhi <= 0.25 AND paquet_max <= 1 | 20 | 12 | 8 | 60.0 % | 19 | 36.8 % (7/19) [19.1-59.0] | sealed |
| ticket_max > 20.2 AND entry_over_operator <= 3.96 AND config_prev > 3 | 20 | 12 | 8 | 60.0 % | 87 | 12.6 % (11/87) [7.2-21.2] | sealed |

### The 50 best TRAIN rules (Wilson lower bound), re-measured in VALIDATION

| # | rule | N train | TRAIN rate | N val | VAL rate | VAL lower bound |
|---:|---|---:|---|---:|---|---:|
| 1 | ticket_std <= 5.288 AND ticket_max <= 20.38 AND amorce <= 0.04444 | 23 | 56.5 % (13/23) [36.8-74.4] | 117 | 30.8 % (36/117) [23.1-39.6] | 0.231 |
| 2 | ticket_min > 6.453 AND ticket_max <= 20.38 AND amorce <= 0.04444 | 21 | 57.1 % (12/21) [36.5-75.5] | 117 | 30.8 % (36/117) [23.1-39.6] | 0.231 |
| 3 | ticket_mean > 20.18 AND max_share <= 0.2535 AND amorce > 0.009875 | 20 | 55.0 % (11/20) [34.2-74.2] | 36 | 30.6 % (11/36) [18.0-46.9] | 0.180 |
| 4 | snipe_sol <= 84.91 AND ticket_mean > 20.18 AND max_share <= 0.2535 | 24 | 54.2 % (13/24) [35.1-72.1] | 37 | 29.7 % (11/37) [17.5-45.8] | 0.175 |
| 5 | ticket_std <= 0.569 AND amorce <= 0.04938 AND age_alert_s <= 12.3 | 30 | 53.3 % (16/30) [36.1-69.8] | 108 | 20.4 % (22/108) [13.9-28.9] | 0.139 |
| 6 | supply_part <= 0.7819 AND amorce <= 0.04938 AND age_alert_s <= 12.3 | 27 | 55.6 % (15/27) [37.3-72.4] | 142 | 18.3 % (26/142) [12.8-25.5] | 0.128 |
| 7 | snipe_sol <= 81.29 AND amorce <= 0.04938 AND age_alert_s <= 12.3 | 28 | 53.6 % (15/28) [35.8-70.5] | 142 | 18.3 % (26/142) [12.8-25.5] | 0.128 |
| 8 | ticket_std <= 0.569 AND amorce <= 0.04938 AND age_alert_s <= 13.5 | 41 | 48.8 % (20/41) [34.3-63.5] | 140 | 17.9 % (25/140) [12.4-25.0] | 0.124 |
| 9 | supply_part <= 0.7861 AND amorce <= 0.04938 AND age_alert_s <= 12.3 | 31 | 51.6 % (16/31) [34.8-68.0] | 151 | 17.2 % (26/151) [12.0-24.0] | 0.120 |
| 10 | supply_part <= 0.7819 AND amorce <= 0.04938 AND age_alert_s <= 13.5 | 35 | 54.3 % (19/35) [38.2-69.5] | 175 | 16.6 % (29/175) [11.8-22.8] | 0.118 |
| 11 | snipe_sol <= 81.29 AND amorce <= 0.04938 AND age_alert_s <= 13.5 | 37 | 51.4 % (19/37) [35.9-66.6] | 176 | 16.5 % (29/176) [11.7-22.7] | 0.117 |
| 12 | supply_part <= 0.7861 AND amorce <= 0.04938 AND age_alert_s <= 13.5 | 41 | 48.8 % (20/41) [34.3-63.5] | 186 | 16.1 % (30/186) [11.5-22.1] | 0.115 |
| 13 | supply_part <= 0.7809 AND amorce <= 0.04938 AND age_alert_s <= 13.5 | 25 | 56.0 % (14/25) [37.1-73.3] | 170 | 15.9 % (27/170) [11.2-22.1] | 0.112 |
| 14 | entry_over_operator <= 3.743 AND n_candidates_prev_60m > 14 AND config_prev > 3 | 20 | 55.0 % (11/20) [34.2-74.2] | 82 | 17.1 % (14/82) [10.5-26.6] | 0.105 |
| 15 | amorce <= 0.04938 AND age_alert_s <= 13.5 AND complete_at_block == False | 21 | 57.1 % (12/21) [36.5-75.5] | 99 | 16.2 % (16/99) [10.2-24.7] | 0.102 |
| 16 | entry_over_operator <= 3.743 AND age_alert_s > 7.8 AND config_prev > 3 | 20 | 55.0 % (11/20) [34.2-74.2] | 77 | 16.9 % (13/77) [10.1-26.8] | 0.101 |
| 17 | n_snipers <= 4 AND entry_over_operator <= 3.743 AND config_prev > 3 | 20 | 55.0 % (11/20) [34.2-74.2] | 87 | 16.1 % (14/87) [9.8-25.2] | 0.098 |
| 18 | max_share > 0.2516 AND p0 <= 3.854e-07 SOL AND config_prev > 3 | 20 | 55.0 % (11/20) [34.2-74.2] | 70 | 15.7 % (11/70) [9.0-26.0] | 0.090 |
| 19 | max_share > 0.2516 AND entry_over_operator <= 3.96 AND config_prev > 3 | 22 | 54.5 % (12/22) [34.7-73.1] | 86 | 14.0 % (12/86) [8.2-22.8] | 0.082 |
| 20 | max_share > 0.2516 AND p0 <= 4.098e-07 SOL AND config_prev > 3 | 21 | 57.1 % (12/21) [36.5-75.5] | 88 | 13.6 % (12/88) [8.0-22.3] | 0.080 |

**Locked for TEST: `ticket_std <= 5.288 AND ticket_max <= 20.38 AND amorce <= 0.04444`** (TRAIN 56.5 % (13/23) [36.8-74.4], VALIDATION 30.8 % (36/117) [23.1-39.6]).

### Ridge logistic regression

Penalty chosen on VALIDATION AUC among [0.1, 1.0, 10.0, 100.0]: lambda = 100. AUC TRAIN 0.722, VALIDATION 0.635. Largest standardised coefficients: paquet_max -0.06, log10_p0 -0.06, log10_mc_usd -0.06, age_alert_s -0.05, round_share +0.05, ticket_mean -0.05.
Signal = score >= TRAIN 80th percentile: TRAIN 22.8 % (13/57) [13.8-35.2], VALIDATION 24.3 % (25/103) [17.0-33.4].

### Shallow tree

Depth chosen on VALIDATION AUC: 2 (AUC VALIDATION 0.624). Best TRAIN leaf: `log10_p0 <= -0.309 (standardised) AND config_prev > 0.131 (standardised)`: TRAIN 47.8 % (11/23) [29.2-67.0], VALIDATION 21.5 % (20/93) [14.4-30.9].

## Target 2x@15m

Base rate: TRAIN 30.1 % (82/272) [25.0-35.8], VALIDATION 29.2 % (182/624) [25.7-32.9].
Rule search: 487 atoms, 160537 rules evaluated, 69276 distinct rules with TRAIN support >= 20.

### Rules with a high TRAIN hit rate

| TRAIN rate | rules | of which N >= 40 | median N | best VAL rate among them (N) | VAL rate pooled over all of them |
|---|---:|---:|---:|---|---|
| 90-100 % | 0 | 0 | - | - | - |
| >= 80 % | 8 | 0 | 20 | 32.4 % (34) | 27.4 % (57/208) [21.8-33.8] (alert-rule pairs, overlapping) |
| >= 70 % | 197 | 0 | 22 | 50.0 % (32) | 29.9 % (2144/7169) [28.9-31.0] (alert-rule pairs, overlapping) |
| >= 60 % | 2626 | 349 | 27 | 61.9 % (42) | 33.0 % (40176/121684) [32.8-33.3] (alert-rule pairs, overlapping) |

Largest-N rules at >= 60 % in TRAIN (the full list is in derived/rules_2x@15m.json):

| rule | N train | TP | FP | TRAIN rate | N val | VAL rate | TEST rate |
|---|---:|---:|---:|---|---:|---|---|
| ticket_max > 20.18 AND fail_ratio <= 0.9 AND p0 <= 3.663e-07 SOL | 66 | 40 | 26 | 60.6 % | 83 | 28.9 % (24/83) [20.3-39.4] | sealed |
| fail_ratio <= 0.9 AND entry_over_operator <= 3.625 AND sniper_reuse_max <= 3 | 58 | 36 | 22 | 62.1 % | 110 | 29.1 % (32/110) [21.4-38.2] | sealed |
| ticket_std > 0.296 AND ticket_min > 6.451 AND p0 <= 3.663e-07 SOL | 58 | 35 | 23 | 60.3 % | 114 | 39.5 % (45/114) [31.0-48.6] | sealed |
| ticket_median > 19.16 AND p0 <= 3.663e-07 SOL AND sniper_reuse_max <= 3 | 57 | 36 | 21 | 63.2 % | 66 | 25.8 % (17/66) [16.7-37.4] | sealed |
| p0 <= 3.663e-07 SOL AND sniper_reuse_max <= 3 AND p0_source == pool | 57 | 35 | 22 | 61.4 % | 92 | 34.8 % (32/92) [25.8-44.9] | sealed |
| hhi <= 0.2504 AND p0 <= 3.663e-07 SOL AND sniper_reuse_max <= 3 | 56 | 34 | 22 | 60.7 % | 85 | 27.1 % (23/85) [18.8-37.3] | sealed |
| supply_part <= 0.7819 AND p0 <= 3.663e-07 SOL AND p0_source == pool | 56 | 34 | 22 | 60.7 % | 109 | 42.2 % (46/109) [33.4-51.6] | sealed |
| max_share <= 0.2658 AND p0 <= 3.663e-07 SOL AND sniper_reuse_max <= 3 | 55 | 34 | 21 | 61.8 % | 84 | 26.2 % (22/84) [18.0-36.5] | sealed |
| ticket_min > 6.451 AND p0 <= 3.663e-07 SOL AND n_alerts_prev_60m > 2 | 55 | 33 | 22 | 60.0 % | 122 | 40.2 % (49/122) [31.9-49.0] | sealed |
| ticket_max > 20.18 AND p0 <= 3.76e-07 SOL AND age_alert_s <= 12.3 | 55 | 33 | 22 | 60.0 % | 70 | 32.9 % (23/70) [23.0-44.5] | sealed |
| ticket_max > 20.18 AND p0 <= 3.862e-07 SOL AND sniper_reuse_max <= 0 | 55 | 33 | 22 | 60.0 % | 90 | 14.4 % (13/90) [8.6-23.2] | sealed |
| ticket_mean > 16.99 AND p0 <= 3.663e-07 SOL AND n_alerts_prev_60m > 2 | 55 | 33 | 22 | 60.0 % | 115 | 38.3 % (44/115) [29.9-47.4] | sealed |
| supply_part <= 0.7819 AND ticket_median > 19.16 AND p0 <= 3.663e-07 SOL | 54 | 34 | 20 | 63.0 % | 74 | 32.4 % (24/74) [22.9-43.7] | sealed |
| core_cv <= 0.05949 AND p0 <= 3.663e-07 SOL AND sniper_reuse_max <= 3 | 54 | 33 | 21 | 61.1 % | 85 | 27.1 % (23/85) [18.8-37.3] | sealed |
| ticket_max <= 21.62 AND p0 <= 3.663e-07 SOL AND sniper_reuse_max <= 3 | 54 | 33 | 21 | 61.1 % | 98 | 30.6 % (30/98) [22.4-40.3] | sealed |

### The 50 best TRAIN rules (Wilson lower bound), re-measured in VALIDATION

| # | rule | N train | TRAIN rate | N val | VAL rate | VAL lower bound |
|---:|---|---:|---|---:|---|---:|
| 1 | max_share > 0.2516 AND nko <= 5 AND p0 <= 3.588e-07 SOL | 26 | 73.1 % (19/26) [53.9-86.3] | 63 | 34.9 % (22/63) [24.3-47.2] | 0.243 |
| 2 | ticket_min > 6.451 AND extra_buyers <= 1 AND p0 <= 3.663e-07 SOL | 22 | 77.3 % (17/22) [56.6-89.9] | 37 | 37.8 % (14/37) [24.1-53.9] | 0.241 |
| 3 | mc_usd <= 36298 AND sniper_reuse_max <= 3 AND complete_at_block == True | 25 | 76.0 % (19/25) [56.6-88.5] | 34 | 38.2 % (13/34) [23.9-55.0] | 0.239 |
| 4 | hhi > 0.2501 AND nko <= 5 AND p0 <= 3.663e-07 SOL | 24 | 75.0 % (18/24) [55.1-88.0] | 72 | 33.3 % (24/72) [23.5-44.8] | 0.235 |
| 5 | nko <= 5 AND entry_over_operator <= 3.548 AND sniper_reuse_max <= 3 | 35 | 71.4 % (25/35) [54.9-83.7] | 66 | 33.3 % (22/66) [23.2-45.3] | 0.232 |
| 6 | extra_buyers <= 1 AND p0 <= 3.663e-07 SOL AND entry_over_operator > 3.197 | 21 | 76.2 % (16/21) [54.9-89.4] | 36 | 36.1 % (13/36) [22.5-52.4] | 0.225 |
| 7 | ticket_min > 6.451 AND ntx <= 7 AND p0 <= 3.663e-07 SOL | 32 | 71.9 % (23/32) [54.6-84.4] | 50 | 34.0 % (17/50) [22.4-47.8] | 0.224 |
| 8 | ntx <= 8 AND nko <= 5 AND entry_over_operator <= 3.548 | 26 | 73.1 % (19/26) [53.9-86.3] | 62 | 32.3 % (20/62) [22.0-44.6] | 0.220 |
| 9 | p0 <= 3.76e-07 SOL AND age_alert_s <= 12.3 AND sniper_reuse_max <= 3 | 37 | 70.3 % (26/37) [54.2-82.5] | 88 | 29.5 % (26/88) [21.0-39.8] | 0.210 |
| 10 | nko <= 6 AND p0 <= 3.588e-07 SOL AND sniper_reuse_max <= 3 | 29 | 72.4 % (21/29) [54.3-85.3] | 62 | 30.6 % (19/62) [20.6-43.0] | 0.206 |
| 11 | p0 <= 3.862e-07 SOL AND age_alert_s <= 12.3 AND sniper_reuse_max <= 3 | 47 | 68.1 % (32/47) [53.8-79.6] | 111 | 27.9 % (31/111) [20.4-36.9] | 0.204 |
| 12 | ticket_mean > 16.99 AND amorce <= 0.04345 AND p0 <= 3.588e-07 SOL | 22 | 77.3 % (17/22) [56.6-89.9] | 51 | 31.4 % (16/51) [20.3-45.0] | 0.203 |
| 13 | entry_over_operator <= 3.625 AND age_alert_s <= 12.3 AND sniper_reuse_max <= 3 | 38 | 71.1 % (27/38) [55.2-83.0] | 72 | 29.2 % (21/72) [19.9-40.5] | 0.199 |
| 14 | nko <= 5 AND p0 <= 3.588e-07 SOL AND sniper_reuse_max <= 3 | 25 | 76.0 % (19/25) [56.6-88.5] | 56 | 30.4 % (17/56) [19.9-43.3] | 0.199 |
| 15 | p0 <= 3.663e-07 SOL AND age_alert_s <= 12.3 AND sniper_reuse_max <= 3 | 32 | 71.9 % (23/32) [54.6-84.4] | 58 | 29.3 % (17/58) [19.2-42.0] | 0.192 |
| 16 | mc_usd <= 36298 AND age_alert_s <= 12.3 AND sniper_reuse_max <= 3 | 28 | 82.1 % (23/28) [64.4-92.1] | 34 | 32.4 % (11/34) [19.1-49.2] | 0.191 |
| 17 | ticket_min > 6.451 AND ntx <= 7 AND entry_over_operator <= 3.548 | 30 | 73.3 % (22/30) [55.6-85.8] | 50 | 30.0 % (15/50) [19.1-43.8] | 0.191 |
| 18 | ticket_min > 6.451 AND extra_buyers <= 1 AND entry_over_operator <= 3.548 | 23 | 78.3 % (18/23) [58.1-90.3] | 36 | 30.6 % (11/36) [18.0-46.9] | 0.180 |
| 19 | p0 <= 3.588e-07 SOL AND age_alert_s <= 12.3 AND sniper_reuse_max <= 3 | 24 | 79.2 % (19/24) [59.5-90.8] | 43 | 27.9 % (12/43) [16.7-42.7] | 0.167 |
| 20 | ntx <= 7 AND p0 <= 3.663e-07 SOL AND entry_over_operator > 3.197 | 28 | 75.0 % (21/28) [56.6-87.3] | 43 | 27.9 % (12/43) [16.7-42.7] | 0.167 |

**Locked for TEST: `max_share > 0.2516 AND nko <= 5 AND p0 <= 3.588e-07 SOL`** (TRAIN 73.1 % (19/26) [53.9-86.3], VALIDATION 34.9 % (22/63) [24.3-47.2]).

### Ridge logistic regression

Penalty chosen on VALIDATION AUC among [0.1, 1.0, 10.0, 100.0]: lambda = 100. AUC TRAIN 0.698, VALIDATION 0.643. Largest standardised coefficients: log10_p0 -0.11, log10_mc_usd -0.11, paquet_max -0.07, sniper_reuse_max -0.06, age_alert_s -0.06, max_share -0.06.
Signal = score >= TRAIN 80th percentile: TRAIN 49.1 % (27/55) [36.4-61.9], VALIDATION 35.6 % (63/177) [28.9-42.9].

### Shallow tree

Depth chosen on VALIDATION AUC: 2 (AUC VALIDATION 0.637). Best TRAIN leaf: `log10_p0 <= -0.36 (standardised) AND max_share > -0.447 (standardised)`: TRAIN 55.4 % (41/74) [44.1-66.2], VALIDATION 37.6 % (53/141) [30.0-45.8].

## Target 2x@1h

Base rate: TRAIN 38.0 % (95/250) [32.2-44.2], VALIDATION 33.9 % (176/519) [30.0-38.1].
Rule search: 487 atoms, 160952 rules evaluated, 60351 distinct rules with TRAIN support >= 20.

### Rules with a high TRAIN hit rate

| TRAIN rate | rules | of which N >= 40 | median N | best VAL rate among them (N) | VAL rate pooled over all of them |
|---|---:|---:|---:|---|---|
| 90-100 % | 0 | 0 | - | - | - |
| >= 80 % | 2 | 0 | 20 | 38.5 % (39) | 34.9 % (29/83) [25.6-45.7] (alert-rule pairs, overlapping) |
| >= 70 % | 202 | 0 | 21 | 47.6 % (42) | 30.5 % (3341/10945) [29.7-31.4] (alert-rule pairs, overlapping) |
| >= 60 % | 2447 | 120 | 26 | 56.8 % (37) | 31.5 % (49541/157134) [31.3-31.8] (alert-rule pairs, overlapping) |

Largest-N rules at >= 60 % in TRAIN (the full list is in derived/rules_2x@1h.json):

| rule | N train | TP | FP | TRAIN rate | N val | VAL rate | TEST rate |
|---|---:|---:|---:|---|---:|---|---|
| p0 <= 1.324e-06 SOL AND sniper_reuse_max <= 8 AND config_prev > 2 | 58 | 35 | 23 | 60.3 % | 156 | 32.1 % (50/156) [25.2-39.7] | sealed |
| p0 <= 1.324e-06 SOL AND n_alerts_prev_60m > 1 AND config_prev > 2 | 56 | 34 | 22 | 60.7 % | 169 | 34.3 % (58/169) [27.6-41.8] | sealed |
| entry_over_operator <= 11.97 AND n_alerts_prev_60m > 1 AND config_prev > 2 | 55 | 33 | 22 | 60.0 % | 169 | 34.3 % (58/169) [27.6-41.8] | sealed |
| p0 <= 3.666e-07 SOL AND entry_over_operator <= 3.622 AND sniper_reuse_max <= 3 | 53 | 32 | 21 | 60.4 % | 75 | 33.3 % (25/75) [23.7-44.6] | sealed |
| p0 <= 1.324e-06 SOL AND n_candidates_prev_60m > 14 AND config_prev > 2 | 53 | 32 | 21 | 60.4 % | 160 | 34.4 % (55/160) [27.5-42.0] | sealed |
| nko <= 7 AND entry_over_operator <= 3.622 AND sniper_reuse_max <= 3 | 53 | 32 | 21 | 60.4 % | 83 | 30.1 % (25/83) [21.3-40.7] | sealed |
| hhi > 0.25 AND fail_ratio <= 0.9 AND p0 <= 3.666e-07 SOL | 51 | 32 | 19 | 62.7 % | 94 | 37.2 % (35/94) [28.1-47.3] | sealed |
| p0 <= 3.666e-07 SOL AND age_alert_s <= 16.1 AND sniper_reuse_max <= 3 | 51 | 31 | 20 | 60.8 % | 81 | 33.3 % (27/81) [24.0-44.1] | sealed |
| fail_ratio <= 0.9 AND entry_over_operator <= 3.622 AND sniper_reuse_max <= 3 | 50 | 32 | 18 | 64.0 % | 85 | 29.4 % (25/85) [20.8-39.8] | sealed |
| hhi > 0.25 AND round_share <= 0 AND p0 <= 3.666e-07 SOL | 50 | 31 | 19 | 62.0 % | 87 | 36.8 % (32/87) [27.4-47.3] | sealed |
| ticket_median > 19.2 AND p0 <= 3.666e-07 SOL AND sniper_reuse_max <= 3 | 50 | 31 | 19 | 62.0 % | 50 | 28.0 % (14/50) [17.5-41.7] | sealed |
| ticket_max > 20.18 AND p0 <= 3.666e-07 SOL AND sniper_reuse_max <= 3 | 50 | 31 | 19 | 62.0 % | 51 | 31.4 % (16/51) [20.3-45.0] | sealed |
| entry_over_operator <= 3.622 AND n_alerts_prev_60m > 1 AND sniper_reuse_max <= 3 | 50 | 30 | 20 | 60.0 % | 89 | 32.6 % (29/89) [23.7-42.9] | sealed |
| hhi > 0.25 AND p0 <= 3.666e-07 SOL AND mc_usd > 32920 | 49 | 30 | 19 | 61.2 % | 92 | 38.0 % (35/92) [28.8-48.3] | sealed |
| p0 <= 3.666e-07 SOL AND sniper_reuse_max <= 3 AND p0_source == pool | 49 | 30 | 19 | 61.2 % | 75 | 36.0 % (27/75) [26.1-47.3] | sealed |

### The 50 best TRAIN rules (Wilson lower bound), re-measured in VALIDATION

| # | rule | N train | TRAIN rate | N val | VAL rate | VAL lower bound |
|---:|---|---:|---|---:|---|---:|
| 1 | max_share > 0.2517 AND nko <= 5 AND entry_over_operator <= 3.55 | 36 | 69.4 % (25/36) [53.1-82.0] | 61 | 42.6 % (26/61) [31.0-55.1] | 0.310 |
| 2 | core_cv > 0.01976 AND nko <= 5 AND p0 <= 3.591e-07 SOL | 23 | 73.9 % (17/23) [53.5-87.5] | 41 | 41.5 % (17/41) [27.8-56.6] | 0.278 |
| 3 | hhi > 0.25 AND nko <= 5 AND p0 <= 3.666e-07 SOL | 36 | 69.4 % (25/36) [53.1-82.0] | 74 | 36.5 % (27/74) [26.4-47.9] | 0.264 |
| 4 | nko <= 5 AND entry_over_operator <= 3.55 AND sniper_reuse_max <= 2 | 27 | 74.1 % (20/27) [55.3-86.8] | 46 | 39.1 % (18/46) [26.4-53.5] | 0.264 |
| 5 | core_cv > 0.02933 AND nko <= 6 AND p0 <= 3.666e-07 SOL | 20 | 75.0 % (15/20) [53.1-88.8] | 63 | 36.5 % (23/63) [25.7-48.9] | 0.257 |
| 6 | max_share > 0.2549 AND nko <= 5 AND p0 <= 3.591e-07 SOL | 20 | 80.0 % (16/20) [58.4-91.9] | 39 | 38.5 % (15/39) [24.9-54.1] | 0.249 |
| 7 | nko <= 5 AND entry_over_operator <= 3.55 AND sniper_reuse_max <= 3 | 33 | 72.7 % (24/33) [55.8-84.9] | 52 | 36.5 % (19/52) [24.8-50.1] | 0.248 |
| 8 | max_share > 0.2517 AND nko <= 5 AND p0 <= 3.591e-07 SOL | 24 | 75.0 % (18/24) [55.1-88.0] | 49 | 36.7 % (18/49) [24.7-50.7] | 0.247 |
| 9 | core_cv > 0.01976 AND amorce <= 0.04345 AND p0 <= 3.591e-07 SOL | 20 | 75.0 % (15/20) [53.1-88.8] | 35 | 37.1 % (13/35) [23.2-53.7] | 0.232 |
| 10 | fail_ratio <= 0.75 AND p0 <= 3.591e-07 SOL AND sniper_reuse_max <= 2 | 23 | 73.9 % (17/23) [53.5-87.5] | 49 | 34.7 % (17/49) [22.9-48.7] | 0.229 |
| 11 | nko <= 6 AND p0 <= 3.591e-07 SOL AND sniper_reuse_max <= 2 | 22 | 77.3 % (17/22) [56.6-89.9] | 46 | 34.8 % (16/46) [22.7-49.2] | 0.227 |
| 12 | ntx <= 8 AND nko <= 5 AND entry_over_operator <= 3.55 | 24 | 79.2 % (19/24) [59.5-90.8] | 50 | 34.0 % (17/50) [22.4-47.8] | 0.224 |
| 13 | supply_part <= 0.7819 AND entry_over_operator <= 3.961 AND config_prev > 2 | 29 | 72.4 % (21/29) [54.3-85.3] | 83 | 31.3 % (26/83) [22.4-41.9] | 0.224 |
| 14 | nko <= 5 AND entry_over_operator <= 3.961 AND config_prev > 2 | 20 | 75.0 % (15/20) [53.1-88.8] | 84 | 31.0 % (26/84) [22.1-41.5] | 0.221 |
| 15 | nko <= 5 AND p0 <= 3.591e-07 SOL AND sniper_reuse_max <= 3 | 22 | 77.3 % (17/22) [56.6-89.9] | 44 | 34.1 % (15/44) [21.9-48.9] | 0.219 |
| 16 | ticket_max > 20.18 AND nko <= 5 AND p0 <= 3.591e-07 SOL | 30 | 73.3 % (22/30) [55.6-85.8] | 35 | 34.3 % (12/35) [20.8-50.8] | 0.208 |
| 17 | n_alerts_prev_60m > 1 AND sniper_reuse_max <= 2 AND config_prev > 4 | 31 | 71.0 % (22/31) [53.4-83.9] | 70 | 30.0 % (21/70) [20.5-41.5] | 0.205 |
| 18 | ticket_mean > 16.99 AND amorce <= 0.04345 AND p0 <= 3.591e-07 SOL | 20 | 80.0 % (16/20) [58.4-91.9] | 44 | 31.8 % (14/44) [20.0-46.6] | 0.200 |
| 19 | mc_usd <= 81621 AND n_alerts_prev_60m > 2 AND config_prev > 4 | 20 | 75.0 % (15/20) [53.1-88.8] | 76 | 28.9 % (22/76) [20.0-40.0] | 0.200 |
| 20 | n_alerts_prev_60m > 2 AND sniper_reuse_max <= 2 AND config_prev > 4 | 20 | 75.0 % (15/20) [53.1-88.8] | 60 | 30.0 % (18/60) [19.9-42.5] | 0.199 |

**Locked for TEST: `max_share > 0.2517 AND nko <= 5 AND entry_over_operator <= 3.55`** (TRAIN 69.4 % (25/36) [53.1-82.0], VALIDATION 42.6 % (26/61) [31.0-55.1]).

### Ridge logistic regression

Penalty chosen on VALIDATION AUC among [0.1, 1.0, 10.0, 100.0]: lambda = 100. AUC TRAIN 0.658, VALIDATION 0.529. Largest standardised coefficients: config_prev +0.09, log10_p0 -0.09, log10_mc_usd -0.08, age_alert_s -0.08, sniper_reuse_max -0.07, creator_prev -0.05.
Signal = score >= TRAIN 80th percentile: TRAIN 54.9 % (28/51) [41.4-67.7], VALIDATION 35.4 % (57/161) [28.4-43.1].

### Shallow tree

Depth chosen on VALIDATION AUC: 2 (AUC VALIDATION 0.502). Best TRAIN leaf: `config_prev > 0.408 (standardised) AND log10_mc_usd <= 0.238 (standardised)`: TRAIN 69.6 % (16/23) [49.1-84.4], VALIDATION 29.6 % (24/81) [20.8-40.3].

## Hypotheses specified before this study (target 2x@1h)

| hypothesis | TRAIN signal | TRAIN rest | VALIDATION signal | VALIDATION rest |
|---|---|---|---|---|
| H1_actor_grouped: actor == grouped (paquet_max >= 2) | 37.9 % (25/66) [27.1-49.9] | 38.0 % (70/184) [31.3-45.2] | 23.7 % (33/139) [17.4-31.5] | 37.6 % (143/380) [32.9-42.6] |
| H2_mc_below_60k: market cap at P0 < 60 000 USD | 39.4 % (74/188) [32.7-46.5] | 33.9 % (21/62) [23.3-46.3] | 37.5 % (145/387) [32.8-42.4] | 23.5 % (31/132) [17.1-31.4] |
| H2b_mc_40k_60k: 40 000 <= market cap at P0 < 60 000 USD | 46.2 % (6/13) [23.2-70.9] | 37.6 % (89/237) [31.6-43.9] | 40.7 % (50/123) [32.4-49.5] | 31.8 % (126/396) [27.4-36.6] |

## Search budget

Atoms (conditions) built: 1461. Rules evaluated: 482519. Models fitted (logistic + trees): 18. Tree thresholds scanned: 7291. Univariate screen (an_30): see derived/univariate_summary.json. Locked signals: 12.
