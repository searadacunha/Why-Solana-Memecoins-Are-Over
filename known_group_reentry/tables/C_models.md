# C. Known group against the baseline (primary target: +50 % within 15 min, entry +5 s)

| split | KNOWN vs UNKNOWN (G1) | PARTIAL vs UNKNOWN | G2 | G3 | G4 |
|---|---|---|---|---|---|
| TRAIN | 60.3 % (N 380) vs 41.9 % (N 310): +18.3 pts [+8.5, +26.3], p 2.27e-06 | 51.5 % (N 99) vs 41.9 % (N 310): +9.6 pts [-6.9, +21.1], p 0.121 | 57.4 % (N 242) vs 49.5 % (N 547): +7.9 pts [-0.2, +17.3], p 0.0486 | 60.9 % (N 169) vs 49.5 % (N 620): +11.4 pts [+2.4, +21.0], p 0.0105 | 62.2 % (N 352) vs 43.7 % (N 437): +18.5 pts [+11.1, +24.8], p 3.09e-07 |
| VAL | 61.2 % (N 227) vs 33.6 % (N 253): +27.6 pts [+16.4, +38.4], p 1.95e-09 | 57.0 % (N 142) vs 33.6 % (N 253): +23.4 pts [+10.4, +36.8], p 9.93e-06 | 60.1 % (N 208) vs 43.5 % (N 414): +16.6 pts [+7.4, +28.1], p 0.000126 | 61.8 % (N 144) vs 45.2 % (N 478): +16.6 pts [+7.8, +28.0], p 0.000647 | 61.9 % (N 215) vs 42.3 % (N 407): +19.6 pts [+9.6, +31.0], p 4.64e-06 |

Holm across G1-G4 on VALIDATION (two-sided Fisher, alert level): G1 7.81e-09, G2 0.000252, G3 0.000647, G4 1.39e-05

## Models fitted on TRAIN, scored on VALIDATION (L2 = 1, no tuning)

| model | AUC | PR-AUC | Brier | log loss | calibration (mean predicted / observed, 5 bins) |
|---|---:|---:|---:|---:|---|
| Model 1 baseline | 0.634 | 0.566 | 0.2305 | 0.6516 | 0.27/0.19, 0.52/0.52, 0.56/0.61, 0.59/0.56, 0.67/0.58 |
| Model 2 group only | 0.631 | 0.591 | 0.2369 | 0.6668 | 0.41/0.35, 0.42/0.34, 0.50/0.56, 0.58/0.56, 0.63/0.64 |
| Model 3 baseline + group | 0.651 | 0.585 | 0.2295 | 0.6493 | 0.27/0.19, 0.47/0.52, 0.55/0.54, 0.59/0.64, 0.67/0.58 |

Log loss, Model 3 minus Model 1, per VALIDATION alert: -0.0023 [-0.0121, +0.0084] (cluster bootstrap; negative = the group adds information).
Base rate of the primary target: TRAIN 52.0 % (N 789), VALIDATION 49.0 % (N 622).
