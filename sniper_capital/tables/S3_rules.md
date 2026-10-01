# S3. Threshold rules per family (TRAIN choice, VALIDATION once) and their controls

Metric: Wilson 95 % lower bound of the TRAIN rate minus the TRAIN base of the launches where the variable is OBSERVED, at least 40 launches. Labeled launches: TRAIN 896, VALIDATION 606.

## 1 ticket / capital: `0.8487 < a_mean <= 0.8872`

- Rules evaluated: 438. TRAIN metric +0.074, permutation p 0.005 (null best: median +0.013, 95th +0.050).
- Coverage: a_mean OBSERVED on 896 of 896 TRAIN and 606 of 606 VALIDATION labeled launches.
- TRAIN 39.3 % (35/89) [29.8-49.7] against a base of 22.4 %; VALIDATION 20.0 % (10/50) [11.2-33.0] against 26.4 %, lower bound 11.2 %: does not hold.
- Other labels, VALIDATION selection: 2x 5 min 12.0 % (6/50), 2x 1 h 31.2 % (15/48), 1.5x 15 min 32.0 % (16/50), 3x 15 min 4.0 % (2/50).
- Lift beyond premium: +3.1 pts [-11.8, +27.5] (CI reaches 0).
- Lift beyond actor: -0.9 pts [-15.3, +24.3] (CI reaches 0).
- Lift beyond snipers: -5.0 pts [-23.0, +29.2] (CI reaches 0).
- Lift beyond premium + actor + snipers: +3.0 pts [-12.1, +27.4] (CI reaches 0).
- Largest operator: 46 % of the VALIDATION selection. Without it: 37.0 % (10/27) [21.5-55.8] against 27.8 % (does not hold). Single-operator launches only: 38.5 % (10/26) [22.4-57.5] against 33.0 % (does not hold).
- VALIDATION halves: 15.4 % (4/26) [6.1-33.5] against 24.4 %; 25.0 % (6/24) [12.0-44.9] against 28.4 %.
- Logistic, signal alone: VALIDATION ROC-AUC 0.486, PR-AUC 0.255, gain from the signal -0.014 [-0.070, +0.038].
- Logistic, + premium: VALIDATION ROC-AUC 0.592, PR-AUC 0.304, gain from the signal -0.045 [-0.149, +0.025].
- Logistic, + operator: VALIDATION ROC-AUC 0.636, PR-AUC 0.339, gain from the signal +0.004 [-0.014, +0.028].
- Logistic, + premium + operator: VALIDATION ROC-AUC 0.641, PR-AUC 0.342, gain from the signal +0.004 [-0.018, +0.030].
- Mantel-Haenszel odds ratio of the signal within premium tercile x actor, VALIDATION: 1.20 [0.46, 2.83] (3 strata with both groups).

**Classification: TRAIN OVERFIT**

## 2 capital after / before: `0.1005 < g_mean <= 0.1403`

- Rules evaluated: 216. TRAIN metric +0.070, permutation p 0.005 (null best: median +0.008, 95th +0.040).
- Coverage: g_mean OBSERVED on 896 of 896 TRAIN and 606 of 606 VALIDATION labeled launches.
- TRAIN 38.9 % (35/90) [29.5-49.2] against a base of 22.4 %; VALIDATION 20.8 % (10/48) [11.7-34.3] against 26.4 %, lower bound 11.7 %: does not hold.
- Other labels, VALIDATION selection: 2x 5 min 12.5 % (6/48), 2x 1 h 32.6 % (15/46), 1.5x 15 min 31.2 % (15/48), 3x 15 min 4.2 % (2/48).
- Lift beyond premium: +4.3 pts [-10.1, +32.4] (CI reaches 0).
- Lift beyond actor: +0.5 pts [-13.7, +28.8] (CI reaches 0).
- Lift beyond snipers: -4.1 pts [-22.6, +34.4] (CI reaches 0).
- Lift beyond premium + actor + snipers: +4.2 pts [-10.2, +32.2] (CI reaches 0).
- Largest operator: 48 % of the VALIDATION selection. Without it: 40.0 % (10/25) [23.4-59.3] against 27.8 % (does not hold). Single-operator launches only: 41.7 % (10/24) [24.5-61.2] against 33.0 % (does not hold).
- VALIDATION halves: 16.0 % (4/25) [6.4-34.7] against 24.4 %; 26.1 % (6/23) [12.5-46.5] against 28.4 %.
- Logistic, signal alone: VALIDATION ROC-AUC 0.489, PR-AUC 0.256, gain from the signal -0.011 [-0.068, +0.040].
- Logistic, + premium: VALIDATION ROC-AUC 0.594, PR-AUC 0.308, gain from the signal -0.042 [-0.146, +0.027].
- Logistic, + operator: VALIDATION ROC-AUC 0.638, PR-AUC 0.343, gain from the signal +0.006 [-0.011, +0.030].
- Logistic, + premium + operator: VALIDATION ROC-AUC 0.643, PR-AUC 0.348, gain from the signal +0.006 [-0.015, +0.033].
- Mantel-Haenszel odds ratio of the signal within premium tercile x actor, VALIDATION: 1.36 [0.53, 3.22] (3 strata with both groups).

