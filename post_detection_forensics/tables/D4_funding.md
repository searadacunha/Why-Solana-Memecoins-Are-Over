# D4. Funding flows (primary label)

## Per sniper (core wallet), winners vs losers

| split | measure | winners: median (q25-q75) or share | losers | N win / lose |
|---|---|---|---|---|
| TRAIN | known | 85.4 % | 88.4 % | 830 / 2824 |
| TRAIN | hub | 91.3 % | 67.1 % | 709 / 2496 |
| TRAIN | received | 1.24 (0.995-21) | 10.2 (0.996-25.2) | 709 / 2496 |
| TRAIN | to_buy_h | 0.742 (0.173-2.12) | 0.535 (0.000556-2.25) | 709 / 2496 |
| TRAIN | to_alert_h | 0.745 (0.176-2.12) | 0.539 (0.0048-2.25) | 709 / 2496 |
| TRAIN | same_funder | 4 (2-4) | 4 (2-4) | 709 / 2496 |
| TRAIN | deployer_link | 34.9 % | 46.8 % | 830 / 2824 |
| TRAIN | prior_uses | 437 (112-1.11e+03) | 162 (0-647) | 709 / 2496 |
| VAL | known | 86.7 % | 94.8 % | 684 / 1831 |
| VAL | hub | 93.3 % | 68.7 % | 593 / 1736 |
| VAL | received | 1.02 (0.83-1.23) | 1.04 (0.771-13.2) | 593 / 1736 |
| VAL | to_buy_h | 1.25 (0.516-2.38) | 0.648 (0.000833-2.08) | 593 / 1736 |
| VAL | to_alert_h | 1.25 (0.519-2.38) | 0.652 (0.00481-2.09) | 593 / 1736 |
| VAL | same_funder | 2 (1-4) | 4 (2-4) | 593 / 1736 |
| VAL | deployer_link | 25.7 % | 52.8 % | 684 / 1831 |
| VAL | prior_uses | 1.19e+03 (552-2.37e+03) | 674 (0-2.02e+03) | 593 / 1736 |

## Per launch: funding topology

| split | topology | P(2x confirmed, 15 min) |
|---|---|---|
| TRAIN | a core wallet funded by a hub | 27.5 % (162/589) [24.1-31.2] |
| TRAIN | deployer linked to a core wallet | 19.5 % (110/563) [16.5-23.0] |
| TRAIN | every known funder distinct | 21.5 % (17/79) [13.9-31.8] |
| TRAIN | no funder known | 27.6 % (24/87) [19.3-37.8] |
| TRAIN | one funder for the whole core | 20.2 % (87/430) [16.7-24.3] |
| TRAIN | some core wallets share a funder | 24.3 % (73/300) [19.8-29.5] |
| VAL | a core wallet funded by a hub | 31.4 % (138/439) [27.3-35.9] |
| VAL | deployer linked to a core wallet | 20.2 % (90/446) [16.7-24.2] |
| VAL | every known funder distinct | 54.1 % (20/37) [38.4-69.0] |
| VAL | no funder known | 50.0 % (10/20) [29.9-70.1] |
| VAL | one funder for the whole core | 15.5 % (36/232) [11.4-20.7] |
| VAL | some core wallets share a funder | 29.7 % (94/317) [24.9-34.9] |
