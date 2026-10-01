# G. Recurrence across launches

- Sniper wallets: 3852; in 2 launches or more: 651; launches per recurring wallet 4 / 2 / 6 / 11 / 2 / 47 (N 651).
- Hours between two launches of the same sniper: 0.376 / 0.283 / 0.672 / 3.73 / 0.00872 / 370 (N 2970).
- Non-hub funders: 1053; funding snipers in 2 launches or more: 199.
- The same funder funding the same sniper in 2 launches or more: 428 relations.
- Deployers: 1645; deploying 2 launches or more: 11.
- Recurring sniper pairs: 1014; distinct deployers behind a recurring pair: 4 / 2 / 6 / 11 / 1 / 30 (N 1014).

## Clusters (wallets joined by co-sniping, non-hub funding, deployer-to-funder transfers, common sources; information at or before each launch)

- Clusters holding a launch: 320; holding 2 launches or more: 176, with 1513 launches.
- Launches per multi-launch cluster: 4 / 3 / 8 / 14 / 2 / 279 (N 176).
- Multi-launch clusters with TRAIN and VALIDATION launches: 10.
- Operator clusters of the previous studies spanned per multi-launch cluster: 1 / 1 / 1 / 3 / 1 / 15 (N 176).

## Behavioral fingerprints of the clusters with 10 launches or more