**Classification: TRAIN OVERFIT**

## 3 ticket / last funding: `0.8481 < tl_med <= 0.8866`

- Rules evaluated: 180. TRAIN metric +0.078, permutation p 0.000 (null best: median +0.002, 95th +0.042).
- Coverage: tl_med OBSERVED on 827 of 896 TRAIN and 536 of 606 VALIDATION labeled launches.
- TRAIN 39.0 % (32/82) [29.2-49.8] against a base of 21.4 %; VALIDATION 29.7 % (22/74) [20.5-40.9] against 24.1 %, lower bound 20.5 %: does not hold.
- Other labels, VALIDATION selection: 2x 5 min 12.2 % (9/74), 2x 1 h 25.8 % (17/66), 1.5x 15 min 47.3 % (35/74), 3x 15 min 9.5 % (7/74).
- Lift beyond premium: +1.7 pts [-11.2, +15.5] (CI reaches 0).
- Lift beyond actor: +0.5 pts [-10.7, +12.3] (CI reaches 0).
- Lift beyond snipers: +6.6 pts [-4.9, +19.0] (CI reaches 0).
- Lift beyond premium + actor + snipers: +0.7 pts [-11.9, +14.4] (CI reaches 0).
- Largest operator: 19 % of the VALIDATION selection. Without it: 30.0 % (18/60) [19.9-42.5] against 23.9 % (does not hold). Single-operator launches only: 29.7 % (22/74) [20.5-40.9] against 31.1 % (does not hold).
- VALIDATION halves: 36.7 % (11/30) [21.9-54.5] against 22.0 %; 25.0 % (11/44) [14.6-39.4] against 26.1 %.
- Logistic, signal alone: VALIDATION ROC-AUC 0.521, PR-AUC 0.273, gain from the signal +0.021 [-0.016, +0.061].
- Logistic, + premium: VALIDATION ROC-AUC 0.643, PR-AUC 0.301, gain from the signal +0.004 [-0.027, +0.038].
- Logistic, + operator: VALIDATION ROC-AUC 0.640, PR-AUC 0.317, gain from the signal -0.004 [-0.030, +0.024].
- Logistic, + premium + operator: VALIDATION ROC-AUC 0.643, PR-AUC 0.301, gain from the signal +0.004 [-0.027, +0.038].
- Mantel-Haenszel odds ratio of the signal within premium tercile x actor, VALIDATION: 0.92 [0.48, 1.59] (3 strata with both groups).

**Classification: TRAIN OVERFIT**

## 4 time since last funding: `102 < age_med <= 646`

