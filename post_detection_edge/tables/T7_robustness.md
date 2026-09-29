# T7. Robustness of the headline signal and of any survivor

## R_2x@1h: `max_share > 0.2517 AND nko <= 5 AND entry_over_operator <= 3.55` (2x@1h)

### By period

| period | signal | rest | base |
|---|---|---|---|
| TRAIN 21-29 Aug | 69.4 % (25/36) [53.1-82.0] | 32.7 % (70/214) [26.8-39.3] | 38.0 % (95/250) [32.2-44.2] |
| VALIDATION 30 Aug-14 Sep | 42.6 % (26/61) [31.0-55.1] | 32.8 % (150/458) [28.6-37.2] | 33.9 % (176/519) [30.0-38.1] |
| TEST 15-29 Sep | 35.5 % (27/76) [25.7-46.7] | 38.3 % (173/452) [33.9-42.8] | 37.9 % (200/528) [33.8-42.1] |
| August (all splits) | 60.0 % (30/50) [46.2-72.4] | 30.0 % (90/300) [25.1-35.4] | 34.3 % (120/350) [29.5-39.4] |
| September (all splits) | 39.0 % (48/123) [30.9-47.9] | 36.8 % (303/824) [33.5-40.1] | 37.1 % (351/947) [34.0-40.2] |
| June, July | no data: the detector started on 2026-08-21 | | |

### By operator cluster (TEST)

76 signal alerts with an observed window, from 28 clusters; the largest cluster holds 25 (33 %). Hits by cluster: 11/25, 0/8, 0/7, 2/4, 1/3, 1/2, 0/2, 2/2.

Leave-one-cluster-out signal rate on TEST: min 31.4 %, max 39.7 % over 28 clusters removed one at a time (base TEST 37.9 %).
Without the largest cluster: 31.4 % (16/51) [20.3-45.0].

### Threshold stability on TEST (descriptive, after the lock)

| condition varied | -10 % | -5 % | locked | +5 % | +10 % |
|---|---|---|---|---|---|
| max_share > 0.2517 | 34.1 % (29/85) [24.9-44.7] | 34.1 % (29/85) [24.9-44.7] | 35.5 % (27/76) [25.7-46.7] | 46.9 % (15/32) [30.9-63.6] | 35.7 % (5/14) [16.3-61.2] |
| nko <= 5 | 33.8 % (22/65) [23.5-46.0] | 33.8 % (22/65) [23.5-46.0] | 35.5 % (27/76) [25.7-46.7] | 35.5 % (27/76) [25.7-46.7] | 35.5 % (27/76) [25.7-46.7] |
| entry_over_operator <= 3.55 | 39.1 % (9/23) [22.2-59.2] | 33.3 % (13/39) [20.6-49.0] | 35.5 % (27/76) [25.7-46.7] | 37.6 % (50/133) [29.8-46.1] | 34.4 % (65/189) [28.0-41.4] |

## L_2x@15m: `ridge logistic score >= TRAIN 80th percentile` (2x@15m)

### By period

| period | signal | rest | base |
|---|---|---|---|
| TRAIN 21-29 Aug | 49.1 % (27/55) [36.4-61.9] | 25.3 % (55/217) [20.0-31.5] | 30.1 % (82/272) [25.0-35.8] |
| VALIDATION 30 Aug-14 Sep | 35.6 % (63/177) [28.9-42.9] | 26.6 % (119/447) [22.7-30.9] | 29.2 % (182/624) [25.7-32.9] |
| TEST 15-29 Sep | 45.7 % (75/164) [38.3-53.4] | 25.6 % (113/442) [21.7-29.8] | 31.0 % (188/606) [27.5-34.8] |
| August (all splits) | 44.7 % (34/76) [34.1-55.9] | 23.4 % (71/304) [18.9-28.4] | 27.6 % (105/380) [23.4-32.3] |
| September (all splits) | 40.9 % (131/320) [35.7-46.4] | 26.9 % (216/802) [24.0-30.1] | 30.9 % (347/1122) [28.3-33.7] |
| June, July | no data: the detector started on 2026-08-21 | | |

### By operator cluster (TEST)

164 signal alerts with an observed window, from 38 clusters; the largest cluster holds 41 (25 %). Hits by cluster: 21/41, 10/17, 3/11, 3/9, 2/6, 3/6, 3/5, 2/5.

Leave-one-cluster-out signal rate on TEST: min 43.9 %, max 47.1 % over 38 clusters removed one at a time (base TEST 31.0 %).
Without the largest cluster: 43.9 % (54/123) [35.4-52.7].

## ANSEM

Mint 9cRCn9rGT8V2imeM2BaKs13yhMEais3ruM3rPvTGpump, created 2026-06-16 21:05:48 UTC. Not in the snapshot: the detector started on 2026-08-21, and its creation block (two buyers, one of them ~84.7 SOL) fails the detector's definition (at least 4 snipers of >= 5 SOL). With ANSEM and without ANSEM are therefore the same numbers. It is not injected into any split.
