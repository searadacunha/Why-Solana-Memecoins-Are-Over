# E3. Controls against false signals, and the classification

VALIDATION holds = its Wilson 95 % lower bound is above the VALIDATION base at the cut-off.

## market cap: `[P5] 3e+04 <= mc_usd < 3.5e+04`

- TRAIN 47.4 % (27/57) [35.0-60.1] (base 21.7 %), permutation p 0.000.
- VALIDATION 31.4 % (11/35) [18.6-48.0], base 25.3 %, lower bound 18.6 %: does not hold.
- VALIDATION drawdown before the 2x, among the 11 that reached it: median -0.01.
- Lift beyond actor: +1.1 pts [-22.8, +13.3] (the CI reaches 0: explained by it).
- Largest operator: 18 of the 35 VALIDATION alerts (51 %).
- Without that operator: 17.6 % (3/17) [6.2-41.0] against 21.9 %: does not hold.
- Without the grouped launches: 31.4 % (11/35) [18.6-48.0] against 31.6 %: does not hold.
- VALIDATION first half: 33.3 % (10/30) [19.2-51.2] against 24.2 %.
- VALIDATION second half: 20.0 % (1/5) [3.6-62.4] against 26.4 %.
  - week from 2026-09-15: 45.5 % (5/11) [21.3-72.0].
  - week from 2026-09-17: 26.3 % (5/19) [11.8-48.8].
  - week from 2026-09-24: 20.0 % (1/5) [3.6-62.4].

**Classification: TRAIN OVERFIT**

## premium: `[D] premium <= 3.299`

- TRAIN 43.3 % (39/90) [33.6-53.6] (base 22.4 %), permutation p 0.000.
- VALIDATION 28.9 % (24/83) [20.3-39.4], base 26.4 %, lower bound 20.3 %: does not hold.
- VALIDATION drawdown before the 2x, among the 24 that reached it: median -0.03.
- Lift beyond actor: -2.6 pts [-24.5, +4.2] (the CI reaches 0: explained by it).
- Largest operator: 55 of the 83 VALIDATION alerts (66 %).
- Without that operator: 14.3 % (4/28) [5.7-31.5] against 23.0 %: does not hold.
- Without the grouped launches: 29.3 % (24/82) [20.5-39.9] against 33.0 %: does not hold.
- VALIDATION first half: 24.4 % (10/41) [13.8-39.3] against 24.4 %.
- VALIDATION second half: 33.3 % (14/42) [21.0-48.4] against 28.4 %.
  - week from 2026-09-15: 40.0 % (2/5) [11.8-76.9].
  - week from 2026-09-17: 26.3 % (10/38) [15.0-42.0].
  - week from 2026-09-24: 30.0 % (12/40) [18.1-45.4].

**Classification: TRAIN OVERFIT**

## other price: `[D] pool_sol <= 70.61`

- TRAIN 39.6 % (65/164) [32.5-47.3] (base 22.4 %), permutation p 0.000.
- VALIDATION 32.8 % (44/134) [25.5-41.2], base 26.4 %, lower bound 25.5 %: does not hold.
- VALIDATION drawdown before the 2x, among the 44 that reached it: median -0.03.
- Lift beyond actor: +1.9 pts [-12.7, +8.9] (the CI reaches 0: explained by it).
- Largest operator: 62 of the 134 VALIDATION alerts (46 %).
- Without that operator: 25.0 % (18/72) [16.4-36.1] against 23.0 %: does not hold.
- Without the grouped launches: 32.8 % (44/134) [25.5-41.2] against 33.0 %: does not hold.
- VALIDATION first half: 31.2 % (25/80) [22.2-42.1] against 24.4 %.
- VALIDATION second half: 35.2 % (19/54) [23.8-48.5] against 28.4 %.
  - week from 2026-09-15: 41.7 % (5/12) [19.3-68.0].
  - week from 2026-09-17: 35.1 % (26/74) [25.2-46.5].
  - week from 2026-09-24: 27.1 % (13/48) [16.6-41.0].

**Classification: TRAIN OVERFIT**

## SOL engaged: `[P20] 97.34 < sol_total <= 101.7`

