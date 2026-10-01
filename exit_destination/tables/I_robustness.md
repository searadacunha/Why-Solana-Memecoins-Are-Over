# I. Robustness and nulls (1000 permutations)

Each cell: observed | null mean [95 %] | percentile | p | effect.

## capital reaches the launch funder (events)

| subset | events (with a branch) | test |
|---|---:|---|
| full | 1457 (1161) | 0.508 | 0.0276 [0.0189, 0.0362] | 100 % | 0.0010 | x18.43 |
| without the dominant operator | 1156 (976) | 0.514 | 0.0381 [0.0277, 0.0492] | 100 % | 0.0010 | x13.50 |
| without the 10 most frequent exit wallets | 1407 (1114) | 0.487 | 0.0284 [0.0197, 0.0377] | 100 % | 0.0010 | x17.17 |
| known non-hub | 1457 (919) | 0.642 | 0.0439 [0.0326, 0.0566] | 100 % | 0.0010 | x14.61 |
| strict non-hub | 1457 (51) | 0.529 | 0.0978 [0.0392, 0.176] | 100 % | 0.0010 | x5.41 |
| TRAIN | 787 (531) | 0.486 | 0.0161 [0.00753, 0.0264] | 100 % | 0.0010 | x30.22 |
| VALIDATION | 670 (630) | 0.527 | 0.0822 [0.0635, 0.103] | 100 % | 0.0010 | x6.41 |
| operator k:21.13+21.08+ (301 events) | 301 (185) | 0.476 | 0.0324 [0.0108, 0.0595] | 100 % | 0.0010 | x14.69 |
| operator c:5MSpdabaEo18 (150 events) | 150 (150) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator k:20.80+20.21+ (150 events) | 150 (150) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |
| operator c:Fb2TAFf2zdgk (120 events) | 120 (120) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:HxYyavxib9P1 (120 events) | 120 (110) | 1 | 0.254 [0.182, 0.336] | 100 % | 0.0010 | x3.94 |
| operator k:22.04+21.96+ (120 events) | 120 (102) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:8uM3AeYfpA88 (60 events) | 60 (60) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |
| operator c:9TN2NEfg6vfi (60 events) | 60 (50) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:Gug21eQUwmZi (60 events) | 60 (60) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |
| operator k:21.59+21.27+ (56 events) | 56 (55) | 0.945 | 0.945 [0.945, 0.945] | 0 % | 1.0000 | x1.00 |
| operator c:2YKa6U61fozw (30 events) | 30 (24) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:BdE3C2tCtCwD (30 events) | 30 (12) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |

Classification: **ROBUST STRUCTURAL EVIDENCE**

## same first SOL destination repeated (exit wallets)

| subset | events (with a branch) | test |
|---|---:|---|
| full | 1457 (1161) | 0.765 | 0.427 [0.377, 0.477] | 100 % | 0.0010 | x1.79 |
| without the dominant operator | 1156 (976) | 0.819 | 0.45 [0.396, 0.507] | 100 % | 0.0010 | x1.82 |
| without the 10 most frequent exit wallets | 1407 (1114) | 0.796 | 0.445 [0.392, 0.496] | 100 % | 0.0010 | x1.79 |
| known non-hub | 1457 (919) | 0.765 | 0.427 [0.377, 0.477] | 100 % | 0.0010 | x1.79 |
| strict non-hub | 1457 (51) | 0.765 | 0.427 [0.377, 0.477] | 100 % | 0.0010 | x1.79 |
| TRAIN | 787 (531) | 0.559 | 0.381 [0.316, 0.449] | 100 % | 0.0010 | x1.47 |
| VALIDATION | 670 (630) | 1 | 0.876 [0.821, 0.927] | 100 % | 0.0010 | x1.14 |
| operator k:21.13+21.08+ (301 events) | 301 (185) | 0.814 | 0.496 [0.372, 0.605] | 100 % | 0.0010 | x1.64 |
| operator c:5MSpdabaEo18 (150 events) | 150 (150) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |
| operator k:20.80+20.21+ (150 events) | 150 (150) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |
| operator c:Fb2TAFf2zdgk (120 events) | 120 (120) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |
| operator c:HxYyavxib9P1 (120 events) | 120 (110) | 0 | 0.796 [0.667, 0.9] | 0 % | 1.0000 | x0.00 |
| operator k:22.04+21.96+ (120 events) | 120 (102) | 0.964 | 0.928 [0.857, 1] | 68 % | 0.3247 | x1.04 |
| operator c:8uM3AeYfpA88 (60 events) | 60 (60) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:9TN2NEfg6vfi (60 events) | 60 (50) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |
| operator c:Gug21eQUwmZi (60 events) | 60 (60) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator k:21.59+21.27+ (56 events) | 56 (55) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:2YKa6U61fozw (30 events) | 30 (24) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:BdE3C2tCtCwD (30 events) | 30 (12) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |

Classification: **ROBUST STRUCTURAL EVIDENCE**

## same terminal wallet in all events (exit wallets)

| subset | events (with a branch) | test |
|---|---:|---|
| full | 1457 (1161) | 0.36 | 0.0219 [0.0045, 0.0405] | 100 % | 0.0010 | x16.48 |
| without the dominant operator | 1156 (976) | 0.372 | 0.0335 [0.0105, 0.0576] | 100 % | 0.0010 | x11.10 |
| without the 10 most frequent exit wallets | 1407 (1114) | 0.377 | 0.0244 [0.00472, 0.0472] | 100 % | 0.0010 | x15.48 |
| known non-hub | 1457 (919) | 0.36 | 0.0219 [0.0045, 0.0405] | 100 % | 0.0010 | x16.48 |
| strict non-hub | 1457 (51) | 0.36 | 0.0219 [0.0045, 0.0405] | 100 % | 0.0010 | x16.48 |
| TRAIN | 787 (531) | 0.364 | 0.044 [0.0155, 0.0775] | 100 % | 0.0010 | x8.27 |
| VALIDATION | 670 (630) | 0.355 | 0.0559 [0.0215, 0.0968] | 100 % | 0.0010 | x6.34 |
| operator k:21.13+21.08+ (301 events) | 301 (185) | 0.756 | 0.127 [0.0488, 0.22] | 100 % | 0.0010 | x5.95 |
| operator c:5MSpdabaEo18 (150 events) | 150 (150) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator k:20.80+20.21+ (150 events) | 150 (150) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |
| operator c:Fb2TAFf2zdgk (120 events) | 120 (120) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:HxYyavxib9P1 (120 events) | 120 (110) | 0 | 0.0474 [0, 0.133] | 0 % | 1.0000 | x0.00 |
| operator k:22.04+21.96+ (120 events) | 120 (102) | 0.125 | 0.452 [0.292, 0.625] | 0 % | 1.0000 | x0.28 |
| operator c:8uM3AeYfpA88 (60 events) | 60 (60) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:9TN2NEfg6vfi (60 events) | 60 (50) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |
| operator c:Gug21eQUwmZi (60 events) | 60 (60) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator k:21.59+21.27+ (56 events) | 56 (55) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:2YKa6U61fozw (30 events) | 30 (24) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:BdE3C2tCtCwD (30 events) | 30 (12) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |

Classification: **ROBUST STRUCTURAL EVIDENCE**

## same return category in all events (exit wallets)

| subset | events (with a branch) | test |
|---|---:|---|
| full | 1457 (1161) | 0.515 | 0.0943 [0.0654, 0.123] | 100 % | 0.0010 | x5.46 |
| without the dominant operator | 1156 (976) | 0.471 | 0.118 [0.0837, 0.154] | 100 % | 0.0010 | x4.01 |
| without the 10 most frequent exit wallets | 1407 (1114) | 0.496 | 0.0872 [0.06, 0.116] | 100 % | 0.0010 | x5.69 |
| known non-hub | 1457 (919) | 0.515 | 0.0943 [0.0654, 0.123] | 100 % | 0.0010 | x5.46 |
| strict non-hub | 1457 (51) | 0.515 | 0.0943 [0.0654, 0.123] | 100 % | 0.0010 | x5.46 |
| TRAIN | 787 (531) | 0.75 | 0.154 [0.103, 0.206] | 100 % | 0.0010 | x4.87 |
| VALIDATION | 670 (630) | 0.268 | 0.0622 [0.0244, 0.106] | 100 % | 0.0010 | x4.32 |
| operator k:21.13+21.08+ (301 events) | 301 (185) | 0.86 | 0.206 [0.093, 0.326] | 100 % | 0.0010 | x4.18 |
| operator c:5MSpdabaEo18 (150 events) | 150 (150) | 0 | 0.319 [0.2, 0.433] | 0 % | 1.0000 | x0.00 |
| operator k:20.80+20.21+ (150 events) | 150 (150) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |
| operator c:Fb2TAFf2zdgk (120 events) | 120 (120) | 0.867 | 0.875 [0.867, 0.9] | 0 % | 1.0000 | x0.99 |
| operator c:HxYyavxib9P1 (120 events) | 120 (110) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |
| operator k:22.04+21.96+ (120 events) | 120 (102) | 0.107 | 0.228 [0.107, 0.357] | 1 % | 0.9870 | x0.47 |
| operator c:8uM3AeYfpA88 (60 events) | 60 (60) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:9TN2NEfg6vfi (60 events) | 60 (50) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |
| operator c:Gug21eQUwmZi (60 events) | 60 (60) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator k:21.59+21.27+ (56 events) | 56 (55) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:2YKa6U61fozw (30 events) | 30 (24) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:BdE3C2tCtCwD (30 events) | 30 (12) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |

Classification: **ROBUST STRUCTURAL EVIDENCE**

## same funder in all events (exit wallets)

| subset | events (with a branch) | test |
|---|---:|---|
| full | 1457 (1161) | 0.298 | 0.00273 [0, 0.0115] | 100 % | 0.0010 | x108.94 |
| without the dominant operator | 1156 (976) | 0.341 | 0.000171 [0, 0.00461] | 100 % | 0.0010 | x2000.00 |
| without the 10 most frequent exit wallets | 1407 (1114) | 0.31 | 0.00325 [0, 0.0119] | 100 % | 0.0010 | x95.24 |
| known non-hub | 1457 (919) | 0.298 | 0.00273 [0, 0.0115] | 100 % | 0.0010 | x108.94 |
| strict non-hub | 1457 (51) | 0.298 | 0.00273 [0, 0.0115] | 100 % | 0.0010 | x108.94 |
| TRAIN | 787 (531) | 0.104 | 0.0035 [0, 0.0149] | 100 % | 0.0010 | x29.85 |
| VALIDATION | 670 (630) | 0.5 | 0.0013 [0, 0.00781] | 100 % | 0.0010 | x383.23 |
| operator k:21.13+21.08+ (301 events) | 301 (185) | 0.125 | 0.00863 [0, 0.0312] | 100 % | 0.0010 | x14.49 |
| operator c:5MSpdabaEo18 (150 events) | 150 (150) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |
| operator k:20.80+20.21+ (150 events) | 150 (150) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |
| operator c:Fb2TAFf2zdgk (120 events) | 120 (120) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |
| operator c:HxYyavxib9P1 (120 events) | 120 (110) | 0 | 0.014 [0, 0.0667] | 0 % | 1.0000 | x0.00 |
| operator k:22.04+21.96+ (120 events) | 120 (102) | 0 | 0.0185 [0, 0.0667] | 0 % | 1.0000 | x0.00 |
| operator c:8uM3AeYfpA88 (60 events) | 60 (60) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:9TN2NEfg6vfi (60 events) | 60 (50) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:Gug21eQUwmZi (60 events) | 60 (60) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator k:21.59+21.27+ (56 events) | 56 (55) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:2YKa6U61fozw (30 events) | 30 (24) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:BdE3C2tCtCwD (30 events) | 30 (12) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |

Classification: **ROBUST STRUCTURAL EVIDENCE**

## same cluster in all events (exit wallets)

| subset | events (with a branch) | test |
|---|---:|---|
| full | 1457 (1161) | 0.443 | 0.0031 [0, 0.01] | 100 % | 0.0010 | x142.86 |
| without the dominant operator | 1156 (976) | 0.641 | 0.00961 [0, 0.0239] | 100 % | 0.0010 | x66.75 |
| without the 10 most frequent exit wallets | 1407 (1114) | 0.459 | 0.00303 [0, 0.0103] | 100 % | 0.0010 | x151.31 |
| known non-hub | 1457 (919) | 0.443 | 0.0031 [0, 0.01] | 100 % | 0.0010 | x142.86 |
| strict non-hub | 1457 (51) | 0.443 | 0.0031 [0, 0.01] | 100 % | 0.0010 | x142.86 |
| TRAIN | 787 (531) | 0.378 | 0.00893 [0, 0.0233] | 100 % | 0.0010 | x42.32 |
| VALIDATION | 670 (630) | 0.531 | 0.0013 [0, 0.00781] | 100 % | 0.0010 | x407.19 |
| operator k:21.13+21.08+ (301 events) | 301 (185) | 0.545 | 0.142 [0.0758, 0.212] | 100 % | 0.0010 | x3.84 |
| operator c:5MSpdabaEo18 (150 events) | 150 (150) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |
| operator k:20.80+20.21+ (150 events) | 150 (150) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |
| operator c:Fb2TAFf2zdgk (120 events) | 120 (120) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |
| operator c:HxYyavxib9P1 (120 events) | 120 (110) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |
| operator k:22.04+21.96+ (120 events) | 120 (102) | 0 | 0.147 [0.0333, 0.267] | 0 % | 1.0000 | x0.00 |
| operator c:8uM3AeYfpA88 (60 events) | 60 (60) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:9TN2NEfg6vfi (60 events) | 60 (50) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |
| operator c:Gug21eQUwmZi (60 events) | 60 (60) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator k:21.59+21.27+ (56 events) | 56 (55) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:2YKa6U61fozw (30 events) | 30 (24) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:BdE3C2tCtCwD (30 events) | 30 (12) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |

