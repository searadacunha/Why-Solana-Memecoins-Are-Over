# K. Post-hoc checks (descriptive, added after reading tables B to J)

## 1. Every outgoing SOL transfer of 0.1 SOL or more (1280)

- signers: exit wallet signs True, recipient pays the fee True, 4 signers: 1280
- route: through an address with 1 transaction(s) in its history: 1280
- exit wallet's SOL after the transfer: 0.0000 / 0.0000 / 0.0000 / 0.0500 / 0.0000 / 5.9927 (N 1280); below 0.001 SOL in 1093
- delay from the receipt of the tokens (s): 152 / 105 / 318 / 370 / 26 / 674 (N 1280)
- delay after the last sale before it (s): 28 / 11 / 61 / 161 / 0 / 519 (N 1236)

## 2. Sales by the exit wallets

- venue: PumpSwap 6049
- fee paid by: exit wallet 6049

- reading complete: 1096 events, tokens not yet sold when it stopped 0 %, sales read per event (median) 2
- reading cap: 361 events, tokens not yet sold when it stopped 65 %, sales read per event (median) 10

## 3. SOL sent straight to the launch's own funder, whatever its hub status

| | branches | SOL | events |
|---|---:|---:|---:|
| to the launch's funder | 788 (62 %) | 9168 (67 %) | 728 of 1161 (63 %) |
| of which to a funder the plan classifies as a hub (H5) | 157 | 1470 | |
| elsewhere | 492 | 4478 | |

- TRAIN: 70 % of branches to the launch's funder
- VALIDATION: 53 % of branches to the launch's funder

## 4. By operator (the unit the event-level nulls ignore)

| operator | launches TRAIN / VAL | read events | transfers | to the launch's funder | recipients | events funding a later launch |
|---|---|---:|---:|---:|---|---:|
| k:21.13+21.08+19 | 45 / 5 | 301 | 219 | 89 % | 23 (D6HE3k 93, 67qjEd 26) | 155 of 185 |
| c:5MSpdabaEo18hZ | 0 / 5 | 150 | 151 | 0 % | 1 (3fzT6g 151) | 0 of 150 |
| k:20.80+20.21+19 | 0 / 7 | 150 | 154 | 100 % | 1 (Cb2Nvw 154) | 150 of 150 |
| c:Fb2TAFf2zdgkf7 | 0 / 3 | 120 | 122 | 0 % | 1 (35Lopf 122) | 0 of 120 |
| c:HxYyavxib9P1oS | 6 / 0 | 120 | 123 | 100 % | 4 (EoBeA3 40, HkBMLh 32) | 82 of 110 |
| k:22.04+21.96+19 | 6 / 0 | 120 | 135 | 0 % | 2 (7934tg 72, EaPUR4 63) | 0 of 102 |
| c:8uM3AeYfpA88Z7 | 0 / 1 | 60 | 61 | 100 % | 1 (DjJMVM 61) | 60 of 60 |
| c:9TN2NEfg6vfijy | 2 / 0 | 60 | 56 | 100 % | 1 (D6HE3k 56) | 50 of 50 |
| c:Gug21eQUwmZio4 | 0 / 1 | 60 | 61 | 100 % | 1 (8E2rmK 61) | 60 of 60 |
| k:21.59+21.27+20 | 0 / 2 | 56 | 56 | 95 % | 1 (4aEJJD 56) | 0 of 55 |
| c:2YKa6U61fozw1a | 0 / 1 | 30 | 25 | 0 % | 1 (Axiwxa 25) | 0 of 24 |
| c:BdE3C2tCtCwDi6 | 10 / 0 | 30 | 12 | 100 % | 1 (8w91Sb 12) | 12 of 12 |
| c:8peR5ucxZnSFWY | 0 / 5 | 20 | 4 | 100 % | 1 (CRXwGG 4) | 4 of 4 |
| c:9FJvWMsUwgr7wd | 5 / 0 | 20 | 26 | 0 % | 6 (AAGmdF 8, 4B4ajw 6) | 0 of 13 |
| c:EwFgFSw9KHqVw3 | 5 / 0 | 20 | 6 | 100 % | 1 (7xXmSD 6) | 6 of 6 |
| k:20.20+19.92+19 | 5 / 0 | 20 | 6 | 17 % | 1 (8bE9Uz 6) | 6 of 6 |
| k:20.20+20.18+19 | 5 / 0 | 20 | 9 | 100 % | 1 (5pQ9ZV 9) | 8 of 8 |
| k:20.24+20.07+19 | 5 / 0 | 20 | 7 | 100 % | 1 (7jbDou 7) | 7 of 7 |
| k:20.32+19.97+19 | 5 / 0 | 20 | 9 | 100 % | 2 (92hhkb 7, Dkcuf3 2) | 7 of 9 |
| k:20.68+20.51+20 | 8 / 0 | 20 | 11 | 100 % | 6 (HBLBFe 3, BYZX1U 2) | 0 of 11 |
| c:YSUcHvAijrKRgS | 7 / 0 | 15 | 4 | 100 % | 3 (5odxJv 2, 8BxVjG 1) | 0 of 4 |
| k:21.39+21.26+21 | 1 / 0 | 13 | 19 | 100 % | 1 (8kEiAZ 19) | 0 of 11 |
| k:21.40+21.14+21 | 0 / 1 | 4 | 1 | 0 % | 1 (2AFX2b 1) | 0 of 1 |
| k:22.02+21.86+21 | 1 / 0 | 4 | 3 | 100 % | 1 (BpWiEe 3) | 0 of 3 |

Operators with transfers: 24; sending 80 % or more to the launch's funder: 17 (TRAIN-only 11, VALIDATION-only 5, both 1); 20 % or less: 7 (TRAIN-only 3, VALIDATION-only 4, both 0); in between: 0.
Operators funding a later launch from the swept capital: 12 of the 17 returning to the funder, 1 of the 7 sending elsewhere.
Read events per launch, median: TRAIN 4, VALIDATION 18; launches: TRAIN 117, VALIDATION 31.

## 5. Recipients other than the launch's funder

20 distinct wallets for 492 transfers; known anywhere in the frozen tables (any role, any time): 4; measured or recorded hubs: 4; too active to reach the inflow in 3 pages: 7.
Recipient wallets used by two operators or more: D6HE3knc (2 operators).
Distinct recipients over all 1280 transfers: 62; events whose transfers go to two recipients or more: 1.

## 6. Exit wallets fed by one sniper in one launch (whole frozen corpus)

0: 2500, 1: 3603, 2: 6, 3: 5, 4: 7, 5: 10, 6: 5, 7: 174, 8: 178, 9: 3, 10: 14, 11: 2, 12: 16, 13: 16, 15: 262, 18: 2, 24: 4, 25: 1, 30: 1, 35: 1, 36: 1, 39: 1, 45: 1, 48: 1, 54: 4, 64: 1, 176: 1, 184: 1, 231: 1

## 7. Recycling links (section F) by the wallet that funds the later launch

the launch's own funder 600, another wallet 7