- TRAIN 42.9 % (33/77) [32.4-54.0] (base 18.7 %), permutation p 0.000.
- VALIDATION 37.2 % (16/43) [24.4-52.1], base 24.1 %, lower bound 24.4 %: holds.
- VALIDATION drawdown before the 2x, among the 16 that reached it: median -0.05.
- Lift beyond premium: +8.1 pts [-10.2, +25.4] (the CI reaches 0: explained by it).
- Lift beyond actor: +10.2 pts [-7.7, +28.5] (the CI reaches 0: explained by it).
- Lift beyond premium + actor: +8.1 pts [-10.2, +25.3] (the CI reaches 0: explained by it).
- Lift beyond premium + actor + snipers + run-up: +8.5 pts [-9.8, +25.2] (the CI reaches 0: explained by it).
- Largest operator: 11 of the 43 VALIDATION alerts (26 %).
- Without that operator: 34.4 % (11/32) [20.4-51.7] against 20.7 %: does not hold.
- Without the grouped launches: 35.7 % (15/42) [23.0-50.8] against 30.3 %: does not hold.
- VALIDATION first half: 39.1 % (9/23) [22.2-59.2] against 22.2 %.
- VALIDATION second half: 35.0 % (7/20) [18.1-56.7] against 26.1 %.
  - week from 2026-09-15: 50.0 % (2/4) [15.0-85.0].
  - week from 2026-09-17: 36.8 % (7/19) [19.1-59.0].
  - week from 2026-09-24: 35.0 % (7/20) [18.1-56.7].
- Same rule with the largest buyer removed: 11.1 % (4/36) [4.4-25.3]: does not hold.

**Classification: PRICE/OPERATOR CONFOUNDED**

## counts and timing: `[P5] 30 < buys_5s <= 35`

- TRAIN 39.2 % (31/79) [29.2-50.3] (base 21.7 %), permutation p 0.040.
- VALIDATION 29.3 % (22/75) [20.2-40.4], base 25.3 %, lower bound 20.2 %: does not hold.
- VALIDATION drawdown before the 2x, among the 22 that reached it: median -0.04.
- Lift beyond premium: -0.3 pts [-12.7, +9.1] (the CI reaches 0: explained by it).
- Lift beyond actor: -1.3 pts [-13.7, +8.0] (the CI reaches 0: explained by it).
- Lift beyond premium + actor: -1.4 pts [-13.7, +8.0] (the CI reaches 0: explained by it).
- Lift beyond premium + actor + snipers + run-up: -0.4 pts [-12.7, +9.3] (the CI reaches 0: explained by it).
- Largest operator: 16 of the 75 VALIDATION alerts (21 %).
- Without that operator: 23.7 % (14/59) [14.7-36.0] against 21.9 %: does not hold.
- Without the grouped launches: 29.3 % (22/75) [20.2-40.4] against 31.6 %: does not hold.
- VALIDATION first half: 34.5 % (10/29) [19.9-52.7] against 24.2 %.
- VALIDATION second half: 26.1 % (12/46) [15.6-40.3] against 26.4 %.
  - week from 2026-09-15: 44.4 % (4/9) [18.9-73.3].
  - week from 2026-09-17: 30.4 % (7/23) [15.6-50.9].
  - week from 2026-09-24: 25.6 % (11/43) [14.9-40.2].

**Classification: TRAIN OVERFIT**

## capacity: `[T0] 25 < cap_all_max <= 35.44`