- Rules evaluated: 191. TRAIN metric +0.023, permutation p 0.105 (null best: median -0.006, 95th +0.038).
- Coverage: age_med OBSERVED on 827 of 896 TRAIN and 536 of 606 VALIDATION labeled launches.
- TRAIN 27.8 % (115/413) [23.7-32.4] against a base of 21.4 %; VALIDATION 29.8 % (79/265) [24.6-35.6] against 24.1 %, lower bound 24.6 %: holds.
- Other labels, VALIDATION selection: 2x 5 min 13.6 % (36/265), 2x 1 h 29.6 % (69/233), 1.5x 15 min 48.7 % (129/265), 3x 15 min 9.4 % (25/265).
- Lift beyond premium: +1.7 pts [-5.5, +9.7] (CI reaches 0).
- Lift beyond actor: +1.7 pts [-5.6, +9.1] (CI reaches 0).
- Lift beyond snipers: +11.4 pts [+1.7, +20.4].
- Lift beyond premium + actor + snipers: +0.9 pts [-6.2, +8.9] (CI reaches 0).
- Largest operator: 10 % of the VALIDATION selection. Without it: 28.9 % (69/239) [23.5-34.9] against 22.3 % (holds). Single-operator launches only: 30.3 % (79/261) [25.0-36.1] against 31.1 % (does not hold).
- VALIDATION halves: 28.4 % (38/134) [21.4-36.5] against 22.0 %; 31.3 % (41/131) [24.0-39.7] against 26.1 %.
- Logistic, signal alone: VALIDATION ROC-AUC 0.578, PR-AUC 0.282, gain from the signal +0.078 [+0.012, +0.145].
- Logistic, + premium: VALIDATION ROC-AUC 0.630, PR-AUC 0.293, gain from the signal -0.009 [-0.050, +0.031].
- Logistic, + operator: VALIDATION ROC-AUC 0.636, PR-AUC 0.301, gain from the signal -0.008 [-0.038, +0.027].
- Logistic, + premium + operator: VALIDATION ROC-AUC 0.634, PR-AUC 0.296, gain from the signal -0.005 [-0.043, +0.035].
- Mantel-Haenszel odds ratio of the signal within premium tercile x actor, VALIDATION: 0.87 [0.56, 1.41] (6 strata with both groups).

**Classification: NO SIGNAL**

## 5 last funding amount: `amt_hhi <= 0.25`

- Rules evaluated: 330. TRAIN metric +0.061, permutation p 0.020 (null best: median +0.010, 95th +0.052).
- Coverage: amt_hhi OBSERVED on 827 of 896 TRAIN and 536 of 606 VALIDATION labeled launches.
- TRAIN 34.3 % (57/166) [27.5-41.8] against a base of 21.4 %; VALIDATION 29.7 % (27/91) [21.3-39.7] against 24.1 %, lower bound 21.3 %: does not hold.
- Other labels, VALIDATION selection: 2x 5 min 13.2 % (12/91), 2x 1 h 26.6 % (21/79), 1.5x 15 min 52.7 % (48/91), 3x 15 min 6.6 % (6/91).
- Lift beyond premium: +0.3 pts [-12.0, +13.1] (CI reaches 0).
- Lift beyond actor: +1.0 pts [-11.1, +13.3] (CI reaches 0).
- Lift beyond snipers: +6.7 pts [-5.8, +19.7] (CI reaches 0).
- Lift beyond premium + actor + snipers: +0.0 pts [-12.3, +12.6] (CI reaches 0).
- Largest operator: 13 % of the VALIDATION selection. Without it: 34.2 % (27/79) [24.7-45.2] against 24.6 % (holds). Single-operator launches only: 30.3 % (27/89) [21.8-40.5] against 31.1 % (does not hold).
- VALIDATION halves: 35.3 % (18/51) [23.6-49.0] against 22.0 %; 22.5 % (9/40) [12.3-37.5] against 26.1 %.
- Logistic, signal alone: VALIDATION ROC-AUC 0.526, PR-AUC 0.272, gain from the signal +0.026 [-0.027, +0.072].
- Logistic, + premium: VALIDATION ROC-AUC 0.640, PR-AUC 0.306, gain from the signal +0.002 [-0.036, +0.035].
- Logistic, + operator: VALIDATION ROC-AUC 0.642, PR-AUC 0.318, gain from the signal -0.003 [-0.041, +0.027].
- Logistic, + premium + operator: VALIDATION ROC-AUC 0.643, PR-AUC 0.308, gain from the signal +0.004 [-0.032, +0.037].
- Mantel-Haenszel odds ratio of the signal within premium tercile x actor, VALIDATION: 0.93 [0.54, 1.53] (5 strata with both groups).

**Classification: TRAIN OVERFIT**

## 6 funding about the ticket: `fit_share_90_100 <= 0.25`

