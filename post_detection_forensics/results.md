# Results: does the on-chain structure of a bundle snipe say which ones double?

Primary label: a 2x from the alert price P0, confirmed by two consecutive reads within 15 minutes
(`A_conf_2x_15m`), complete-case. Features at alert - 1 s. Everything below comes from the frozen table
(`derived/TABLE_FREEZE.json`, sha256 `9d2fd31f...`, committed in `88ac240` before any rate was
computed) and from the scripts `ana_10` to `ana_90`; every number is in `tables/D1` to `tables/D9`.

| | TRAIN (2026-08-21 to 09-14) | VALIDATION (09-15 to 09-29) |
|---|---:|---:|
| alerts, on-chain coverage | 1,015, 100 % | 642, 100 % |
| primary label observed | 896 | 606 |
| confirmed 2x within 5 min / 15 min / 1 h | 10.8 % / 22.4 % / 28.7 % | 12.0 % / 26.4 % / 32.4 % |

TRAIN is exploration. VALIDATION re-measures what TRAIN chose, but it also chose among candidates
(model configurations, the kept rule), so its rates are optimistic. VALIDATION was the previous
study's TEST. There is no TEST here: the future TEST (alerts after 2026-09-29 11:23 UTC) is a separate
question.

## A. What the data prove

Only what survives the controls.

1. **The price at entry is the strongest single variable, and it is one variable.** P0, the entry
   premium over the operator, the pool's SOL reserve and the market cap are rank-correlated at 0.91
   to 0.98. Cheaper entries double more often: ROC-AUC 0.67 to 0.69 in TRAIN, 0.64 to 0.66 in
   VALIDATION, same direction in both.
2. **The actor label and the premium carry the same information.** 392 "grouped" launches are almost
   all at x4.5 or more over the operator, 1,233 "single" launches almost all below; the other two
   cells hold 15 and 6 alerts. On VALIDATION, actor alone gives ROC-AUC 0.632, premium alone 0.636,
   both 0.637 (actor + premium minus premium: +0.001 [-0.009, +0.008]).
