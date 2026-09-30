# D2. Pairs of features, systematic screen (primary label)

141 features, 9870 pairs tested. Base: TRAIN 22.4 %, VALIDATION 26.4 %. Passing BH (q < 0.05) in TRAIN: 5843. Of those, VALIDATION rate with a Wilson lower bound above the VALIDATION base (N >= 30): 3644.

## Best TRAIN pairs (by q)

| best cell | TRAIN | q (BH) | VALIDATION |
|---|---|---:|---|
| b_migrated_slot0 <= med, h_creator_prior_creates <= med | 28.2 % (189/671) [24.9-31.7] | 1.6e-11 | 33.1 % (158/477) [29.0-37.5] |
| b_tx_per_wallet <= med, h_creator_prior_creates <= med | 28.2 % (189/671) [24.9-31.7] | 1.6e-11 | 33.1 % (158/477) [29.0-37.5] |
| g_core_common_ratio <= med, h_creator_prior_creates <= med | 28.3 % (174/615) [24.9-32.0] | 1.6e-11 | 32.0 % (149/465) [28.0-36.4] |
| g_creator_shares_core_funder <= med, h_creator_prior_creates <= med | 28.2 % (189/671) [24.9-31.7] | 1.6e-11 | 33.1 % (158/477) [29.0-37.5] |
| h_creator_prev_alerts <= med, h_creator_prior_creates <= med | 28.3 % (189/667) [25.0-31.9] | 1.6e-11 | 33.4 % (158/473) [29.3-37.8] |
| h_creator_prior_creates <= med, h_early_tx_24h <= med | 28.2 % (189/671) [24.9-31.7] | 1.6e-11 | 33.1 % (158/477) [29.0-37.5] |
| h_creator_prior_creates <= med, m_creator_sells <= med | 28.5 % (188/659) [25.2-32.1] | 1.6e-11 | 33.6 % (157/467) [29.5-38.0] |
| h_creator_prior_creates <= med, w_creator_fresh <= med | 28.2 % (189/671) [24.9-31.7] | 1.6e-11 | 33.1 % (158/477) [29.0-37.5] |
| h_creator_prior_creates <= med, w_early_capped <= med | 28.2 % (189/671) [24.9-31.7] | 1.6e-11 | 33.1 % (158/477) [29.0-37.5] |
| h_creator_prior_creates <= med, w_early_log_prior_n <= med | 28.2 % (189/671) [24.9-31.7] | 1.6e-11 | 33.1 % (158/477) [29.0-37.5] |
| h_creator_prior_creates <= med, w_creator_err_share <= med | 28.5 % (186/652) [25.2-32.1] | 2.1e-11 | 34.4 % (157/457) [30.1-38.8] |
| g_core_common_ratio <= med, h_creator_tx_24h <= med | 28.7 % (170/592) [25.2-32.5] | 2.5e-11 | 33.4 % (147/440) [29.2-37.9] |
| h_creator_tx_1h <= med, m_creator_sells <= med | 28.8 % (183/636) [25.4-32.4] | 4.2e-11 | 34.3 % (155/452) [30.1-38.8] |
| c_actor_grouped <= med, m_creator_sells <= med | 28.5 % (185/649) [25.2-32.1] | 4.2e-11 | 33.5 % (155/462) [29.4-38.0] |
| b_core_tip_sol <= med, h_creator_prior_creates <= med | 28.1 % (187/665) [24.8-31.7] | 4.4e-11 | 32.8 % (153/466) [28.7-37.2] |
| b_migrated_slot0 <= med, c_actor_grouped <= med | 28.1 % (186/661) [24.8-31.7] | 4.4e-11 | 33.0 % (155/469) [28.9-37.4] |
| b_migrated_slot0 <= med, h_creator_tx_1h <= med | 28.4 % (184/647) [25.1-32.0] | 4.4e-11 | 34.3 % (156/455) [30.1-38.8] |
| b_migrated_slot0 <= med, h_creator_tx_24h <= med | 28.5 % (183/642) [25.1-32.1] | 4.4e-11 | 34.5 % (156/452) [30.3-39.0] |
| b_tx_per_wallet <= med, c_actor_grouped <= med | 28.1 % (186/661) [24.8-31.7] | 4.4e-11 | 33.0 % (155/469) [28.9-37.4] |
| b_tx_per_wallet <= med, h_creator_tx_1h <= med | 28.4 % (184/647) [25.1-32.0] | 4.4e-11 | 34.3 % (156/455) [30.1-38.8] |
| b_tx_per_wallet <= med, h_creator_tx_24h <= med | 28.5 % (183/642) [25.1-32.1] | 4.4e-11 | 34.5 % (156/452) [30.3-39.0] |
| c_actor_grouped <= med, g_core_common_ratio <= med | 28.3 % (171/605) [24.8-32.0] | 4.4e-11 | 31.9 % (146/457) [27.8-36.4] |
| c_actor_grouped <= med, g_creator_shares_core_funder <= med | 28.1 % (186/661) [24.8-31.7] | 4.4e-11 | 33.0 % (155/469) [28.9-37.4] |
| c_actor_grouped <= med, h_creator_prev_alerts <= med | 28.3 % (186/658) [25.0-31.8] | 4.4e-11 | 33.3 % (155/465) [29.2-37.7] |
| c_actor_grouped <= med, h_creator_prior_creates <= med | 28.3 % (186/658) [25.0-31.8] | 4.4e-11 | 33.0 % (155/469) [28.9-37.4] |
| c_actor_grouped <= med, h_early_tx_24h <= med | 28.1 % (186/661) [24.8-31.7] | 4.4e-11 | 33.0 % (155/469) [28.9-37.4] |
| c_actor_grouped <= med, w_creator_err_share <= med | 28.5 % (184/646) [25.1-32.1] | 4.4e-11 | 34.2 % (154/450) [30.0-38.7] |
| c_actor_grouped <= med, w_creator_fresh <= med | 28.1 % (186/661) [24.8-31.7] | 4.4e-11 | 33.0 % (155/469) [28.9-37.4] |
| c_actor_grouped <= med, w_early_capped <= med | 28.1 % (186/661) [24.8-31.7] | 4.4e-11 | 33.0 % (155/469) [28.9-37.4] |
| c_actor_grouped <= med, w_early_log_prior_n <= med | 28.1 % (186/661) [24.8-31.7] | 4.4e-11 | 33.0 % (155/469) [28.9-37.4] |

