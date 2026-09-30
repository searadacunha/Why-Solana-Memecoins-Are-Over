# D6. Simple rules (primary label)

Atoms 1690, rules evaluated 1582590, distinct rules with TRAIN support >= 40: 978424. Base: TRAIN 22.4 %, VALIDATION 26.4 %.

## Rules by TRAIN hit rate, and what VALIDATION gives them

| TRAIN rate | rules | largest N | pooled TRAIN | pooled VALIDATION (alert-rule pairs) |
|---|---:|---:|---|---|
| 80-100 % | 0 | - | - | - |
| 70-80 % | 0 | - | - | - |
| 60-70 % | 431 | 56 | 61.2 % (11191/18281) [60.5-61.9] | 39.7 % (6200/15610) [39.0-40.5] |

## The 50 best TRAIN rules, re-measured in VALIDATION

| rule | TRAIN | VALIDATION | VAL Wilson lower bound |
|---|---|---|---:|
| b_ticket_median <= 18.86 AND m_buy_max > 0.9802 AND m_buys_5s > 24 | 65.0 % (26/40) [49.5-77.9] | 45.8 % (22/48) [32.6-59.7] | 0.326 |
| b_ticket_median <= 18.86 AND m_buys_5s > 24 AND m_first1_sol > 9.99e-06 | 63.4 % (26/41) [48.1-76.4] | 45.8 % (22/48) [32.6-59.7] | 0.326 |
| b_ticket_median <= 18.86 AND c_alerts_60m > 1 AND m_buys_5s > 24 | 65.0 % (26/40) [49.5-77.9] | 45.7 % (21/46) [32.2-59.8] | 0.322 |
| b_ticket_median <= 18.86 AND m_buys_5s > 24 AND m_failed > 14 | 63.4 % (26/41) [48.1-76.4] | 44.0 % (22/50) [31.2-57.7] | 0.312 |
| b_ticket_mean <= 21.14 AND b_ticket_median <= 18.86 AND m_buys_5s > 24 | 65.0 % (26/40) [49.5-77.9] | 43.1 % (22/51) [30.5-56.7] | 0.305 |
| b_ticket_median <= 18.86 AND m_buys_5s > 24 AND m_rate > 2.65 | 65.0 % (26/40) [49.5-77.9] | 43.1 % (22/51) [30.5-56.7] | 0.305 |
| b_slot0_pool_buy_sol <= 49.84 AND b_ticket_median <= 18.86 AND m_buys_5s > 24 | 63.4 % (26/41) [48.1-76.4] | 43.1 % (22/51) [30.5-56.7] | 0.305 |
| b_ticket_median <= 18.86 AND h_early_tx_1h <= 93 AND m_buys_5s > 24 | 63.4 % (26/41) [48.1-76.4] | 43.1 % (22/51) [30.5-56.7] | 0.305 |
| b_ticket_median <= 18.86 AND m_buy_max > 0.4762 AND m_buys_5s > 24 | 63.4 % (26/41) [48.1-76.4] | 43.1 % (22/51) [30.5-56.7] | 0.305 |
| b_ticket_median <= 18.86 AND m_buys_5s > 24 AND m_first5_sol > 0.1109 | 63.4 % (26/41) [48.1-76.4] | 43.1 % (22/51) [30.5-56.7] | 0.305 |
| b_ticket_median <= 18.86 AND m_buys_5s > 26 | 65.0 % (26/40) [49.5-77.9] | 43.5 % (20/46) [30.2-57.8] | 0.302 |
| c_alerts_60m > 7 AND g_funder_prior_uses > 1527 AND w_creator_log_age_h <= 0.5556 | 65.0 % (26/40) [49.5-77.9] | 40.5 % (17/42) [27.0-55.5] | 0.270 |
| b_ticket_q75 <= 19.74 AND m_buyburn > 0 AND p_entry_over_operator <= 3.464 | 62.8 % (27/43) [47.9-75.6] | 39.2 % (20/51) [27.0-52.9] | 0.270 |
| c_alerts_60m > 7 AND g_funder_prior_uses > 1527 | 63.4 % (26/41) [48.1-76.4] | 38.0 % (19/50) [25.9-51.8] | 0.259 |
| b_slot0_tx > 8 AND c_alerts_60m > 6 AND g_funder_prior_uses > 1527 | 65.0 % (26/40) [49.5-77.9] | 36.5 % (19/52) [24.8-50.1] | 0.248 |
| b_slot0_tx > 5 AND c_alerts_60m > 6 AND g_funder_prior_uses > 1527 | 63.4 % (26/41) [48.1-76.4] | 32.4 % (22/68) [22.4-44.2] | 0.224 |
| c_alerts_60m > 7 AND c_dow > 0 AND g_funder_prior_uses > 1527 | 65.0 % (26/40) [49.5-77.9] | 34.0 % (16/47) [22.2-48.3] | 0.222 |
| b_other_slot0_buyers > 0 AND c_alerts_60m > 6 AND g_funder_prior_uses > 1527 | 65.0 % (26/40) [49.5-77.9] | 31.3 % (21/67) [21.5-43.2] | 0.215 |
| b_ticket_q75 <= 19.74 AND f_bundle_share_top_funder > 0.7508 AND m_buy_max > 0.987 | 65.9 % (27/41) [50.5-78.4] | 52.9 % (18/34) [36.7-68.5] | VAL N < 40 |
| b_ticket_max <= 20.18 AND f_bundle_share_top_funder > 0.7508 AND p_price_max_ratio > 1.002 | 65.9 % (27/41) [50.5-78.4] | 64.3 % (9/14) [38.8-83.7] | VAL N < 40 |
| b_top_half <= 0.5046 AND m_buy_median <= 0.09901 AND m_core_exits > 3 | 65.9 % (27/41) [50.5-78.4] | 29.0 % (9/31) [16.1-46.6] | VAL N < 40 |
| b_ticket_q75 <= 19.74 AND f_bundle_share_top_funder > 0.7508 AND m_buy_sol > 5.146 | 64.6 % (31/48) [50.4-76.6] | 56.2 % (18/32) [39.3-71.8] | VAL N < 40 |
| b_ticket_q75 <= 19.74 AND f_indep_share <= 0.4 AND m_buy_sol > 5.146 | 63.8 % (30/47) [49.5-76.0] | 53.1 % (17/32) [36.4-69.1] | VAL N < 40 |
| c_alerts_60m > 7 AND g_core_fund_cv <= 0.004309 AND m_tx > 63 | 65.0 % (26/40) [49.5-77.9] | 42.9 % (12/28) [26.5-60.9] | VAL N < 40 |
| b_ticket_q75 <= 19.74 AND f_bundle_share_top_funder > 0.7508 AND p_pool_price_ratio <= 1.124 | 65.0 % (26/40) [49.5-77.9] | 53.3 % (16/30) [36.1-69.8] | VAL N < 40 |

**Kept (best VALIDATION lower bound, VALIDATION N >= 40): `b_ticket_median <= 18.86 AND m_buy_max > 0.9802 AND m_buys_5s > 24`**: TRAIN 65.0 % (26/40) [49.5-77.9], VALIDATION 45.8 % (22/48) [32.6-59.7] (base 26.4 %). VALIDATION chose it among 50 rules, so its VALIDATION rate is optimistic.
