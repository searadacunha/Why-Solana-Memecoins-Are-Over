# D0. What the pipeline can see: a dry run on synthetic tables

Written before the real analytic table was frozen. No real alert, feature or label is used here.

Each synthetic table has 1 650 alerts on the real calendar (TRAIN before 2026-09-15, about 550
VALIDATION alerts with an observed primary label), the 144 SAFE features filled with noise, and
operator clusters drawn at random. The label is drawn from a logistic model with a planted premium
effect (-0.6 per standard deviation) and actor effect (+0.5), which every run shares, plus a planted
on-chain effect of size b on two features: `f_same_funder_multi` (binary, about 40 % of alerts) and
`g_early_linked` above 1 (about 16 %). b = 0 is the null control. Every step from 1 to 9 then ran
exactly as it will on the real table (`ana_10`, `ana_30`, `ana_60`, `ana_70`, `ana_80`, `ana_90`),
four seeds per size.

| planted on-chain effect b (log-odds, odds ratio) | gate "screened" minus "actor + premium", CI above 0 | verdict PROMISING | verdict WEAK | verdict NO ROBUST |
|---|---:|---:|---:|---:|
| 0 (null control) | 0 / 4 | 0 / 4 | 0 / 4 | 4 / 4 |
| 1.0 (about 2.7) | 2 / 4 | 0 / 4 | 2 / 4 | 2 / 4 |
| 1.5 (about 4.5) | 4 / 4 | 3 / 4 | 1 / 4 | 0 / 4 |
| 2.0 (about 7.4) | 4 / 4 | 4 / 4 | 0 / 4 | 0 / 4 |

Gate estimates (VALIDATION ROC-AUC difference): b = 0: +0.000 in all four runs (the screen keeps no
on-chain feature, so both models are the same); b = 1.0: +0.026 to +0.056; b = 1.5: +0.058 to
+0.106; b = 2.0: +0.060 to +0.134.

Reading:

- No false positive in four null runs. Four runs do not measure a false-positive rate; they show
  that a premium-and-actor signal alone does not pass the gate or the residual-lift check.
- With about 550 VALIDATION alerts the pipeline finds on-chain effects from an odds ratio of about
  4.5, sees an odds ratio of about 2.7 half the time, and never promotes it to PROMISING.
- A NO ROBUST ON-CHAIN SEPARATION verdict on the real table therefore excludes on-chain effects of
  the size of b = 1.5 and above on a feature carried by a large share of alerts. It does not
  exclude moderate effects, nor effects confined to a small share of alerts.
- The synthetic features are independent noise. Real features are correlated with each other and
  with the premium, which can lower the power further.