Classification: **ROBUST STRUCTURAL EVIDENCE**

## capital reaches the cluster's deployer network (events)

| subset | events (with a branch) | test |
|---|---:|---|
| full | 1457 (1161) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| without the dominant operator | 1156 (976) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| without the 10 most frequent exit wallets | 1407 (1114) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| known non-hub | 1457 (919) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| strict non-hub | 1457 (51) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| TRAIN | 787 (531) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| VALIDATION | 670 (630) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator k:21.13+21.08+ (301 events) | 301 (185) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:5MSpdabaEo18 (150 events) | 150 (150) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator k:20.80+20.21+ (150 events) | 150 (150) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:Fb2TAFf2zdgk (120 events) | 120 (120) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:HxYyavxib9P1 (120 events) | 120 (110) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator k:22.04+21.96+ (120 events) | 120 (102) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:8uM3AeYfpA88 (60 events) | 60 (60) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:9TN2NEfg6vfi (60 events) | 60 (50) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:Gug21eQUwmZi (60 events) | 60 (60) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator k:21.59+21.27+ (56 events) | 56 (55) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:2YKa6U61fozw (30 events) | 30 (24) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:BdE3C2tCtCwD (30 events) | 30 (12) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |

Classification: **NULL-COMPATIBLE**

## capital funds a later launch (events)

| subset | events (with a branch) | test |
|---|---:|---|
| full | 1457 (1161) | 0.523 | 0.291 [0.276, 0.307] | 100 % | 0.0010 | x1.80 |
| without the dominant operator | 1156 (976) | 0.463 | 0.269 [0.252, 0.286] | 100 % | 0.0010 | x1.72 |
| without the 10 most frequent exit wallets | 1407 (1114) | 0.512 | 0.287 [0.271, 0.303] | 100 % | 0.0010 | x1.78 |
| known non-hub | 1457 (919) | 0.509 | 0.301 [0.283, 0.319] | 100 % | 0.0010 | x1.69 |
| strict non-hub | 1457 (51) | 0.49 | 0.381 [0.314, 0.451] | 100 % | 0.0040 | x1.29 |
| TRAIN | 787 (531) | 0.616 | 0.359 [0.333, 0.384] | 100 % | 0.0010 | x1.72 |
| VALIDATION | 670 (630) | 0.444 | 0.272 [0.251, 0.292] | 100 % | 0.0010 | x1.63 |
| operator k:21.13+21.08+ (301 events) | 301 (185) | 0.838 | 0.612 [0.573, 0.654] | 100 % | 0.0010 | x1.37 |
| operator c:5MSpdabaEo18 (150 events) | 150 (150) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator k:20.80+20.21+ (150 events) | 150 (150) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |
| operator c:Fb2TAFf2zdgk (120 events) | 120 (120) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:HxYyavxib9P1 (120 events) | 120 (110) | 0.745 | 0.569 [0.509, 0.618] | 100 % | 0.0010 | x1.31 |
| operator k:22.04+21.96+ (120 events) | 120 (102) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:8uM3AeYfpA88 (60 events) | 60 (60) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |
| operator c:9TN2NEfg6vfi (60 events) | 60 (50) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |
| operator c:Gug21eQUwmZi (60 events) | 60 (60) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |
| operator k:21.59+21.27+ (56 events) | 56 (55) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:2YKa6U61fozw (30 events) | 30 (24) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:BdE3C2tCtCwD (30 events) | 30 (12) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |

Classification: **ROBUST STRUCTURAL EVIDENCE**

## fixed sniper-to-exit-wallet pairs (exit wallets, corpus)

