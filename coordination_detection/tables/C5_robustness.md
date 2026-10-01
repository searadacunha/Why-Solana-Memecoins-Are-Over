# C5. Robustness and operators

Population null p of each label's raw criterion (the C2 test), and the label's prevalence, in each subset.

## Splits

| subset | launches | SHARED_FUNDER | HIGH_SYNCHRONIZATION | FUNDING_CLUSTER | RECURRING_WALLET_CLUSTER |
|---|---:|---|---|---|---|
| TRAIN | 1015 | 790 (78 %), p 0.005 | 923 (91 %), p 0.005 | 828 (82 %), p 0.005 | 472 (47 %), p 0.005 |
| VAL | 642 | 454 (71 %), p 0.005 | 555 (86 %), p 0.005 | 507 (79 %), p 0.005 | 232 (36 %), p 0.005 |

## Weeks

| subset | launches | SHARED_FUNDER | HIGH_SYNCHRONIZATION | FUNDING_CLUSTER | RECURRING_WALLET_CLUSTER |
|---|---:|---|---|---|---|
| 2026-08-21 TRAIN | 246 | 190 (77 %), p 0.005 | 210 (85 %), p 0.005 | 213 (87 %), p 0.005 | 105 (43 %), p 0.005 |
| 2026-08-27 TRAIN | 225 | 183 (81 %), p 0.005 | 197 (88 %), p 0.005 | 194 (86 %), p 0.005 | 103 (46 %), p 0.005 |
| 2026-09-03 TRAIN | 350 | 268 (77 %), p 0.005 | 328 (94 %), p 0.005 | 269 (77 %), p 0.005 | 181 (52 %), p 0.005 |
| 2026-09-10 TRAIN | 258 | 197 (76 %), p 0.005 | 247 (96 %), p 0.010 | 201 (78 %), p 0.005 | 110 (43 %), p 0.005 |
| 2026-09-17 VAL | 271 | 214 (79 %), p 0.005 | 230 (85 %), p 0.005 | 239 (88 %), p 0.005 | 97 (36 %), p 0.005 |
| 2026-09-24 VAL | 307 | 192 (63 %), p 0.005 | 266 (87 %), p 0.005 | 219 (71 %), p 0.005 | 108 (35 %), p 0.005 |

## Number of snipers

| subset | launches | SHARED_FUNDER | HIGH_SYNCHRONIZATION | FUNDING_CLUSTER | RECURRING_WALLET_CLUSTER |
|---|---:|---|---|---|---|
| 4, TRAIN | 930 | 785 (84 %), p 0.005 | 912 (98 %), p 0.005 | 781 (84 %), p 0.005 | 431 (46 %), p 0.005 |
| 5, TRAIN | 76 | 2 (3 %), p 0.920 | 6 (8 %), p 0.005 | 44 (58 %), p 0.005 | 40 (53 %), p 0.005 |
| 6+, TRAIN | 9 | too few | too few | too few | too few |
| 4, VAL | 554 | 445 (80 %), p 0.005 | 550 (99 %), p 0.005 | 445 (80 %), p 0.005 | 207 (37 %), p 0.005 |
| 5, VAL | 77 | 8 (10 %), p 0.502 | 4 (5 %), p 0.005 | 52 (68 %), p 0.005 | 17 (22 %), p 0.005 |
| 6+, VAL | 11 | too few | too few | too few | too few |

## Median ticket tercile (TRAIN cuts 19.64 / 20.55 SOL)

