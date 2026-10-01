# C2. Null models, population level (200 permutations each, inside each split)

Observed | null mean | percentile of the observed in the null | empirical p (one-sided, towards coordination) | 95 % null interval.

| measure | TRAIN | VALIDATION |
|---|---|---|
| shared funder, N1 wallets shuffled | 790 | 17.73 | 100 % | 0.005 | [9, 26] | 454 | 20.19 | 100 % | 0.005 | [11, 29] |
| shared funder, N2 funders shuffled | 790 | 15.46 | 100 % | 0.005 | [8, 23] | 454 | 18.75 | 100 % | 0.005 | [10, 27] |
| funding cluster, N2 funders shuffled | 828 | 1.49 | 100 % | 0.005 | [0, 4] | 507 | 0.94 | 100 % | 0.005 | [0, 3] |
| funding spread, N3 timing shuffled | 480.6 | 1125 | 0 % | 0.005 | [1114, 1136] | 41.95 | 1219 | 0 % | 0.005 | [1179, 1237] |
| early same-slot share, N3 | 0.7859 | 0.7059 | 100 % | 0.005 | [0.7005, 0.7119] | 0.7537 | 0.7237 | 100 % | 0.005 | [0.7164, 0.7303] |
| identical tickets, N4 | 106 | 46.27 | 100 % | 0.005 | [33, 58] | 20 | 24.77 | 12 % | 0.881 | [15, 34] |
| near-identical tickets, N4 | 637 | 426.1 | 100 % | 0.005 | [398, 453] | 352 | 243.6 | 100 % | 0.005 | [220, 267] |
| round tickets, N4 | 3 | 6.6 | 3 % | 0.970 | [2, 12] | 0 | 0.36 | 0 % | 1.000 | [0, 2] |
| recurring sniper pairs, N5 | 664 | 44.47 | 100 % | 0.005 | [31, 59] | 368 | 36.26 | 100 % | 0.005 | [26, 48] |

Wallets in recurring sniper pairs: TRAIN 416, VALIDATION 234.
