# C3. Labels per launch (per-launch nulls of 200 draws from the launch's own split)

| label | TRAIN launches | VALIDATION launches | launches where it can be decided, TRAIN / VAL |
|---|---:|---:|---|
| SHARED_FUNDER | 790 (83.7 %) | 454 (77.6 %) | 944 / 585 |
| HIGH_SYNCHRONIZATION | 923 (98.3 %) | 555 (97.5 %) | 939 / 569 |
| FUNDING_CLUSTER | 828 (81.6 %) | 507 (79.0 %) | 1015 / 642 |
| RECURRING_WALLET_CLUSTER | 472 (46.5 %) | 232 (36.1 %) | 1015 / 642 |
| MULTI-SIGNAL_COORDINATION | 884 (87.1 %) | 520 (81.0 %) | 1015 / 642 |
| NO_SHARED_STRUCTURE | 28 (2.8 %) | 25 (3.9 %) | 1015 / 642 |

## Are the four dimensions distinct? Phi on TRAIN (launches where both are decided)

| | SHARED_FUNDER | HIGH_SYNCHRONIZATION | FUNDING_CLUSTER | RECURRING_WALLET_CLUSTER |
|---|---:|---:|---:|---:|
| SHARED_FUNDER | 1.00 | 0.28 | 0.95 | -0.00 |
| HIGH_SYNCHRONIZATION | 0.28 | 1.00 | 0.21 | 0.11 |
| FUNDING_CLUSTER | 0.95 | 0.21 | 1.00 | -0.03 |
| RECURRING_WALLET_CLUSTER | -0.00 | 0.11 | -0.03 | 1.00 |

Score (number of the four labels) allowed: at least three pairs of dimensions have |phi| below 0.5.
- TRAIN: score 0: 28, score 1: 103, score 2: 97, score 3: 432, score 4: 355.
- VAL: score 0: 25, score 1: 97, score 2: 74, score 3: 281, score 4: 165.