| subset | events (with a branch) | test |
|---|---:|---|
| full | 1457 (1161) | 0.42 | 2e-05 [0, 0] | 100 % | 0.0010 | x21000.00 |
| without the dominant operator | 1156 (976) | 0.36 | 2.57e-05 [0, 0] | 100 % | 0.0010 | x14000.00 |
| without the 10 most frequent exit wallets | 1407 (1114) | 0.434 | 2.41e-05 [0, 0] | 100 % | 0.0010 | x18000.00 |
| known non-hub | 1457 (919) | 0.42 | 2e-05 [0, 0] | 100 % | 0.0010 | x21000.00 |
| strict non-hub | 1457 (51) | 0.42 | 2e-05 [0, 0] | 100 % | 0.0010 | x21000.00 |
| TRAIN | 787 (531) | 0.36 | 0.000134 [0, 0] | 100 % | 0.0010 | x2695.65 |
| VALIDATION | 670 (630) | 0.405 | 0 [0, 0] | 100 % | 0.0010 | n/a |
| operator k:21.13+21.08+ (301 events) | 301 (185) | 0.266 | 0.000532 [0, 0.00917] | 100 % | 0.0010 | x500.00 |
| operator c:5MSpdabaEo18 (150 events) | 150 (150) | 0.867 | 0 [0, 0] | 100 % | 0.0010 | n/a |
| operator k:20.80+20.21+ (150 events) | 150 (150) | 1 | 0 [0, 0] | 100 % | 0.0010 | n/a |
| operator c:Fb2TAFf2zdgk (120 events) | 120 (120) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:HxYyavxib9P1 (120 events) | 120 (110) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator k:22.04+21.96+ (120 events) | 120 (102) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:8uM3AeYfpA88 (60 events) | 60 (60) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:9TN2NEfg6vfi (60 events) | 60 (50) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:Gug21eQUwmZi (60 events) | 60 (60) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator k:21.59+21.27+ (56 events) | 56 (55) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:2YKa6U61fozw (30 events) | 30 (24) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:BdE3C2tCtCwD (30 events) | 30 (12) | 1 | 0 [0, 0] | 100 % | 0.0010 | n/a |

Classification: **ROBUST STRUCTURAL EVIDENCE**

## branches ending in H1

| subset | events (with a branch) | test |
|---|---:|---|
| full | 1457 (1161) | 0.493 | 0.0248 [0.0172, 0.0328] | 100 % | 0.0010 | x19.86 |
| without the dominant operator | 1156 (976) | 0.5 | 0.0351 [0.0254, 0.0462] | 100 % | 0.0010 | x14.27 |
| without the 10 most frequent exit wallets | 1407 (1114) | 0.472 | 0.0253 [0.0171, 0.0341] | 100 % | 0.0010 | x18.67 |
| known non-hub | 1457 (919) | 0.644 | 0.0422 [0.0306, 0.0531] | 100 % | 0.0010 | x15.25 |
| strict non-hub | 1457 (51) | 0.465 | 0.088 [0.0423, 0.141] | 100 % | 0.0010 | x5.28 |
| TRAIN | 787 (531) | 0.457 | 0.0146 [0.00626, 0.0235] | 100 % | 0.0010 | x31.21 |
| VALIDATION | 670 (630) | 0.529 | 0.0833 [0.0655, 0.103] | 100 % | 0.0010 | x6.35 |
| operator k:21.13+21.08+ (301 events) | 301 (185) | 0.457 | 0.0282 [0.00913, 0.0502] | 100 % | 0.0010 | x16.19 |
| operator c:5MSpdabaEo18 (150 events) | 150 (150) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator k:20.80+20.21+ (150 events) | 150 (150) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |
| operator c:Fb2TAFf2zdgk (120 events) | 120 (120) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:HxYyavxib9P1 (120 events) | 120 (110) | 1 | 0.259 [0.179, 0.341] | 100 % | 0.0010 | x3.86 |
| operator k:22.04+21.96+ (120 events) | 120 (102) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:8uM3AeYfpA88 (60 events) | 60 (60) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |
| operator c:9TN2NEfg6vfi (60 events) | 60 (50) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:Gug21eQUwmZi (60 events) | 60 (60) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |
| operator k:21.59+21.27+ (56 events) | 56 (55) | 0.946 | 0.946 [0.946, 0.946] | 0 % | 1.0000 | x1.00 |
| operator c:2YKa6U61fozw (30 events) | 30 (24) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:BdE3C2tCtCwD (30 events) | 30 (12) | 1 | 1 [1, 1] | 0 % | 1.0000 | x1.00 |

Classification: **ROBUST STRUCTURAL EVIDENCE**

