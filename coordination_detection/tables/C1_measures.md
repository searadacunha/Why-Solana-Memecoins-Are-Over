# C1. Measures per launch (median, p25-p75 or share), TRAIN and VALIDATION

| measure | TRAIN: launches with it | TRAIN | VALIDATION: launches | VALIDATION |
|---|---:|---|---:|---|
| early_burstiness | 1013 | 0.286 (0.212-0.359) | 642 | 0.266 (0.186-0.348) |
| early_gap_cv | 1013 | 1.8 (1.54-2.12) | 642 | 1.73 (1.46-2.07) |
| early_same_slot_share | 1015 | 0.816 (0.739-0.875) | 642 | 0.792 (0.7-0.855) |
| early_within_10s | 1015 | 31 (19-42) | 642 | 31 (19-43) |
| early_within_1s | 1015 | 7 (4-11) | 642 | 7 (5-11) |
| early_within_5s | 1015 | 22 (15-29) | 642 | 24 (14-31) |
| fund_age_cv | 929 | 0 (0-0.000487) | 562 | 0 (0-0.00158) |
| fund_age_median | 939 | 187 (16-374) | 569 | 191 (22-415) |
| fund_spread_s | 939 | 0 (0-1) | 569 | 0 (0-1) |
| g_density | 1015 | 0.267 (0.267-0.267) | 642 | 0.267 (0.182-0.267) |
| g_deployer_distance | 274 | 2 (2-2) | 154 | 2 (2-2) |
| g_largest_component_snipers | 1015 | 4 (4-4) | 642 | 4 (4-4) |
| g_largest_share | 1015 | 1 (1-1) | 642 | 1 (0.8-1) |
| g_max_degree_to_snipers | 1015 | 4 (4-4) | 642 | 4 (4-4) |
| g_n_components_with_sniper | 1015 | 1 (1-1) | 642 | 1 (1-2) |
| g_pairs_only_via_top | 1015 | 6 (6-6) | 642 | 6 (6-6) |
| g_snipers_with_deployer | 1015 | 0 (0-4) | 642 | 0 (0-0) |
| gen_depth | 827 | 1 (1-2) | 560 | 1 (1-2) |
| gen_ge2 | 827 | 28.8 % true | 560 | 24.5 % true |
| gen_ge3 | 827 | 28.8 % true | 560 | 24.5 % true |
| gen_ge4 | 827 | 28.5 % true | 560 | 24.5 % true |
| gen_gini | 592 | 0.00225 (0-0.0306) | 423 | 0.00295 (0.00146-0.0816) |
| gen_hhi | 827 | 0.25 (0.25-1) | 559 | 0.253 (0.25-0.789) |
| gen_majority | 827 | 28.8 % true | 560 | 24.5 % true |
| gen_max_funders_per_source | 827 | 0 (0-1) | 560 | 0 (0-1) |
| gen_n_funders | 827 | 4 (1-4) | 560 | 4 (4-4) |
| gen_n_sources | 827 | 0 (0-1) | 560 | 0 (0-1) |
| gen_ratio | 827 | 0.25 (0.25-1) | 560 | 0.25 (0.25-0.25) |
| gen_same_source_2_funders | 827 | 0.5 % true | 560 | 0.4 % true |
| gen_shared | 827 | 1 (1-4) | 560 | 1 (1-1) |
| gen_sol_share_top | 827 | 0.258 (0.25-1) | 559 | 0.293 (0.251-0.886) |
| gen_strict_ge2 | 827 | 28.8 % true | 560 | 24.5 % true |
| last_ge2 | 939 | 83.8 % true | 569 | 79.8 % true |
| last_ge3 | 939 | 83.1 % true | 569 | 79.6 % true |
| last_ge4 | 939 | 83.1 % true | 569 | 79.6 % true |
| last_gini | 160 | 9.3e-07 (0-1.73e-06) | 125 | 1.25e-06 (8.12e-07-7.39e-05) |
| last_hhi | 939 | 1 (1-1) | 569 | 1 (1-1) |
| last_majority | 939 | 83.1 % true | 569 | 79.6 % true |
| last_n_funders | 939 | 1 (1-1) | 569 | 1 (1-1) |
| last_ratio | 939 | 1 (1-1) | 569 | 1 (1-1) |
| last_shared | 939 | 4 (4-4) | 569 | 4 (4-4) |
| last_sol_share_top | 939 | 1 (1-1) | 569 | 1 (1-1) |
| last_strict_ge2 | 939 | 30.8 % true | 569 | 27.2 % true |
| max_per_tx | 1015 | 1 (1-2) | 642 | 1 (1-1) |
| n_early_pre | 1015 | 36 (21-49) | 642 | 38.5 (22-52) |
| n_snipers | 1015 | 4 (4-4) | 642 | 4 (4-4) |
| re_funders_seen_before | 1015 | 0 (0-1) | 642 | 0 (0-1) |
| re_pairs_seen_before | 1015 | 0 (0-6) | 642 | 0 (0-6) |
| re_snipers_seen_before | 1015 | 0 (0-4) | 642 | 0 (0-4) |
| re_tickets_seen_before | 1015 | 4 (3-4) | 642 | 4 (4-4) |
| share_multi_tx | 1015 | 0 (0-1) | 642 | 0 (0-0) |
| tk_entropy | 1015 | 1 (0.963-1) | 642 | 1 (0.961-1) |
| tk_gini | 1015 | 0.0164 (0.0102-0.133) | 642 | 0.0204 (0.0141-0.178) |
| tk_hhi | 1015 | 0.25 (0.25-0.251) | 642 | 0.25 (0.25-0.251) |
| tk_identical_pairs | 1015 | 0 (0-0) | 642 | 0 (0-0) |
| tk_max_over_median | 1015 | 1.03 (1.02-1.08) | 642 | 1.04 (1.03-1.27) |
| tk_near10 | 1015 | 0 (0-0) | 642 | 0 (0-0) |
| tk_near20 | 1015 | 1 (0-2) | 642 | 1 (0-2) |
| tk_near5 | 1015 | 0 (0-0) | 642 | 0 (0-0) |
| tk_near_identical_pairs | 1015 | 1 (0-2) | 642 | 1 (0-1) |
| tk_round | 1015 | 0 (0-0) | 642 | 0 (0-0) |
| tk_top1 | 1015 | 0.259 (0.254-0.295) | 642 | 0.259 (0.257-0.277) |
| tk_top2 | 1015 | 0.514 (0.505-0.55) | 642 | 0.514 (0.51-0.529) |
| tk_top3 | 1015 | 0.758 (0.754-0.774) | 642 | 0.759 (0.754-0.77) |

## Funding-graph architecture (hubs excluded; unknown-status last funders kept, then dropped)

| architecture | TRAIN | VALIDATION | TRAIN, strict | VALIDATION, strict |
|---|---:|---:|---:|---:|
| A | 261 (26 %) | 151 (24 %) | 233 (23 %) | 133 (21 %) |
| B | 4 (0 %) | 2 (0 %) | 4 (0 %) | 2 (0 %) |
| SHARED | 569 (56 %) | 355 (55 %) | 68 (7 %) | 29 (5 %) |
| INDEPENDENT | 178 (18 %) | 134 (21 %) | 710 (70 %) | 478 (74 %) |
| OTHER | 3 (0 %) | 0 (0 %) | 0 (0 %) | 0 (0 %) |
