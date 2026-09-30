# D9. Verdict, rules of analysis_plan.md applied as written

- On-chain coverage: 100.0 % (minimum 80 %).
- VALIDATION alerts with an observed primary label: 606 (minimum 300).
- Step 7 'screened' minus 'actor + premium', VALIDATION ROC-AUC: +0.063 [-0.018, +0.114], independent on-chain information: no. Screened features: b_core_prio_sol, b_core_signers, b_core_sol, b_core_tip_sol, b_core_tx_n, b_creator_buy_sol, b_entropy, b_gini, b_hhi, b_migrated_slot0, b_other_slot0_buyers, b_other_slot0_sol, b_round_share, b_slot0_pool_buy_sol, b_ticket_cv, b_ticket_max, b_ticket_mean, b_ticket_median, b_ticket_q75, b_ticket_range, b_ticket_std, b_top1, b_top2, b_top3, b_top_half, b_tx_per_wallet, c_alerts_60m, e_prior_launches_share, f_fund_to_alert_h, f_fund_to_buy_h, f_funder_log_hist, f_hub_funded_share, g_core_fund_age_h, g_core_fund_cv, g_core_fund_sol, g_funder_prior_uses, h_core_last_in_age_h, h_core_prior_buys, h_core_tx_1h, h_core_tx_24h, h_creator_prior_buys, h_creator_prior_creates, h_creator_tx_1h, h_creator_tx_24h, h_sniper_reuse_max, m_accel, m_ata, m_buy_max, m_buy_median, m_buy_sell_ratio, m_buy_sol, m_buyers, m_buys, m_buys_10s, m_buys_5s, m_core_exit_share, m_core_exits, m_first10_sol, m_first1_sol, m_first3_sol, m_first5_sol, m_rate, m_sell_max, m_sell_sol, m_sellers, m_sells, m_tx, p_log_mc_usd, p_log_p0, p_pool_sol, p_price_max_ratio, p_velocity, w_core_log_age_h, w_core_log_prior_n, w_creator_log_age_h, w_creator_log_prior_n, w_early_err_share, c_actor_grouped, p_entry_over_operator.
- Reported, not used: step 7 'all' minus 'actor + premium', +0.037 [-0.056, +0.094].
- Reported, not used: step 3 ridge F minus C, +0.037 [-0.056, +0.094].

## rule: b_ticket_median <= 18.86 AND m_buy_max > 0.9802 AND m_buys_5s > 24

VALIDATION 45.8 % (22/48) [32.6-59.7], base 26.4 %, variants held 7 of 7.

- VALIDATION N >= 50: FAIL
- rate >= base + 15 points: pass
- Wilson lower bound > base: pass
- >= 6 of 7 variants held: pass
- |Spearman| < 0.8 with P0, premium, actor: pass
- no 2x2 cell below 20 against actor or premium: FAIL
- lift beyond the P0 + premium + actor model, CI above 0: FAIL

## model 'screened' (logreg), top 20 % by the TRAIN threshold

VALIDATION 45.5 % (51/112) [36.6-54.8], base 26.4 %, variants held 7 of 7.

- VALIDATION N >= 50: pass
- rate >= base + 15 points: pass
- Wilson lower bound > base: pass
- >= 6 of 7 variants held: pass
- |Spearman| < 0.8 with P0, premium, actor: pass
- no 2x2 cell below 20 against actor or premium: FAIL
- lift beyond the P0 + premium + actor model, CI above 0: pass

## Historical performance of the kept signals (primary label)

| signal | status | period | N selected | base | 2x rate [Wilson 95 %] | lift |
|---|---|---|---:|---:|---|---|
| rule: b_ticket_median <= 18.86 AND m_buy_max > 0.9802 AND m_buys_5s > 24 | TRAIN (in-sample: chosen or fitted here) | 2026-08-23 to 2026-09-14 | 40 | 22.4 % | 65.0 % (26/40) [49.5-77.9] | +42.6 pts, x2.90 |
| rule: b_ticket_median <= 18.86 AND m_buy_max > 0.9802 AND m_buys_5s > 24 | VALIDATION (used to choose among candidates) | 2026-09-15 to 2026-09-29 | 48 | 26.4 % | 45.8 % (22/48) [32.6-59.7] | +19.4 pts, x1.74 |
| model 'screened' (logreg), top 20 % by the TRAIN threshold | TRAIN (in-sample: chosen or fitted here) | 2026-08-23 to 2026-09-14 | 180 | 22.4 % | 39.4 % (71/180) [32.6-46.7] | +17.0 pts, x1.76 |
| model 'screened' (logreg), top 20 % by the TRAIN threshold | VALIDATION (used to choose among candidates) | 2026-09-15 to 2026-09-29 | 112 | 26.4 % | 45.5 % (51/112) [36.6-54.8] | +19.1 pts, x1.72 |

No TEST row: the future TEST is a separate question and is not touched here.

**Verdict: NO ROBUST ON-CHAIN SEPARATION FOUND**

ROBUST ON-CHAIN SIGNAL needs the future TEST and is not reachable here. Nothing in this verdict accounts for costs, slippage or execution prices.