3. **The early buyers carry no information, because they are all the same kind of wallet.** In
   1,013 of 1,015 TRAIN alerts, the median early buyer already has 1,000 earlier transactions or
   more (the collection's cap), and in no alert are most early buyers fresh wallets. Before the
   alert, the buyers besides the bundle are seasoned bots.
4. **Once actor and premium are known, the on-chain features do not add ROC-AUC at the confidence
   the plan required.** The gate (the TRAIN-screened on-chain features plus actor and premium,
   against actor and premium alone, same model grid) is +0.063 [-0.018, +0.114] on VALIDATION. The
   plan's other two versions agree: every feature, ridge logistic, +0.037 [-0.056, +0.094]; every
   feature, best of the grid, +0.037 [-0.056, +0.094].
5. **Funding topology has no stable effect.** Among launches of the same week, premium tercile,
   number of snipers and bundle SOL, a common funder for two snipers or more changes the rate by
   +6.6 points [-5.2, +17.2] in TRAIN and -21.8 points [-41.7, -3.3] in VALIDATION. The sign flips.

## B. The main on-chain pattern

What the launches that double tend to look like, before the alert, in both splits:

- lower price at entry (the single variable of A.1) and the "single" operator family;
- smaller tickets and a slightly smaller bundle (`b_ticket_mean` ROC-AUC 0.64 and 0.69 read
  downwards, `b_core_sol` 80.1 against 82.4 SOL in TRAIN), bought through more separate
  transactions and with Jito tips (`b_core_tx_n` 0.63 and 0.67, `b_core_tip_sol` 0.64 and 0.65);
- snipers funded by high-volume funders (hubs) with a long record of funding in the corpus (91 to
  93 % of the winners' snipers are hub-funded against 67 to 69 % of the losers'; `g_funder_prior_uses`
  0.62 and 0.64);
- more buying in the seconds before the alert (`m_buys_5s`, `m_rate`, `m_buy_max`, ROC-AUC 0.62 to
  0.67).

Pairs of ROC-AUC are TRAIN then VALIDATION. The number of snipers is not in this list: alone it does
not pass the TRAIN screen (0.53). Round tickets and priority fees pass it but do not hold in
VALIDATION.

This is a bundle of correlated proxies, not one structure. The model that combines them best
(ridge logistic, penalty 1,000, on the 79 features that pass the TRAIN screen) spreads almost equal
weights, about 0.03 each on standardised inputs, over all of them. Its top 20 % reaches 45.5 %
(51/112) on VALIDATION against a 26.4 % base, but that selection never contains a "grouped" launch
nor a premium of x4.5 or more (0 alerts in both cells), is correlated at +0.64 with the number of
snipers and at -0.45 with P0, and takes 71 of its 112 alerts from a single operator cluster.

## C. Variables that bring information of their own

None at the confidence the plan fixed. What points that way, without reaching it:

- the gate itself, +0.063 with a lower bound at -0.018;
- the model's top 20 % keeps a lift beyond what a TRAIN model of P0, premium and actor predicts for
  the same alerts: +10.6 points [+2.2, +30.8]. Without its dominant operator it still reads 43.9 %
  (18/41) against 23.0 %, on 41 alerts;
- the bundle features alone reach ROC-AUC 0.695 on VALIDATION, against 0.637 for actor and premium
  (a point comparison, not tested);
- the actor label adds to every on-chain feature: all + actor minus all without actor, +0.031
  [+0.006, +0.069]. What the detector's operator clustering knows is not fully in the per-launch
  on-chain features.

## D. Variables that cannot be separated with this sample

| variables | why |
|---|---|
| P0, entry premium, pool SOL reserve, market cap | Spearman 0.91 to 0.98 |
| actor label and entry premium | 15 and 6 alerts in the off-diagonal cells; Spearman 0.71 |
| `b_core_tx_n` and `b_core_signers` | Spearman 1.00 |
| `m_buys_5s` and `m_rate` | Spearman 0.86 |
| the model's top 20 % and (single actor, premium below x4.5) | 0 selected alerts outside that cell |
| the kept rule and one operator | 45 of its 48 VALIDATION alerts are one operator cluster |
| any rate and the operator mix of the period | the largest cluster is 22 % of TRAIN and 16 % of VALIDATION; one VALIDATION cluster of 98 doubles 43.9 % of the time, another of 31 never does |

## E. Historical performance

Primary label. Lift = rate minus base, and rate over base.

| signal | status | period | N | base | 2x rate [Wilson 95 %] | lift |
|---|---|---|---:|---:|---|---|
| actor + premium, top 20 % (reference) | VALIDATION | 09-15 to 09-29 | 121 | 26.4 % | 31.4 % (38/121) [23.8-40.1] | +5.0 pts, x1.19 |
| rule `b_ticket_median <= 18.86 AND m_buy_max > 0.98 AND m_buys_5s > 24` | TRAIN, in-sample | 08-23 to 09-14 | 40 | 22.4 % | 65.0 % (26/40) [49.5-77.9] | +42.6 pts, x2.90 |
| same rule | VALIDATION, chose it among 50 | 09-15 to 09-29 | 48 | 26.4 % | 45.8 % (22/48) [32.6-59.7] | +19.4 pts, x1.74 |
| model "screened", top 20 % by the TRAIN threshold | TRAIN, in-sample | 08-23 to 09-14 | 180 | 22.4 % | 39.4 % (71/180) [32.6-46.7] | +17.0 pts, x1.76 |
| same model | VALIDATION, chose its configuration | 09-15 to 09-29 | 112 | 26.4 % | 45.5 % (51/112) [36.6-54.8] | +19.1 pts, x1.72 |
| same model, without its dominant operator | VALIDATION | 09-15 to 09-29 | 41 | 23.0 % | 43.9 % (18/41) [29.9-59.0] | +20.9 pts, x1.91 |
| TEST | none | | | | | |

ROC-AUC on VALIDATION by feature set (`tables/D7_models.md`): actor 0.632, actor + premium 0.637,
funding 0.646, wallets + history 0.655, micro 0.673, all 0.674, price + micro 0.681, bundle 0.695,
screened 0.700.

## F. Robustness

The seven variants were fixed before any rate was computed (window 10 / 20 min, threshold 1.8 /
2.2x, single read, cut-off -2 / -5 s).

- The model's top 20 % holds all seven on VALIDATION (lower bound above the base each time: 44.7 %
  at 10 min, 39.3 % at 2.2x, 51.8 % single read, 44.8 % at -5 s), in both halves of VALIDATION
  (42.0 % and 51.2 %) and in every week of both splits where it selects more than 8 alerts.