- TRAIN 43.3 % (39/90) [33.6-53.6] (base 22.4 %), permutation p 0.005.
- VALIDATION 34.3 % (12/35) [20.8-50.8], base 26.4 %, lower bound 20.8 %: does not hold.
- VALIDATION drawdown before the 2x, among the 12 that reached it: median -0.01.
- Lift beyond premium: +2.2 pts [-13.5, +28.7] (the CI reaches 0: explained by it).
- Lift beyond actor: +5.1 pts [-9.8, +31.5] (the CI reaches 0: explained by it).
- Lift beyond premium + actor: +2.3 pts [-13.2, +28.7] (the CI reaches 0: explained by it).
- Lift beyond premium + actor + snipers + run-up: +2.3 pts [-13.2, +28.8] (the CI reaches 0: explained by it).
- Largest operator: 8 of the 35 VALIDATION alerts (23 %).
- Without that operator: 37.0 % (10/27) [21.5-55.8] against 26.4 %: does not hold.
- Without the grouped launches: 34.4 % (11/32) [20.4-51.7] against 33.0 %: does not hold.
- VALIDATION first half: 32.1 % (9/28) [17.9-50.7] against 24.4 %.
- VALIDATION second half: 42.9 % (3/7) [15.8-75.0] against 28.4 %.
  - week from 2026-09-15: 75.0 % (3/4) [30.1-95.4].
  - week from 2026-09-17: 25.0 % (6/24) [12.0-44.9].
  - week from 2026-09-24: 42.9 % (3/7) [15.8-75.0].

**Classification: TRAIN OVERFIT**

## funding: `[P300] 0.9708 < fu_ticket_over_recv_24h_median <= 0.971`

- TRAIN 33.8 % (22/65) [23.5-46.0] (base 11.1 %), permutation p 0.005.
- VALIDATION 62.5 % (5/8) [30.6-86.3], base 15.2 %, lower bound 30.6 %: holds.
- VALIDATION drawdown before the 2x, among the 5 that reached it: median -0.13.
- Lift beyond premium: +46.5 pts [+3.5, +86.1].
- Lift beyond actor: +41.6 pts [+2.4, +80.7].
- Lift beyond premium + actor: +36.7 pts [-6.6, +77.4] (the CI reaches 0: explained by it).
- Lift beyond premium + actor + snipers + run-up: +32.2 pts [-12.8, +76.6] (the CI reaches 0: explained by it).
- Largest operator: 3 of the 8 VALIDATION alerts (38 %).
- Without that operator: 80.0 % (4/5) [37.6-96.4] against 15.2 %: holds.
- Without the grouped launches: n/a (0) against 11.5 %: does not hold.
- VALIDATION first half: 100.0 % (2/2) [34.2-100.0] against 15.4 %.
- VALIDATION second half: 50.0 % (3/6) [18.8-81.2] against 15.1 %.
  - week from 2026-09-15: 100.0 % (1/1) [20.7-100.0].
  - week from 2026-09-17: 100.0 % (1/1) [20.7-100.0].
  - week from 2026-09-24: 50.0 % (3/6) [18.8-81.2].

**Classification: PRICE/OPERATOR CONFOUNDED**

## combination: `[D] premium <= 3.564 AND [D] sol_top3 < 60 AND [D] sol_hhi > 0.1667 AND [D] n_early > 40`

- TRAIN 76.2 % (32/42) [61.5-86.5] (base 22.4 %), permutation p 0.000.
- VALIDATION 38.9 % (7/18) [20.3-61.4], base 26.4 %, lower bound 20.3 %: does not hold.
- VALIDATION drawdown before the 2x, among the 7 that reached it: median -0.05.
- Lift beyond premium: -0.9 pts [-27.7, +29.1] (the CI reaches 0: explained by it).
- Lift beyond actor: +9.0 pts [-15.2, +39.0] (the CI reaches 0: explained by it).
- Lift beyond premium + actor: -0.7 pts [-27.7, +29.3] (the CI reaches 0: explained by it).
- Lift beyond premium + actor + snipers + run-up: -0.9 pts [-27.9, +29.0] (the CI reaches 0: explained by it).
- Largest operator: 4 of the 18 VALIDATION alerts (22 %).
- Without that operator: 28.6 % (4/14) [11.7-54.6] against 23.0 %: does not hold.
- Without the grouped launches: 41.2 % (7/17) [21.6-64.0] against 33.0 %: does not hold.
- VALIDATION first half: 75.0 % (3/4) [30.1-95.4] against 24.4 %.
- VALIDATION second half: 28.6 % (4/14) [11.7-54.6] against 28.4 %.
  - week from 2026-09-15: 100.0 % (2/2) [34.2-100.0].
  - week from 2026-09-17: 66.7 % (2/3) [20.8-93.9].
  - week from 2026-09-24: 23.1 % (3/13) [8.2-50.3].

**Classification: TRAIN OVERFIT**