- Rules evaluated: 33. TRAIN metric +0.025, permutation p 0.015 (null best: median -0.020, 95th +0.010).
- Coverage: fit_share_90_100 OBSERVED on 827 of 896 TRAIN and 536 of 606 VALIDATION labeled launches.
- TRAIN 27.5 % (145/527) [23.9-31.5] against a base of 21.4 %; VALIDATION 33.2 % (119/358) [28.6-38.3] against 24.1 %, lower bound 28.6 %: holds.
- Other labels, VALIDATION selection: 2x 5 min 15.1 % (54/358), 2x 1 h 33.1 % (102/308), 1.5x 15 min 52.5 % (188/358), 3x 15 min 12.3 % (44/358).
- Lift beyond premium: +13.4 pts [+4.2, +22.7].
- Lift beyond actor: +12.8 pts [+4.5, +21.2].
- Lift beyond snipers: +27.6 pts [+19.0, +35.4].
- Lift beyond premium + actor + snipers: +12.2 pts [+3.0, +21.6].
- Largest operator: 9 % of the VALIDATION selection. Without it: 30.9 % (101/327) [26.1-36.1] against 22.3 % (holds). Single-operator launches only: 33.1 % (117/353) [28.4-38.2] against 31.1 % (does not hold).
- VALIDATION halves: 35.0 % (56/160) [28.0-42.7] against 22.0 %; 31.8 % (63/198) [25.7-38.6] against 26.1 %.
- Logistic, signal alone: VALIDATION ROC-AUC 0.668, PR-AUC 0.331, gain from the signal +0.168 [+0.096, +0.236].
- Logistic, + premium: VALIDATION ROC-AUC 0.675, PR-AUC 0.328, gain from the signal +0.037 [-0.011, +0.093].
- Logistic, + operator: VALIDATION ROC-AUC 0.674, PR-AUC 0.331, gain from the signal +0.030 [+0.001, +0.067].
- Logistic, + premium + operator: VALIDATION ROC-AUC 0.677, PR-AUC 0.331, gain from the signal +0.037 [-0.008, +0.090].
- Mantel-Haenszel odds ratio of the signal within premium tercile x actor, VALIDATION: 2.63 [1.44, 7.35] (5 strata with both groups).

**Classification: PRICE/OPERATOR CONFOUNDED**

## 7 snipers by fraction risked: `n_a_ge90 <= 2`

- Rules evaluated: 35. TRAIN metric +0.029, permutation p 0.010 (null best: median -0.020, 95th +0.009).
- Coverage: n_a_ge90 OBSERVED on 896 of 896 TRAIN and 606 of 606 VALIDATION labeled launches.
- TRAIN 28.8 % (181/629) [25.4-32.4] against a base of 22.4 %; VALIDATION 35.0 % (153/437) [30.7-39.6] against 26.4 %, lower bound 30.7 %: holds.
- Other labels, VALIDATION selection: 2x 5 min 16.7 % (73/437), 2x 1 h 34.8 % (131/376), 1.5x 15 min 52.4 % (229/437), 3x 15 min 14.2 % (62/437).
- Lift beyond premium: +14.4 pts [+5.1, +23.0].
- Lift beyond actor: +14.3 pts [+4.4, +22.5].
- Lift beyond snipers: +28.7 pts [+20.9, +34.6].
- Lift beyond premium + actor + snipers: +13.7 pts [+4.4, +21.9].
- Largest operator: 21 % of the VALIDATION selection. Without it: 31.8 % (110/346) [27.1-36.9] against 23.0 % (holds). Single-operator launches only: 34.9 % (150/430) [30.5-39.5] against 33.0 % (does not hold).
- VALIDATION halves: 36.6 % (71/194) [30.1-43.6] against 24.4 %; 33.7 % (82/243) [28.1-39.9] against 28.4 %.
- Logistic, signal alone: VALIDATION ROC-AUC 0.660, PR-AUC 0.353, gain from the signal +0.160 [+0.098, +0.228].
- Logistic, + premium: VALIDATION ROC-AUC 0.670, PR-AUC 0.357, gain from the signal +0.033 [-0.008, +0.079].
- Logistic, + operator: VALIDATION ROC-AUC 0.661, PR-AUC 0.349, gain from the signal +0.029 [+0.002, +0.060].
- Logistic, + premium + operator: VALIDATION ROC-AUC 0.669, PR-AUC 0.357, gain from the signal +0.032 [-0.008, +0.077].
- Mantel-Haenszel odds ratio of the signal within premium tercile x actor, VALIDATION: 4.38 [1.95, 19.31] (4 strata with both groups).

**Classification: PRICE/OPERATOR CONFOUNDED**

## 8 topology: `gen_share_hub > 0`

