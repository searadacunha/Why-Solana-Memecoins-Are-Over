# C4. Is coordination another name for the existing structure?

| label | split | launches | snipers | bundle SOL | supply share | premium | market cap (log10 USD) | grouped |
|---|---|---:|---|---|---|---|---|---:|
| SHARED_FUNDER | TRAIN | 790 | 4 (4-4) | 81.2 (78.7-84.1) | 0.777 (0.773-0.785) | 3.8 (3.58-8.62) | 4.6 (4.57-5) | 31 % |
| SHARED_FUNDER | VAL | 454 | 4 (4-4) | 83.9 (79.6-84.6) | 0.781 (0.775-0.79) | 3.78 (3.59-7.78) | 4.67 (4.61-4.98) | 30 % |
| HIGH_SYNCHRONIZATION | TRAIN | 923 | 4 (4-4) | 80.8 (78.5-84) | 0.777 (0.772-0.783) | 3.77 (3.56-7.07) | 4.6 (4.57-4.89) | 28 % |
| HIGH_SYNCHRONIZATION | VAL | 555 | 4 (4-4) | 83.6 (79.5-84.2) | 0.78 (0.775-0.788) | 3.75 (3.57-4.18) | 4.66 (4.6-4.71) | 25 % |
| FUNDING_CLUSTER | TRAIN | 828 | 4 (4-4) | 82.3 (78.8-84.3) | 0.778 (0.774-0.788) | 3.78 (3.54-8.36) | 4.6 (4.57-4.98) | 30 % |
| FUNDING_CLUSTER | VAL | 507 | 4 (4-4) | 83.6 (79.3-84.5) | 0.781 (0.775-0.79) | 3.75 (3.54-6.4) | 4.66 (4.59-4.86) | 27 % |
| RECURRING_WALLET_CLUSTER | TRAIN | 472 | 4 (4-4) | 80.1 (78.4-84) | 0.778 (0.775-0.787) | 3.67 (3.47-3.86) | 4.58 (4.55-4.61) | 4 % |
| RECURRING_WALLET_CLUSTER | VAL | 232 | 4 (4-4) | 83 (79.7-84.1) | 0.786 (0.777-0.788) | 3.64 (3.44-3.77) | 4.64 (4.58-4.68) | 1 % |
| MULTI-SIGNAL_COORDINATION | TRAIN | 884 | 4 (4-4) | 80.9 (78.5-84.1) | 0.777 (0.772-0.785) | 3.78 (3.55-7.41) | 4.6 (4.57-4.91) | 28 % |
| MULTI-SIGNAL_COORDINATION | VAL | 520 | 4 (4-4) | 83.9 (79.8-84.5) | 0.781 (0.775-0.79) | 3.75 (3.56-5.54) | 4.67 (4.6-4.83) | 26 % |
| NO_SHARED_STRUCTURE | TRAIN | 28 | 5 (4-5) | 82.3 (78.7-85) | 0.782 (0.775-0.791) | 3.37 (2.83-3.81) | 4.55 (4.5-4.6) | 7 % |
| NO_SHARED_STRUCTURE | VAL | 25 | 5 (5-5) | 77.6 (76.5-78.1) | 0.773 (0.768-0.774) | 3.19 (2.91-3.26) | 4.52 (4.5-4.59) | 12 % |

## Redundancy rule (TRAIN boosting of snipers, bundle SOL, supply share, premium, market cap and grouped, measured on VALIDATION; Cohen's kappa with grouped on VALIDATION)

| label | ROC-AUC | kappa with grouped | redundant |
|---|---:|---:|---|
| SHARED_FUNDER | 0.644 | 0.13 | no |
| HIGH_SYNCHRONIZATION | 0.635 | 0.01 | no |
| FUNDING_CLUSTER | 0.674 | 0.12 | no |
| RECURRING_WALLET_CLUSTER | 0.787 | -0.36 | no |
| MULTI-SIGNAL_COORDINATION | 0.847 | 0.10 | no |
| NO_SHARED_STRUCTURE | 0.931 | -0.03 | yes |
