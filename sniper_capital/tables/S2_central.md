# S2. The central test: does ticket / capital add anything?

`a_med` = the launch median of ticket / capital before the buy. N: TRAIN 896, VALIDATION 606 (every sniper OBSERVED for all of them).

- ROC-AUC, oriented on TRAIN (lower a_med, more 2x): TRAIN 0.622, VALIDATION 0.727.
- VALIDATION ROC-AUC of premium + actor + snipers + a_med minus premium + actor + snipers (TRAIN boosting): +0.013 [-0.029, +0.057].

## Matched comparison: a_med above its TRAIN median (0.836) against below, within week x premium tercile x actor x snipers (4 or 5+)

- all launches, TRAIN (896 launches, 19 strata with both groups): +1.8 pts [-5.8, +9.6].
- all launches, VALIDATION (606 launches, 13 strata with both groups): -22.8 pts [-32.3, -13.2].
- without the dominant operator, TRAIN (697 launches, 17 strata with both groups): +7.3 pts [-1.2, +16.8].
- without the dominant operator, VALIDATION (508 launches, 13 strata with both groups): -20.7 pts [-29.4, -11.2].
- single-operator launches only, TRAIN (661 launches, 15 strata with both groups): +2.5 pts [-4.9, +10.0].
- single-operator launches only, VALIDATION (469 launches, 9 strata with both groups): -23.0 pts [-31.8, -13.6].