- Rules evaluated: 42. TRAIN metric +0.022, permutation p 0.035 (null best: median -0.018, 95th +0.018).
- Coverage: gen_share_hub OBSERVED on 734 of 896 TRAIN and 531 of 606 VALIDATION labeled launches.
- TRAIN 27.0 % (141/523) [23.3-30.9] against a base of 21.1 %; VALIDATION 30.9 % (122/395) [26.5-35.6] against 23.9 %, lower bound 26.5 %: holds.
- Other labels, VALIDATION selection: 2x 5 min 13.4 % (53/395), 2x 1 h 30.2 % (103/341), 1.5x 15 min 49.1 % (194/395), 3x 15 min 10.9 % (43/395).
- Lift beyond premium: +6.3 pts [-0.6, +12.8] (CI reaches 0).
- Lift beyond actor: +7.0 pts [+0.0, +13.2].
- Lift beyond snipers: +27.2 pts [+19.5, +33.6].
- Lift beyond premium + actor + snipers: +5.6 pts [-1.2, +12.1] (CI reaches 0).
- Largest operator: 9 % of the VALIDATION selection. Without it: 30.4 % (109/359) [25.8-35.3] against 23.0 % (holds). Single-operator launches only: 30.8 % (121/393) [26.4-35.5] against 30.7 % (does not hold).
- VALIDATION halves: 28.4 % (52/183) [22.4-35.3] against 21.1 %; 33.0 % (70/212) [27.0-39.6] against 26.7 %.
- Logistic, signal alone: VALIDATION ROC-AUC 0.642, PR-AUC 0.286, gain from the signal +0.142 [+0.073, +0.218].
- Logistic, + premium: VALIDATION ROC-AUC 0.636, PR-AUC 0.293, gain from the signal +0.001 [-0.010, +0.010].
- Logistic, + operator: VALIDATION ROC-AUC 0.642, PR-AUC 0.286, gain from the signal +0.002 [-0.000, +0.006].
- Logistic, + premium + operator: VALIDATION ROC-AUC 0.636, PR-AUC 0.293, gain from the signal +0.002 [-0.000, +0.005].
- Mantel-Haenszel odds ratio of the signal within premium tercile x actor, VALIDATION: 2.83 [0.00, 5.76] (5 strata with both groups).

**Classification: PRICE/OPERATOR CONFOUNDED**

## 9 other aggregates: `hhi_ticket <= 0.25`

- Rules evaluated: 371. TRAIN metric +0.063, permutation p 0.015 (null best: median +0.013, 95th +0.046).
- Coverage: hhi_ticket OBSERVED on 896 of 896 TRAIN and 606 of 606 VALIDATION labeled launches.
- TRAIN 35.4 % (64/181) [28.8-42.6] against a base of 22.4 %; VALIDATION 34.2 % (52/152) [27.1-42.1] against 26.4 %, lower bound 27.1 %: holds.
- Other labels, VALIDATION selection: 2x 5 min 17.1 % (26/152), 2x 1 h 31.8 % (42/132), 1.5x 15 min 49.3 % (75/152), 3x 15 min 17.1 % (26/152).
- Lift beyond premium: -2.1 pts [-12.3, +12.1] (CI reaches 0).
- Lift beyond actor: +5.1 pts [-6.5, +14.4] (CI reaches 0).
- Lift beyond snipers: +3.7 pts [-5.3, +13.6] (CI reaches 0).
- Lift beyond premium + actor + snipers: -2.2 pts [-12.2, +12.0] (CI reaches 0).
- Largest operator: 49 % of the VALIDATION selection. Without it: 28.6 % (22/77) [19.7-39.5] against 23.0 % (does not hold). Single-operator launches only: 35.2 % (51/145) [27.9-43.2] against 33.0 % (does not hold).
- VALIDATION halves: 35.0 % (28/80) [25.5-45.9] against 24.4 %; 33.3 % (24/72) [23.5-44.8] against 28.4 %.
- Logistic, signal alone: VALIDATION ROC-AUC 0.550, PR-AUC 0.300, gain from the signal +0.050 [-0.008, +0.092].
- Logistic, + premium: VALIDATION ROC-AUC 0.649, PR-AUC 0.342, gain from the signal +0.012 [-0.021, +0.039].
- Logistic, + operator: VALIDATION ROC-AUC 0.643, PR-AUC 0.335, gain from the signal +0.011 [-0.023, +0.039].
- Logistic, + premium + operator: VALIDATION ROC-AUC 0.650, PR-AUC 0.344, gain from the signal +0.013 [-0.018, +0.038].
- Mantel-Haenszel odds ratio of the signal within premium tercile x actor, VALIDATION: 1.14 [0.74, 1.86] (5 strata with both groups).

**Classification: PRICE/OPERATOR CONFOUNDED**