- The rule also holds all seven, but on 32 to 50 alerts from one operator; it is explained by P0,
  premium and actor (lift beyond their model +6.1 points [-37.4, +47.8]).
- In the univariate screen, 68 of the 79 features that pass BH in TRAIN keep their direction in
  VALIDATION with p < 0.05. Those p-values ignore the operator clusters and most of the features are
  proxies of A.1 and A.2, so this counts one factor many times, not 68 findings.
- August against September is only visible on TRAIN rows; nothing measured on TRAIN is called robust.

## G. What does not work

- **Rules at 70 or 80 %.** 1,582,590 rules of one to three conditions were evaluated; none reaches
  70 % in TRAIN with 40 alerts or more. The 431 between 60 and 70 % pool to 39.7 % on VALIDATION.
- **The pair screen.** 5,843 of 9,870 feature pairs pass BH in TRAIN and 3,644 hold in VALIDATION:
  nearly every pair contains a proxy of price or actor, and a Fisher test that ignores the clusters
  cannot sort them. The screen separates nothing.
- **Funding topology.** "One funder for the whole core" doubles less than the base (20.2 % and
  15.5 % against 22.4 % and 26.4 %); "some snipers share a funder" and "distributed funding" sit at
  the base; the matched comparison flips sign (A.5). The funding amount does not replicate either:
  the winners' snipers received a median 1.24 SOL against 10.2 for the losers' in TRAIN, and 1.02
  against 1.04 in VALIDATION.
- **Deployer links.** A funding link between the deployer and a sniper is associated with a lower
  rate in both splits (19.5 % and 20.2 %), in line with the "grouped" family of A.2, not beyond it.
- **Profiles 5 and 6** (experienced or fresh early buyers): not measurable, see A.3.
- **The concentrated-bundle profile** doubles less than the base in both splits (17.0 % and 23.1 %).
- **One ridge logistic on every feature** does no better than actor and premium (F minus C, +0.037
  [-0.056, +0.094]).

## H. Verdict

**NO ROBUST ON-CHAIN SEPARATION FOUND**

Computed by `code/ana_90_verdict.py` from the rules of `analysis_plan.md`: coverage 100 % and 606
VALIDATION alerts (not inconclusive); the gate's lower bound is below 0, so no independent on-chain
information is established, and the subgroup checks do not change that.

What the verdict covers, and what it does not:

- It is historical. The future TEST can still ask whether the screened model's top 20 % keeps its
  45 % on launches nobody has looked at; the model is frozen in `derived/D7_gate_model.json` with its
  TRAIN threshold, for that purpose only.
- It excludes large on-chain effects, not moderate ones. On synthetic tables of this size
  (`tables/D0_power_dry_run.md`), an on-chain effect with an odds ratio of about 4.5 passes the gate
  4 times in 4, one of about 2.7 only half the time. The gate estimate here (+0.063) sits in the
  range where this sample cannot decide.
- It is about separation, not money. Nothing here accounts for fees, slippage, latency or the price
  actually paid, and the previous study found no tradable edge after costs for a signal of the same
  size (45.7 % against 31.0 %).
- Nothing here is exploitable: the pattern of B is mostly price and operator, the kept rule is one
  operator, and the one selection that survives every check lives entirely inside the cheap,
  "single" corner that the premium alone already points to.

## Deviations and data notes

- The plan was amended on 2026-09-29, before the freeze, after a dry run on synthetic tables; each
  amendment and its reason is at the end of `analysis_plan.md`.
- Profiles 5 and 6 were defined as "above the TRAIN median" of features that sit at their cap (or at
  0) for almost every alert; they select no one. Reported, not redefined.
- The kept rule was chosen on VALIDATION among the 50 best TRAIN rules; its VALIDATION rate is
  optimistic, and its TRAIN rate is in-sample.
- The detector reads the creation slot with transactions capped at version 0 and misses the snipers
  who bought through a version-1 transaction (20 alerts, 2026-09-17 to 09-27). The bundle features
  here count them; the alert population is what the detector raised.
