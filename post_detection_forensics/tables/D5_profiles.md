# D5. Profiles (defined in advance, TRAIN-median thresholds {'b_top1': 0.2586, 'b_ticket_cv': 0.0308, 'w_early_log_prior_n': 3.0004, 'w_early_fresh': 0.0}; not ranked)

| profile | split | N | 2x 5 min | 2x 15 min | 2x 1 h | median time to 2x (s) | MFE 15 min q25 / median / q75 / q90 |
|---|---|---:|---|---|---|---:|---|
| 1 concentrated bundle (b_top1 > TRAIN median) | TRAIN | 498 | 6.2 % (29/464) [4.4-8.8] | 17.0 % (75/441) [13.8-20.8] | 29.2 % (112/383) [24.9-34.0] | 741 | 1.14 / 1.43 / 1.91 / 2.72 |
| 1 concentrated bundle (b_top1 > TRAIN median) | VAL | 362 | 11.1 % (39/350) [8.3-14.9] | 23.1 % (78/337) [19.0-27.9] | 35.4 % (104/294) [30.1-41.0] | 461 | 1.14 / 1.38 / 2.10 / 3.58 |
| 2 distributed bundle (independent share 1, ticket CV < median) | TRAIN | 129 | 14.0 % (16/114) [8.8-21.6] | 24.8 % (27/109) [17.6-33.6] | 27.1 % (26/96) [19.2-36.7] | 290 | 1.10 / 1.53 / 2.17 / 3.17 |
| 2 distributed bundle (independent share 1, ticket CV < median) | VAL | 14 | 28.6 % (4/14) [11.7-54.6] | 38.5 % (5/13) [17.7-64.5] | 30.0 % (3/10) [10.8-60.3] | 99 | 1.09 / 1.93 / 2.54 / 2.77 |
| 3 common funding (one funder >= 2 core wallets) | TRAIN | 810 | 10.3 % (79/768) [8.3-12.6] | 21.9 % (160/730) [19.1-25.1] | 29.2 % (181/619) [25.8-32.9] | 439 | 1.15 / 1.50 / 2.13 / 2.82 |
| 3 common funding (one funder >= 2 core wallets) | VAL | 579 | 10.1 % (57/566) [7.9-12.8] | 23.7 % (130/549) [20.3-27.4] | 30.1 % (145/482) [26.2-34.3] | 430 | 1.17 / 1.47 / 2.15 / 3.30 |
| 4 distributed funding (>= 3 distinct funders) | TRAIN | 244 | 11.6 % (26/225) [8.0-16.4] | 22.7 % (48/211) [17.6-28.9] | 23.8 % (43/181) [18.1-30.5] | 302 | 1.21 / 1.64 / 2.18 / 2.92 |
| 4 distributed funding (>= 3 distinct funders) | VAL | 248 | 11.5 % (28/243) [8.1-16.1] | 27.5 % (65/236) [22.2-33.6] | 25.2 % (52/206) [19.8-31.6] | 351 | 1.23 / 1.63 / 2.37 / 3.65 |
| 5 experienced early wallets (history > median) | TRAIN | 0 | n/a (0) | n/a (0) | n/a (0) | nan | nan / nan / nan / nan |
| 5 experienced early wallets (history > median) | VAL | 0 | n/a (0) | n/a (0) | n/a (0) | nan | nan / nan / nan / nan |
| 6 fresh early wallets (fresh share > median) | TRAIN | 0 | n/a (0) | n/a (0) | n/a (0) | nan | nan / nan / nan / nan |
| 6 fresh early wallets (fresh share > median) | VAL | 0 | n/a (0) | n/a (0) | n/a (0) | nan | nan / nan / nan / nan |
| all alerts | TRAIN | 1015 | 10.8 % (102/944) [9.0-12.9] | 22.4 % (201/896) [19.8-25.3] | 28.7 % (221/769) [25.7-32.0] | 413 | 1.15 / 1.51 / 2.15 / 2.88 |
| all alerts | VAL | 642 | 12.0 % (75/626) [9.7-14.8] | 26.4 % (160/606) [23.0-30.1] | 32.4 % (171/528) [28.5-36.5] | 422 | 1.18 / 1.51 / 2.32 / 3.62 |
