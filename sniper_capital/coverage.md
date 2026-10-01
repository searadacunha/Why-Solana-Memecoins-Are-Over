# Coverage of the sniper-capital variables, before any analysis

One record per sniper and launch: 6822 records, 3852 distinct wallets, 1657 launches. Snipers = the detector's tickets (5 SOL or more on the curve in the creation slot, the creator's own buy included). No label was read to build this file.

## Per variable, sniper records

| variable | OBSERVED | PARTIAL | MISSING | OBSERVED, TRAIN / VALIDATION |
|---|---:|---:|---:|---|
| capital_before_buy | 100.0 % | 0.0 % | 0.0 % | 100.0 % / 100.0 % |
| capital_after_buy | 100.0 % | 0.0 % | 0.0 % | 100.0 % / 100.0 % |
| ticket | 100.0 % | 0.0 % | 0.0 % | 100.0 % / 100.0 % |
| funding_1h | 55.5 % | 44.5 % | 0.0 % | 53.0 % / 59.5 % |
| funding_6h | 52.9 % | 47.1 % | 0.0 % | 50.0 % / 57.3 % |
| funding_24h | 50.7 % | 49.3 % | 0.0 % | 46.9 % / 56.6 % |
| funding_7d | 48.9 % | 51.1 % | 0.0 % | 44.7 % / 55.3 % |
| time_since_last_funding | 97.4 % | 2.6 % | 0.0 % | 97.7 % / 97.0 % |
| balance_before_recent_funding | 97.4 % | 2.6 % | 0.0 % | 97.7 % / 97.0 % |
| sol_spent_history | 48.6 % | 40.3 % | 11.1 % | 44.4 % / 55.2 % |
| n_history_tx | 88.9 % | 11.1 % | 0.0 % | 86.8 % / 92.2 % |
| n_history_trades | 48.6 % | 0.0 % | 51.4 % | 44.4 % / 55.2 % |
| wallet_age | 88.9 % | 11.1 % | 0.0 % | 86.8 % / 92.2 % |
| genesis_funder | 88.9 % | 0.0 % | 11.1 % | 86.8 % / 92.2 % |
| funder_of_funder | 88.9 % | 0.0 % | 11.1 % | 86.8 % / 92.2 % |

## Per variable, launches whose every sniper is OBSERVED

| variable | all launches | TRAIN | VALIDATION |
|---|---:|---:|---:|
| capital_before_buy | 1657 (100 %) | 1015 | 642 |
| capital_after_buy | 1657 (100 %) | 1015 | 642 |
| ticket | 1657 (100 %) | 1015 | 642 |
| funding_1h | 836 (50 %) | 517 | 319 |
| funding_6h | 800 (48 %) | 492 | 308 |
| funding_24h | 766 (46 %) | 462 | 304 |
| funding_7d | 742 (45 %) | 444 | 298 |
| time_since_last_funding | 1508 (91 %) | 939 | 569 |
| balance_before_recent_funding | 1508 (91 %) | 939 | 569 |
| sol_spent_history | 738 (45 %) | 441 | 297 |
| n_history_tx | 1387 (84 %) | 827 | 560 |
| n_history_trades | 738 (45 %) | 441 | 297 |
| wallet_age | 1387 (84 %) | 827 | 560 |
| genesis_funder | 1387 (84 %) | 827 | 560 |
| funder_of_funder | 1387 (84 %) | 827 | 560 |

## Temporal bias: share of sniper records OBSERVED, by week

| week from | records | capital before buy | funding 1h | funding 24h | funding 7d | whole history |
|---|---:|---:|---:|---:|---:|---:|
| 2026-08-21 | 1020 | 100 % | 59 % | 51 % | 47 % | 46 % |
| 2026-08-27 | 931 | 100 % | 55 % | 46 % | 45 % | 45 % |
| 2026-09-03 | 1423 | 100 % | 47 % | 42 % | 41 % | 41 % |
| 2026-09-10 | 1041 | 100 % | 54 % | 51 % | 49 % | 49 % |
| 2026-09-17 | 1130 | 100 % | 58 % | 55 % | 54 % | 54 % |
| 2026-09-24 | 1277 | 100 % | 62 % | 59 % | 57 % | 57 % |

## Who is incomplete

- history of 5 transactions or fewer before the buy: 3318 records (49 %), funding 24h OBSERVED for 100 % of them.
- 6 to 99 before the buy: 2412 records (35 %), funding 24h OBSERVED for 3 % of them.
- 100 to 999 before the buy: 334 records (5 %), funding 24h OBSERVED for 6 % of them.
- 1,000 or more (capped) before the buy: 758 records (11 %), funding 24h OBSERVED for 7 % of them.

## Transactions that could not be reconstructed, and traps

- Earlier transactions returned null by the RPC and skipped by the collector: 0 (out of 23651 asked).
- Records whose balance before the buy is below the ticket: 6; records funded by a transfer inside the buy transaction itself: 6. For them the balance before the transaction is not the capital used; the transfer inside the transaction has to be added.
- Wrapped SOL is not in the native balance; a sniper paying with it would look poorer than it is.

## Cost of completing each variable

Calls deduplicated per wallet (a wallet sniping several launches shares its history). Time at 14 calls per second (three keys, measured), on the Helius budget the live detector also uses.

| variable | getTransaction | getSignaturesForAddress pages | records still unbounded | time |
|---|---:|---:|---:|---:|
| funding_1h | 43,895 | 4 | 4 | 0.9 h |
| funding_6h | 87,348 | 40 | 40 | 1.7 h |
| funding_24h | 119,723 | 58 | 58 | 2.4 h |
| funding_7d | 189,913 | 209 | 209 | 3.8 h |
| sol_spent_history | 275,665 | 758 | 758 | 5.5 h |
| n_history_trades | 275,665 | 758 | 758 | 5.5 h |

"Unbounded": the 1,000 signatures fetched before the buy do not reach back that far, so the count above is a floor and more pages are needed for those records.