| cluster | launches TRAIN / VAL | dominant architecture | one-tx funding | funding s before buy | snipers | ticket SOL | supply share | exited by +30 s | exits by transfer | proceeds to first funder | days between launches | operator clusters |
|---|---|---|---:|---|---:|---|---|---:|---:|---|---|---:|
| 1 | 174 / 105 | UNRESOLVED (45 %) | 12 % | 289 | 4 | 19.4 | 0.778 | 91 % | 81 % | 142 of 253 | 0.02 | 14 |
| 2 | 58 / 0 | A (100 %) | 0 % | 1 | 4 | 24.7 | 0.759 | 23 % | 0 % | n/a | 0.06 | 14 |
| 3 | 30 / 24 | B (61 %) | 2 % | 306 | 4 | 19.6 | 0.776 | 85 % | 72 % | 27 of 30 | 0.02 | 7 |
| 4 | 47 / 5 | A (100 %) | 0 % | 1 | 4 | 24.7 | 0.759 | 27 % | 0 % | n/a | 0.08 | 15 |
| 5 | 0 / 38 | A (100 %) | 0 % | 2 | 4 | 20.1 | 0.759 | 27 % | 0 % | n/a | 0.05 | 6 |
| 6 | 21 / 2 | A (100 %) | 0 % | 1 | 4 | 24.7 | 0.790 | 67 % | 0 % | n/a | 0.24 | 2 |
| 7 | 23 / 0 | B (100 %) | 0 % | 314 | 4 | 18.9 | 0.765 | 96 % | 100 % | n/a | 0.01 | 1 |
| 8 | 19 / 0 | A (100 %) | 0 % | 1 | 4 | 19.8 | 0.776 | 32 % | 0 % | n/a | 0.20 | 13 |
| 9 | 16 / 3 | B (79 %) | 0 % | 366 | 4 | 19.6 | 0.775 | 73 % | 91 % | 40 of 40 | 0.02 | 6 |
| 10 | 0 / 18 | A (100 %) | 0 % | 1 | 4 | 14.8 | 0.790 | 82 % | 0 % | n/a | 0.07 | 1 |
| 11 | 0 / 18 | B (100 %) | 0 % | 233 | 4 | 20.8 | 0.787 | 100 % | 100 % | 68 of 68 | 0.01 | 1 |
| 12 | 17 / 0 | A (100 %) | 0 % | 1 | 4 | 19.8 | 0.793 | 74 % | 0 % | n/a | 0.45 | 9 |
| 13 | 17 / 0 | B (100 %) | 0 % | 292 | 4 | 20.8 | 0.788 | 100 % | 100 % | 60 of 60 | 0.01 | 1 |
| 14 | 10 / 6 | B (88 %) | 0 % | 294 | 4 | 20.9 | 0.785 | 81 % | 100 % | 28 of 30 | 0.02 | 2 |
| 15 | 13 / 3 | A (100 %) | 0 % | 1 | 4 | 21.7 | 0.759 | 80 % | 0 % | n/a | 0.55 | 10 |
| 16 | 0 / 16 | E (100 %) | 0 % | 168 | 4 | 20.8 | 0.788 | 100 % | 100 % | 40 of 40 | 0.01 | 1 |
| 17 | 0 / 16 | E (100 %) | 0 % | 96 | 4 | 19.5 | 0.779 | 100 % | 100 % | n/a | 0.02 | 2 |
| 18 | 0 / 15 | A (100 %) | 0 % | 2 | 4 | 19.8 | 0.790 | 27 % | 0 % | n/a | 0.14 | 6 |
| 19 | 14 / 0 | E (100 %) | 100 % | 190 | 4 | 18.5 | 0.762 | 100 % | 100 % | 0 of 51 | 0.02 | 1 |
| 20 | 0 / 14 | B (100 %) | 0 % | 74 | 4 | 19.2 | 0.775 | 100 % | 100 % | 25 of 29 | 0.01 | 1 |
| 21 | 0 / 14 | B (100 %) | 0 % | 315 | 4 | 20.4 | 0.781 | 100 % | 100 % | n/a | 0.01 | 1 |
| 22 | 13 / 0 | B (92 %) | 8 % | 301 | 4 | 20.7 | 0.788 | 92 % | 100 % | 42 of 46 | 0.01 | 1 |
| 23 | 13 / 0 | B (100 %) | 0 % | 242 | 4 | 19.1 | 0.777 | 100 % | 100 % | 12 of 28 | 0.01 | 1 |
| 24 | 0 / 13 | A (100 %) | 0 % | 1 | 4 | 19.8 | 0.793 | 21 % | 0 % | n/a | 0.24 | 5 |
| 25 | 12 / 0 | B (83 %) | 0 % | 246 | 4 | 19.6 | 0.773 | 100 % | 92 % | n/a | 0.01 | 1 |
| 26 | 12 / 0 | A (100 %) | 0 % | 1 | 4 | 19.8 | 0.759 | 27 % | 0 % | n/a | 0.10 | 6 |
| 27 | 12 / 0 | B (92 %) | 0 % | 370 | 4 | 19.6 | 0.777 | 85 % | 98 % | 16 of 16 | 0.02 | 1 |
| 28 | 0 / 12 | E (100 %) | 0 % | 120 | 4 | 19.5 | 0.778 | 100 % | 100 % | n/a | 0.01 | 1 |
| 29 | 0 / 12 | B (83 %) | 0 % | 439 | 4 | 20.2 | 0.786 | 96 % | 100 % | n/a | 0.02 | 2 |
| 30 | 11 / 0 | B (82 %) | 0 % | 381 | 4 | 19.6 | 0.776 | 93 % | 98 % | 8 of 8 | 0.01 | 1 |
| 31 | 9 / 2 | C (82 %) | 100 % | 9 | 4 | 21.3 | 0.793 | 7 % | 100 % | n/a | 1.92 | 1 |
| 32 | 11 / 0 | B (36 %) | 45 % | 192 | 4 | 18.9 | 0.767 | 90 % | 84 % | 0 of 8 | 0.02 | 2 |
| 33 | 11 / 0 | B (100 %) | 0 % | 254 | 4 | 19.1 | 0.775 | 100 % | 100 % | 12 of 22 | 0.02 | 1 |
| 34 | 0 / 11 | B (100 %) | 0 % | 469 | 4 | 19.6 | 0.776 | 48 % | 76 % | 2 of 2 | 0.01 | 1 |
| 35 | 0 / 10 | B (100 %) | 0 % | 135 | 4 | 19.6 | 0.780 | 100 % | 100 % | n/a | 0.02 | 2 |
