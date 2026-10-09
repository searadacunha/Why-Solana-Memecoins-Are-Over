# Pump-Gold inspired features (pre-alert window, external trades, cut alert - 1 s)

| feature | definition | non-null |
|---|---|---|
| `pg_tx_per_wallet` | external buys + sells per distinct external trader | 1656 |
| `pg_buys_per_buyer` | external buys per distinct external buyer | 1656 |
| `pg_repeat_buyer_sol_share` | share of external buy SOL from wallets with >= 2 buys | 1656 |
| `pg_max_buys_one_wallet` | largest number of external buys by one wallet | 1656 |
| `pg_roundtrip_wallets` | external wallets that both bought and sold before the cut | 1656 |
| `pg_roundtrip_share` | round-trip wallets / distinct external buyers | 1656 |
| `pg_roundtrip_sol_share` | SOL sold by round-trip wallets / external buy SOL | 1656 |
| `pg_seller_buyer_overlap` | external sellers that had bought in the window / external sellers | 1315 |
| `pg_sell_buy_count_ratio` | external sells / external buys | 1656 |
| `pg_pingpong_10s` | buy followed by a sell of the same wallet within 10 s (count) | 1656 |
| `pg_same_size_share` | share of external buys whose SOL size (1e-3) is repeated by another buy | 1656 |
| `pg_modal_size_share` | share of external buys at the modal SOL size (1e-3) | 1656 |
| `pg_size_cv` | coefficient of variation of external buy sizes | 1656 |
| `pg_wallets_per_sol` | distinct external buyers per SOL of external buys | 1656 |
| `pg_sol_per_buyer` | external buy SOL per distinct external buyer | 1656 |
| `pg_buy_gini` | Gini of external buy SOL across buyer wallets | 1656 |
| `pg_top5_buyer_share` | share of external buy SOL from the 5 largest buyers | 1656 |
| `pg_small_buy_share` | share of external buys below 0.05 SOL | 1656 |
| `pg_big_buy_sol_share` | share of external buy SOL from buys >= 1 SOL | 1656 |
| `pg_ext_over_bundle` | external buy SOL / bundle SOL (core tickets) | 1656 |
| `pg_apparent_per_wallet` | (external buy + sell SOL) per distinct external trader | 1656 |
| `pg_sell_pressure` | external sell SOL / external buy SOL | 1656 |
| `pg_core_sell_over_ext_buy` | core sniper sell SOL before the cut / external buy SOL | 1656 |
| `pg_sell_first` | 1 if the first external trade after slot 0 is a sell | 1656 |
| `pg_buy_run_max` | longest run of consecutive external buys without an external sell | 1656 |
| `pg_buy_slot_gap_cv` | coefficient of variation of the slot gaps between consecutive external buys | 1609 |
| `pg_novelty_2nd_half` | share of second-half external buys made by wallets absent from the first half | 1473 |
| `pg_size_shift` | median external buy size, second half over first half of the window | 1473 |
| `pg_fresh_ata_share` | token accounts opened by first-time wallets / distinct external buyers | 1656 |
| `pg_sync_same_size_pairs` | pairs of external buys in the same slot by different wallets within 5 % in size | 1656 |
| `pg_same_slot_max_buyers` | largest number of distinct external buyers in one slot | 1656 |
| `pg_payer_mismatch_share` | share of external trades whose fee payer is not the trader | 1656 |
| `pg_modal_prio_share` | share of external trades paying the modal priority fee | 1656 |
| `pg_multisig_share` | share of external trades with >= 2 signatures | 1656 |
| `pg_n_ext_trades` | number of external trades (coverage) | 1657 |