## branches ending in H2

| subset | events (with a branch) | test |
|---|---:|---|
| full | 1457 (1161) | 0.00547 | 0.00806 [0.00391, 0.0133] | 7 % | 0.9281 | x0.68 |
| without the dominant operator | 1156 (976) | 0.0066 | 0.00691 [0.00283, 0.0113] | 39 % | 0.6144 | x0.95 |
| without the 10 most frequent exit wallets | 1407 (1114) | 0.00569 | 0.00623 [0.00244, 0.0106] | 35 % | 0.6494 | x0.91 |
| known non-hub | 1457 (919) | 0.00714 | 0.0113 [0.0051, 0.0184] | 5 % | 0.9500 | x0.63 |
| strict non-hub | 1457 (51) | 0 | 0.0608 [0.0282, 0.113] | 0 % | 1.0000 | x0.00 |
| TRAIN | 787 (531) | 0.00626 | 0.0285 [0.0172, 0.0407] | 0 % | 1.0000 | x0.22 |
| VALIDATION | 670 (630) | 0.00468 | 0.000388 [0, 0.00156] | 100 % | 0.0010 | x12.05 |
| operator k:21.13+21.08+ (301 events) | 301 (185) | 0 | 0.118 [0.0868, 0.146] | 0 % | 1.0000 | x0.00 |
| operator c:5MSpdabaEo18 (150 events) | 150 (150) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator k:20.80+20.21+ (150 events) | 150 (150) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:Fb2TAFf2zdgk (120 events) | 120 (120) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:HxYyavxib9P1 (120 events) | 120 (110) | 0 | 0.37 [0.317, 0.423] | 0 % | 1.0000 | x0.00 |
| operator k:22.04+21.96+ (120 events) | 120 (102) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:8uM3AeYfpA88 (60 events) | 60 (60) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:9TN2NEfg6vfi (60 events) | 60 (50) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:Gug21eQUwmZi (60 events) | 60 (60) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator k:21.59+21.27+ (56 events) | 56 (55) | 0.0536 | 0.0536 [0.0536, 0.0536] | 0 % | 1.0000 | x1.00 |
| operator c:2YKa6U61fozw (30 events) | 30 (24) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:BdE3C2tCtCwD (30 events) | 30 (12) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |

Classification: **NULL-COMPATIBLE**

## branches ending in H3

| subset | events (with a branch) | test |
|---|---:|---|
| full | 1457 (1161) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| without the dominant operator | 1156 (976) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| without the 10 most frequent exit wallets | 1407 (1114) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| known non-hub | 1457 (919) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| strict non-hub | 1457 (51) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| TRAIN | 787 (531) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| VALIDATION | 670 (630) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator k:21.13+21.08+ (301 events) | 301 (185) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:5MSpdabaEo18 (150 events) | 150 (150) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator k:20.80+20.21+ (150 events) | 150 (150) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:Fb2TAFf2zdgk (120 events) | 120 (120) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:HxYyavxib9P1 (120 events) | 120 (110) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator k:22.04+21.96+ (120 events) | 120 (102) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:8uM3AeYfpA88 (60 events) | 60 (60) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:9TN2NEfg6vfi (60 events) | 60 (50) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:Gug21eQUwmZi (60 events) | 60 (60) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator k:21.59+21.27+ (56 events) | 56 (55) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:2YKa6U61fozw (30 events) | 30 (24) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |
| operator c:BdE3C2tCtCwD (30 events) | 30 (12) | 0 | 0 [0, 0] | 0 % | 1.0000 | n/a |

Classification: **NULL-COMPATIBLE**

## Time (ISO weeks of the receipt)

| week | events | with a branch | reaches the funder | same cluster or funder (H1+H2 branches) | deployer network | funds a later launch |
|---|---:|---:|---:|---:|---:|---:|
| 2026-W34 | 68 | 33 | 61 % | 43 % | 0 % | 21 % |
| 2026-W35 | 169 | 78 | 94 % | 95 % | 0 % | 58 % |
| 2026-W36 | 200 | 146 | 84 % | 84 % | 0 % | 71 % |
| 2026-W37 | 350 | 274 | 15 % | 13 % | 0 % | 63 % |
| 2026-W38 | 370 | 334 | 48 % | 48 % | 0 % | 48 % |
| 2026-W39 | 120 | 120 | 100 % | 100 % | 0 % | 100 % |
| 2026-W40 | 180 | 176 | 30 % | 31 % | 0 % | 0 % |
