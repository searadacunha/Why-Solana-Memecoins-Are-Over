# D8. Robustness, mechanics and matched comparison

## rule: b_ticket_median <= 18.86 AND m_buy_max > 0.9802 AND m_buys_5s > 24

| variant | signal | base | holds (Wilson lower bound above base) |
|---|---|---|---|
| primary | 45.8 % (22/48) [32.6-59.7] | 26.4 % | yes |
| window 10 min | 46.0 % (23/50) [33.0-59.6] | 23.3 % | yes |
| window 20 min | 46.8 % (22/47) [33.3-60.8] | 26.6 % | yes |
| threshold 1.8x | 52.1 % (25/48) [38.3-65.5] | 30.5 % | yes |
| threshold 2.2x | 45.8 % (22/48) [32.6-59.7] | 21.8 % | yes |
| single read | 50.0 % (24/48) [36.4-63.6] | 31.0 % | yes |
| cut-off -2 s | 45.5 % (20/44) [31.7-59.9] | 26.4 % | yes |
| cut-off -5 s | 46.9 % (15/32) [30.9-63.6] | 26.4 % | yes |

Variants held: 7 of 7.
- VALIDATION first half: signal 41.7 % (5/12) [19.3-68.0], base 24.3 %.
- VALIDATION second half: signal 47.2 % (17/36) [32.0-63.0], base 28.6 %.
- month 08, TRAIN rows: signal 28.6 % (2/7) [8.2-64.1], base 21.3 %.
- month 09, TRAIN rows: signal 72.7 % (24/33) [55.8-84.9], base 23.3 %.
- month 09, VAL rows: signal 45.8 % (22/48) [32.6-59.7], base 26.4 %.
- week from 2026-08-21, TRAIN rows: signal 0.0 % (0/4) [0.0-49.0], base 20.1 %.
- week from 2026-08-27, TRAIN rows: signal 75.0 % (3/4) [30.1-95.4], base 22.0 %.
- week from 2026-09-03, TRAIN rows: signal 68.4 % (13/19) [46.0-84.6], base 20.4 %.
- week from 2026-09-10, TRAIN rows: signal 76.9 % (10/13) [49.7-91.8], base 30.0 %.
- week from 2026-09-10, VAL rows: signal n/a (0), base 27.6 %.
- week from 2026-09-17, VAL rows: signal 58.8 % (10/17) [36.0-78.4], base 25.7 %.
- week from 2026-09-24, VAL rows: signal 38.7 % (12/31) [23.7-56.2], base 26.8 %.

Mechanics on VALIDATION (Spearman with the signal):

- p_log_p0: -0.36
- p_entry_over_operator: -0.34
- p_pool_sol: -0.34
- p_reserve_vs_p0: +0.12
- p_curve_left_sol: +0.08
- b_core_supply: -0.17
- c_actor_grouped: -0.13
- f_same_funder_multi: -0.29
- g_core_common_ratio: -0.22
- b_core_n: +0.74
- 2x2 signal x actor (out/in x 0/1): {(0, 0): 452, (0, 1): 140, (1, 0): 48, (1, 1): 2}  (NOT SEPARABLE, a cell below 20)
- 2x2 signal x premium (out/in x 0/1): {(0, 0): 453, (0, 1): 139, (1, 0): 49, (1, 1): 1}  (NOT SEPARABLE, a cell below 20)
- Lift within premium tercile x P0 tercile x actor (VALIDATION, 5 strata with both groups, reported only): +16.9 pts [+3.0, +32.1]
- Lift beyond the P0 + premium + actor model (observed minus expected, in minus out): +6.1 pts [-37.4, +47.8]  (EXPLAINED by P0, premium, actor: the CI reaches 0)

## model 'screened' (logreg), top 20 % by the TRAIN threshold

| variant | signal | base | holds (Wilson lower bound above base) |
|---|---|---|---|
| primary | 45.5 % (51/112) [36.6-54.8] | 26.4 % | yes |
| window 10 min | 44.7 % (51/114) [35.9-53.9] | 23.3 % | yes |
| window 20 min | 45.5 % (50/110) [36.5-54.8] | 26.6 % | yes |
| threshold 1.8x | 50.9 % (57/112) [41.8-60.0] | 30.5 % | yes |
| threshold 2.2x | 39.3 % (44/112) [30.7-48.5] | 21.8 % | yes |
| single read | 51.8 % (58/112) [42.6-60.8] | 31.0 % | yes |
| cut-off -2 s | 45.9 % (50/109) [36.8-55.2] | 26.4 % | yes |
| cut-off -5 s | 44.8 % (43/96) [35.2-54.7] | 26.4 % | yes |

Variants held: 7 of 7.
- VALIDATION first half: signal 42.0 % (29/69) [31.1-53.8], base 24.3 %.
- VALIDATION second half: signal 51.2 % (22/43) [36.8-65.4], base 28.6 %.
- month 08, TRAIN rows: signal 37.2 % (16/43) [24.4-52.1], base 21.3 %.
- month 09, TRAIN rows: signal 40.1 % (55/137) [32.3-48.5], base 23.3 %.
- month 09, VAL rows: signal 45.5 % (51/112) [36.6-54.8], base 26.4 %.
- week from 2026-08-21, TRAIN rows: signal 25.0 % (2/8) [7.1-59.1], base 20.1 %.
- week from 2026-08-27, TRAIN rows: signal 43.2 % (16/37) [28.7-59.1], base 22.0 %.
- week from 2026-09-03, TRAIN rows: signal 33.3 % (29/87) [24.3-43.8], base 20.4 %.
- week from 2026-09-10, TRAIN rows: signal 50.0 % (24/48) [36.4-63.6], base 30.0 %.
- week from 2026-09-10, VAL rows: signal 46.7 % (7/15) [24.8-69.9], base 27.6 %.
- week from 2026-09-17, VAL rows: signal 46.7 % (28/60) [34.6-59.1], base 25.7 %.
- week from 2026-09-24, VAL rows: signal 43.2 % (16/37) [28.7-59.1], base 26.8 %.

Mechanics on VALIDATION (Spearman with the signal):

- p_log_p0: -0.45
- p_entry_over_operator: -0.39
- p_pool_sol: -0.44
- p_reserve_vs_p0: -0.02
- p_curve_left_sol: +0.01
- b_core_supply: -0.29
- c_actor_grouped: -0.25
- f_same_funder_multi: -0.23
- g_core_common_ratio: -0.15
- b_core_n: +0.64
- 2x2 signal x actor (out/in x 0/1): {(0, 0): 383, (0, 1): 142, (1, 0): 117, (1, 1): 0}  (NOT SEPARABLE, a cell below 20)
- 2x2 signal x premium (out/in x 0/1): {(0, 0): 385, (0, 1): 140, (1, 0): 117, (1, 1): 0}  (NOT SEPARABLE, a cell below 20)
- Lift within premium tercile x P0 tercile x actor (VALIDATION, 7 strata with both groups, reported only): +17.1 pts [+5.8, +28.1]
- Lift beyond the P0 + premium + actor model (observed minus expected, in minus out): +10.6 pts [+2.2, +30.8]

## Matched comparison: common funding within similar launches

Strata: week x premium tercile (TRAIN cuts 3.60 / 3.96) x core wallets above 4 x bundle SOL above 81.6 (TRAIN medians). Treated: one funder for >= 2 core wallets. Mantel-Haenszel risk difference, stratified bootstrap (1000).

- TRAIN: 20 strata with both groups; MH difference +6.6 pts [-5.2, +17.2].
- VAL: 15 strata with both groups; MH difference -21.8 pts [-41.7, -3.3].
