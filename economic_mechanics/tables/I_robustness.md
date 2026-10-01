# I. Robustness (p of each null, 1000 permutations)

| subset | split | launches | exits in one slot (share) | funding-time synchrony (spread, s) | one funding transaction for 2+ snipers | recurring sniper pairs | shared last funder | tokens consolidated to one recipient |
|---|---|---:|---|---|---|---|---|---|
| without the dominant operator | TRAIN | 801 | 0.0010 (x14.36) | 0.0010 (x0.48) | 0.0010 (x200.72) | 0.0010 (x15.47) | 0.0010 (x40.75) | 0.2328 (x1.40) |
| without the 10 most frequent sniper wallets | TRAIN | 989 | 0.0010 (x14.31) | 0.0010 (x0.43) | 0.0010 (x311.64) | 0.0010 (x17.15) | 0.0010 (x48.93) | 0.0310 (x2.01) |
| without the dominant operator | VAL | 536 | 0.0010 (x11.20) | 0.0010 (x0.01) | 0.0010 (x121.62) | 0.0010 (x15.82) | 0.0010 (x21.19) | 0.9281 (x0.44) |
| without the 10 most frequent sniper wallets | VAL | 609 | 0.0010 (x11.37) | 0.0010 (x0.02) | 0.0010 (x157.89) | 0.0010 (x19.80) | 0.0010 (x24.00) | 0.9151 (x0.49) |
| known non-hub last funders only: shared funder | TRAIN | 1015 | observed 289, null mean 3.6, p 0.0010 |
| known non-hub last funders only: shared funder | VAL | 642 | observed 157, null mean 2.7, p 0.0010 |
| genesis funders only: shared funder | TRAIN | 1015 | observed 243, null mean 1.2, p 0.0010 |
| genesis funders only: shared funder | VAL | 642 | observed 137, null mean 1.2, p 0.0010 |

## Inside the operators with 30 launches or more (both splits pooled)

| operator | launches | shared last funder | one funding tx | funding synchrony | exits in one slot |
|---|---:|---|---|---|---|
| operator 1 | 320 | 212 vs 11.7, p 0.001 | 35 vs 0.295, p 0.001 | 92.93 vs 714, p 0.001 | 0.6216 vs 0.0555, p 0.001 |
| operator 2 | 40 | 40 vs 4.43, p 0.001 | 0 vs 0, p 1.000 | 0 vs 1.31, p 0.001 | 0 vs 0.0311, p 1.000 |
| operator 3 | 40 | 40 vs 4.43, p 0.001 | 0 vs 0, p 1.000 | 1.6 vs 6.69, p 0.001 | n/a |
| operator 4 | 38 | 38 vs 4.3, p 0.001 | 0 vs 0, p 1.000 | 2.789 vs 20.5, p 0.001 | n/a |