## The pairs named in the plan

| pair (best cell) | TRAIN | q (BH) | VALIDATION |
|---|---|---:|---|
| f_funder_top1 <= med, p_entry_over_operator <= med | 30.0 % (121/404) [25.7-34.6] | 1.8e-06 | 32.3 % (100/310) [27.3-37.7] |
| b_hhi <= med, b_ticket_median <= med | 30.7 % (90/293) [25.7-36.2] | 0.0007 | 38.1 % (61/160) [31.0-45.8] |
| g_creator_shares_core_funder <= med, w_creator_log_age_h > med | 26.6 % (119/448) [22.7-30.8] | 0.017 | 36.9 % (118/320) [31.8-42.3] |
| b_core_n > med, b_hhi <= med | 36.8 % (25/68) [26.3-48.6] | 0.029 | 45.7 % (37/81) [35.3-56.5] |
| b_core_tx_n > med, g_core_common_ratio <= med | 37.1 % (23/62) [26.2-49.5] | 0.03 | 44.7 % (34/76) [34.1-55.9] |
| b_ticket_cv <= med, f_indep_actors_strict <= med | 28.5 % (68/239) [23.1-34.5] | 0.045 | 34.7 % (42/121) [26.8-43.5] |
| b_core_n > med, f_hub_funded_share <= med | 33.8 % (23/68) [23.7-45.7] | 0.075 | 47.4 % (36/76) [36.5-58.4] |
| b_top1 > med, m_core_exit_share > med | 28.7 % (51/178) [22.5-35.7] | 0.11 | 35.0 % (56/160) [28.0-42.7] |
| f_funder_top1 <= med, w_early_log_prior_n <= med | 21.9 % (177/809) [19.2-24.9] | 1 | 25.6 % (150/586) [22.2-29.3] |
