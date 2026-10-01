# B. Token exit paths: sniper -> exit wallet -> token

Sampled events 1457; read 1457 (complete 1096, window end 0, cap 361); not read 0.

| disposal of the token by the exit wallet | TRAIN | VALIDATION | all | launches | exit wallets |
|---|---:|---:|---:|---:|---:|
| sold | 499 | 632 | 1131 (78 %) | 113 | 274 |
| mixed | 288 | 38 | 326 (22 %) | 116 | 107 |

Token amounts over the read events: sold 56 %, transferred 0 %, other contracts 0 %, left at the end of the reading 44 %.

Delay from the sniper's transfer to the exit wallet's first move of the token (s), median / p25 / p75 / p90 / min / max: 81 / 35 / 143 / 330 / 3 / 641 (N 1457)

Delay to the first sale (s): 81 / 35 / 143 / 330 / 3 / 641 (N 1457)

Events where two snipers or more sent the same token to the same exit wallet: 0 of 1457 (0 %).

Recipients of tokens transferred onward by the exit wallet (transfers): none

Outgoing SOL transfers of 0.1 SOL or more signed (fee paid) by the exit wallet itself: 0 of 1280.
Distinct fee payers of the others: 62; the largest pays for 154 transfers.