| subset | launches | SHARED_FUNDER | HIGH_SYNCHRONIZATION | FUNDING_CLUSTER | RECURRING_WALLET_CLUSTER |
|---|---:|---|---|---|---|
| tercile 1, TRAIN | 341 | 209 (61 %), p 0.005 | 278 (82 %), p 0.005 | 239 (70 %), p 0.005 | 200 (59 %), p 0.005 |
| tercile 2, TRAIN | 336 | 275 (82 %), p 0.005 | 311 (93 %), p 0.005 | 282 (84 %), p 0.005 | 136 (40 %), p 0.005 |
| tercile 3, TRAIN | 338 | 306 (91 %), p 0.005 | 334 (99 %), p 0.005 | 307 (91 %), p 0.005 | 136 (40 %), p 0.005 |
| tercile 1, VAL | 154 | 69 (45 %), p 0.005 | 78 (51 %), p 0.005 | 120 (78 %), p 0.005 | 58 (38 %), p 0.005 |
| tercile 2, VAL | 266 | 208 (78 %), p 0.005 | 257 (97 %), p 0.005 | 209 (79 %), p 0.005 | 49 (18 %), p 0.005 |
| tercile 3, VAL | 222 | 177 (80 %), p 0.005 | 220 (99 %), p 0.005 | 178 (80 %), p 0.005 | 125 (56 %), p 0.005 |

## Operators

| subset | launches | SHARED_FUNDER | HIGH_SYNCHRONIZATION | FUNDING_CLUSTER | RECURRING_WALLET_CLUSTER |
|---|---:|---|---|---|---|
| all, TRAIN | 1015 | 790 (78 %), p 0.005 | 923 (91 %), p 0.005 | 828 (82 %), p 0.005 | 472 (47 %), p 0.005 |
| without the dominant operator, TRAIN | 801 | 684 (85 %), p 0.005 | 770 (96 %), p 0.005 | 694 (87 %), p 0.005 | 319 (40 %), p 0.005 |
| operators seen 2 times or more, TRAIN | 925 | 725 (78 %), p 0.005 | 846 (91 %), p 0.005 | 755 (82 %), p 0.005 | 471 (51 %), p 0.005 |
| operators seen 5 times or more, TRAIN | 746 | 570 (76 %), p 0.005 | 670 (90 %), p 0.005 | 602 (81 %), p 0.005 | 410 (55 %), p 0.005 |
| single launches only, TRAIN | 750 | 545 (73 %), p 0.005 | 666 (89 %), p 0.005 | 577 (77 %), p 0.005 | 452 (60 %), p 0.005 |
| all, VAL | 642 | 454 (71 %), p 0.005 | 555 (86 %), p 0.005 | 507 (79 %), p 0.005 | 232 (36 %), p 0.005 |
| without the dominant operator, VAL | 536 | 426 (79 %), p 0.005 | 520 (97 %), p 0.005 | 435 (81 %), p 0.005 | 186 (35 %), p 0.005 |
| operators seen 2 times or more, VAL | 599 | 418 (70 %), p 0.005 | 516 (86 %), p 0.005 | 469 (78 %), p 0.005 | 232 (39 %), p 0.005 |
| operators seen 5 times or more, VAL | 473 | 307 (65 %), p 0.005 | 392 (83 %), p 0.005 | 358 (76 %), p 0.005 | 196 (41 %), p 0.005 |
| single launches only, VAL | 500 | 320 (64 %), p 0.005 | 418 (84 %), p 0.005 | 370 (74 %), p 0.005 | 230 (46 %), p 0.005 |

## Dominant wallets (their records removed; labels as computed on the full launches)

| subset | launches | SHARED_FUNDER | HIGH_SYNCHRONIZATION | FUNDING_CLUSTER | RECURRING_WALLET_CLUSTER |
|---|---:|---|---|---|---|
| without the 10 most frequent sniper wallets, TRAIN | 989 | 764 (77 %), p 0.005 | 897 (91 %), p 0.005 | 802 (81 %), p 0.005 | 448 (45 %), p 0.005 |
| without the 10 most frequent sniper wallets, VAL | 609 | 443 (73 %), p 0.005 | 541 (89 %), p 0.005 | 480 (79 %), p 0.005 | 199 (33 %), p 0.005 |

Dominant operator: TRAIN 214 launches; VAL 106 launches.
The 10 most frequent sniper wallets appear in 118 launches together.
