# Known group re-entry as a live trading signal: results

Protocol: [analysis_plan.md](analysis_plan.md), committed with the chronological group features (8bae78e)
before any outcome was computed. Features: `derived/kg_features.jsonl.gz` (sha256 `b264efcc...`); outcomes and
trades: `derived/kg_outcomes.jsonl.gz` (sha256 `cd666bf5...`). Tables B to J in `tables/`. No new Helius call.
Prices, coverage rules, simulator and costs are those of the post-detection-edge snapshot, used unchanged. TEST
(alerts after 2026-09-29 11:23 UTC) is not in the data and was not read.

## A. Executive summary

- **The group carries information on its own.** Alerts whose snipers were already seen together reach +50 %
  within 15 minutes (entry +5 s) more often than alerts with no known group:
  - TRAIN: 60 % against 42 % (+18 pts [+9, +26]);
  - VALIDATION: 61 % against 34 % (+28 pts [+16, +38]);
  - all four pre-registered definitions are positive in VALIDATION after Holm.
- **It adds nothing beyond the baseline features.** Matched on number of snipers, SOL, supply, premium and
  market cap, the difference is +5 pts [-9, +15] in TRAIN and +16 pts [-4, +33] in VALIDATION. Adding the group
  to the baseline model does not lower the VALIDATION log loss: -0.0023 [-0.012, +0.008], AUC 0.651 against
  0.634.
- **Depth.** A group's first appearance reaches the target 42-44 % of the time, against 59-64 % once it has
  been seen at least once, in both periods. More repetitions add nothing.
- **Recency.** No stable pattern: the 1-6 h and over-6 h bins swap places between periods.
- **Operator controls.** The raw difference survives without the dominant operator and when any one of the 10
  largest operators is left out (+24 to +29 pts in VALIDATION). Within operators it holds in VALIDATION
  (+20 pts [+6, +39]) but not in TRAIN (+8 pts [-9, +18]).
- **Costs.** The primary strategy (entry +5 s, target +50 %, stop -15 %, 15 min, $500) on known groups loses
  17.3 % per trade in VALIDATION [-21.3, -13.0] and 15.0 % in TRAIN. It already loses 4.8 % before costs, and
  break-even needs a 57 % win rate against 31 % observed.
- **No strategy works.** All 96 VALIDATION combinations (4 entries x 8 exits x 3 populations) lose after
  costs. The best gross case for known groups, chosen after the fact, makes +4.1 % before costs and -1.6 %
  [-4.0, +1.6] at $100.
- **Decision: NO INCREMENTAL SIGNAL** (the rule of the protocol, as written). Read more generously as a
  statistical signal, it is still not tradable.

## B. Historical group recognition

At each alert, the group is recognised only from earlier alerts whose 30 s window had closed at least 60 s
before (`code/kg_10_features.py`). The integrity check confirms it for all 1,657 alerts.

Relations come from the frozen economic-mechanics table:
- **G1 KNOWN** (primary): two current snipers were snipers together in one earlier alert.
- **G1 PARTIAL**: one current sniper was seen before, or a current sniper's non-hub funder funded an earlier
  sniper.
- **G2**: a recurring funder of two current snipers.
- **G3**: G1 KNOWN and G2.
- **G4**: a current sniper already sent tokens to an exit wallet.

The current alert's exits and everything after its alert are never read, and the builder cannot open a price
file.

| split | alerts | G1 KNOWN | G1 PARTIAL | G1 UNKNOWN | G2 | G3 | G4 |
|---|---:|---:|---:|---:|---:|---:|---:|
| TRAIN | 1,015 | 472 | 122 | 421 | 297 | 204 | 436 |
| VALIDATION | 642 | 232 | 147 | 263 | 213 | 146 | 220 |

## C. Baseline against known group

Primary target: +50 % within 15 min, entry +5 s. Base rate: 52.0 % in TRAIN (N 789), 49.0 % in VALIDATION
(N 622).

| split | G1 KNOWN vs UNKNOWN | G1 PARTIAL vs UNKNOWN | G2 | G3 | G4 |
|---|---|---|---|---|---|
| TRAIN | +18.3 pts [+8.5, +26.3] | +9.6 pts [-6.9, +21.1] | +7.9 pts [-0.2, +17.3] | +11.4 pts [+2.4, +21.0] | +18.5 pts [+11.1, +24.8] |
| VALIDATION | +27.6 pts [+16.4, +38.4] | +23.4 pts [+10.4, +36.8] | +16.6 pts [+7.4, +28.1] | +16.6 pts [+7.8, +28.0] | +19.6 pts [+9.6, +31.0] |

Holm on VALIDATION, G1-G4: 7.8e-9, 2.5e-4, 6.5e-4, 1.4e-5. Intervals are cluster bootstraps over operators.

Models fitted on TRAIN and scored on VALIDATION (L2 = 1, no tuning):

| model | AUC | PR-AUC | Brier | log loss |
|---|---:|---:|---:|---:|
| 1 baseline | 0.634 | 0.566 | 0.2305 | 0.6516 |
| 2 group only | 0.631 | 0.591 | 0.2369 | 0.6668 |
| 3 baseline + group | 0.651 | 0.585 | 0.2295 | 0.6493 |

The log-loss gain of Model 3 over Model 1 is -0.0023 [-0.0121, +0.0084], so not distinguishable from zero.
The group alone predicts about as well as the baseline (AUC 0.631 against 0.634). Together they barely improve:
the two carry mostly the same information.

## D. Matched analysis

Known against unknown, inside strata of TRAIN tertiles of n_snipers, SOL, supply, premium and market cap:

| split | strata | KNOWN | UNKNOWN | weighted difference [cluster CI] |
|---|---:|---:|---:|---|
| TRAIN | 28 | 354 | 300 | +5.1 pts [-8.8, +14.5] |
| VALIDATION | 23 | 198 | 159 | +15.9 pts [-4.2, +32.9] |

At comparable current conditions, recurrence itself is not shown to carry information. Most of the raw
difference is explained by the size and price of the current launch.

## E. Recurrence depth, recency, stability

Primary target and primary strategy, $500 (`tables/E_recurrence.md`):

| depth (prior group launches) | TRAIN rate | VALIDATION rate | VALIDATION net per trade |
|---|---:|---:|---:|
| 0 | 44.3 % | 42.0 % | -21.3 % |
| 1 | 58.8 % | 58.9 % | -21.7 % |
| 2-5 | 61.1 % | 63.9 % | -13.6 % |
| more than 5 | 60.0 % | 60.2 % | -17.9 % |

- **Recency.** Under 5 min never occurs (a group cannot return before its previous window closes plus 60 s).
  15-30 min is the largest bin (65 % and 69 %). The 1-6 h bin reads 70 % then 24 %, and the over-6 h bin 27 %
  then 71 %, on fewer than 35 alerts each. No pattern carries across periods.
- **Stability.** Weak / medium / strong: 50-56 %, 60 %, 61-62 %. Every bin loses 13 to 28 % per trade.

## F. Operator robustness

G1 KNOWN against UNKNOWN on the primary target:

| | TRAIN | VALIDATION |
|---|---|---|
| full | +18.3 pts [+8.5, +26.3] | +27.6 pts [+16.4, +38.4] |
| without the dominant operator (k:21.13) | +16.8 pts [+5.7, +26.6] | +29.0 pts [+17.4, +39.9] |
| within operators (Mantel-Haenszel) | +8.1 pts [-9.2, +18.4], 47 operators | +20.0 pts [+6.3, +38.5], 36 operators |
| operator-level means (operators with both) | 61.3 % vs 58.5 % | 65.3 % vs 39.0 % |
| leave one of the 10 largest out | not computed | +24.3 to +29.0 pts, all above zero |
| funder definition restricted to measured non-hub funders | +15.5 pts [+4.5, +38.9], N 39 | -1.5 pts [-48.2, +11.8], N 21 |

The raw difference does not depend on one operator. Within operators it is only clear in VALIDATION.

## G. Forward return distributions

Median from entry +5 s, VALIDATION (`tables/G_returns.md`):
- **Point return**, known group / unknown:
  - 10 s: +1.0 % / +1.6 %;
  - 60 s: +3.5 % / -2.7 %;
  - 5 min: -27.8 % / -29.3 %;
  - 15 min: -99.2 % / -98.5 %;
  - 1 h: -99.3 % / -99.3 %.
- **Highest point reached**: 1.20 / 1.11 at 60 s, and 1.49 / 1.15 at 5 min.
- **Lowest point reached**: 0.87 / 0.88 at 60 s.
- **The pattern.** Known-group tokens go higher in the first minutes, then both fall to almost nothing within
  15 minutes.

Binary targets, known against unknown, entry +5 s, VALIDATION:

| target | 60 s | 5 min | 15 min | 1 h |
|---|---|---|---|---|
| +10 % | 70 % vs 55 % | 88 % vs 65 % | 91 % vs 77 % | 93 % vs 87 % |
| +25 % | 42 % vs 25 % | 75 % vs 41 % | 80 % vs 56 % | 82 % vs 72 % |
| +50 % | 15 % vs 9 % | 50 % vs 23 % | 61 % vs 34 % | 64 % vs 57 % |
| +100 % | 2 % vs 4 % | 18 % vs 11 % | 38 % vs 18 % | 41 % vs 38 % |

These are touches of a spot read, not fills.

## H. Trading simulation

Primary strategy (entry +5 s, target +50 %, stop -15 %, 15 min, $500), costs included:

| split | population | trades | win | mean net [cluster CI] | gross | fees | slippage | break-even win, gross / net |
|---|---|---:|---:|---|---:|---:|---:|---|
| TRAIN | all alerts | 753 | 36 % | -16.1 % [-19.3, -13.1] | -3.8 % | -2.1 % | -10.2 % | 43 % / 60 % |
| TRAIN | G1 KNOWN | 362 | 39 % | -15.0 % [-19.1, -12.1] | -1.7 % | -2.2 % | -11.2 % | 44 % / 60 % |
| TRAIN | G1 UNKNOWN | 295 | 33 % | -15.2 % [-19.7, -9.8] | -4.3 % | -2.1 % | -8.8 % | 40 % / 57 % |
| VALIDATION | all alerts | 604 | 28 % | -19.8 % [-22.3, -16.9] | -8.6 % | -2.0 % | -9.1 % | 39 % / 57 % |
| VALIDATION | G1 KNOWN | 220 | 31 % | -17.3 % [-21.3, -13.0] | -4.8 % | -2.1 % | -10.4 % | 38 % / 57 % |
| VALIDATION | G1 UNKNOWN | 250 | 18 % | -21.8 % [-25.7, -18.0] | -12.3 % | -2.0 % | -7.5 % | 35 % / 54 % |
| VALIDATION | Model 1, top 20 % | 118 | 42 % | -17.8 % [-22.6, -5.3] | -4.1 % | -2.1 % | -11.5 % | 46 % / 64 % |
| VALIDATION | Model 3, top 20 % | 107 | 36 % | -17.7 % [-26.0, -14.2] | -4.0 % | -2.1 % | -11.6 % | 40 % / 61 % |

Other metrics for known groups in VALIDATION:
- median trade -27.4 %, worst -99 %;
- profit factor 0.34;
- holding time 78 s, 1.5 % of the period in a position;
- maximum drawdown of 38 stakes (the running sum of per-trade returns).

Every entry and exit, VALIDATION, mean net return, known / unknown / all (`tables/H_trading.md`):
- **Time exits:** -9 % to -48 %; the 15-minute exit is the worst, at -31 % to -48 % depending on the population.
- **Target and stop:** -13 % to -28 %.
- **Before any cost**, the known-group cells range from -37 % to +4 %. The best is entry +15 s with a 30 s
  exit, at +4.1 %.

Sensitivities on the primary strategy, known groups:

| variant | mean net |
|---|---:|
| $100 | -10.1 % |
| $1,000 | -25.4 % |
| depth x0.5 / x2 | -20.9 % / -14.5 % |
| take-profit at the next read | -16.8 % |

**Upper bound.** The best gross cell (chosen on VALIDATION, so optimistic) at $100 gives -1.6 %
[-4.0, +1.6]. At $500 it gives -9.6 %, at $1,000 -18.6 %. Fees and slippage on these pools exceed the
largest gross gain available.

## I. Out-of-sample results

| | TRAIN | VALIDATION |
|---|---|---|
| G1 KNOWN vs UNKNOWN, primary target | +18.3 pts [+8.5, +26.3] | +27.6 pts [+16.4, +38.4] |
| within operators | +8.1 pts [-9.2, +18.4] | +20.0 pts [+6.3, +38.5] |
| matched | +5.1 pts [-8.8, +14.5] | +15.9 pts [-4.2, +32.9] |
| primary strategy on KNOWN, net | -15.0 % [-19.1, -12.1] | -17.3 % [-21.3, -13.0] |
| Model 3 - Model 1, log loss | (fitted here) | -0.0023 [-0.0121, +0.0084] |

TEST is untouched.

## J. Final decision

**NO INCREMENTAL SIGNAL.**

This applies section 7 of the protocol as written: on VALIDATION the matched difference contains zero, and the
group does not lower the baseline model's log loss. A first version of the decision code left the matched
comparison out of that test and printed STATISTICAL SIGNAL, NOT TRADABLE; it was brought back to the text.

Under either reading the signal is not tradable. The primary strategy loses 15 to 17 % per trade in both
periods, and no combination of entry, exit and size is positive after costs.

## WHAT WE KNOW

- At the alert, it is possible to tell without any look-ahead that a group has already launched: 46 % of TRAIN
  alerts and 36 % of VALIDATION alerts.
- Those alerts reach +50 % within 15 minutes more often, and the difference is stable across periods (+18 and
  +28 pts) and without the dominant operator.
- Matched on the size and price of the launch, the difference is no longer distinguishable from zero. The group
  does not improve the baseline model.
- Every simulated trade loses after costs, known group or not:
  - the primary strategy at -15 % to -17 %;
  - the best gross case at -1.6 % at $100 and worse above;
  - 15 minutes after the alert, the median token is down about 99 %.

## WHAT THE DATA SUGGESTS

- Recognising a known group mostly re-measures what the launch's size and price already say. The operators
  who come back are those whose launches are larger and run higher in the first minutes.
- The extra early rise of known-group tokens is real (highest point at 5 min 1.49 against 1.15) but short.
  It is smaller than the round-trip cost of entering after the bundle, and the dump follows within minutes.

## WHAT FAILED

- **Group definitions.** G1, G2, G3, G4 as trading filters: all negative net.
- **Depth.** Depth bins 0 / 1 / 2-5 / more than 5: all negative net.
- **Recency and stability.** Recency bins are unstable across periods; weak / medium / strong stability
  is all negative.
- **Models.** Model 2 (group only) and Model 3 (baseline + group) against Model 1: no log-loss gain. Model 3's
  top 20 % loses 17.7 % per trade.
- **Entries, exits and sizes.**
  - Entries +0, +5, +15 and +30 s; time exits 10 s to 15 min; target and stop +25/-10, +50/-15, +100/-20;
  - sizes $100, $500 and $1,000; depth x0.5 and x2; take-profit at the next read;
  - all negative net on known groups in VALIDATION.
- **The upper bound** (best gross cell, smallest size): -1.6 % [-4.0, +1.6].

## WHAT TO DO NEXT

**Stop pursuing known-group re-entry as a buy signal.** The information it carries is real, but it is
already in the launch's size and price. The trade it suggests loses after realistic costs, and it was
already losing before costs on the primary strategy.

The one thing that could still change the trading side is cost: slippage here is derived from price, not
measured, and it is the largest cost (about 10 % at $500). If we want to check this before closing the buy
side for good, there are two steps, both your decision:
1. **Measure real fills on tiny sizes.** This would replace the derived depth with measured slippage on
   PumpSwap for these launches.
2. **Only then, a pre-registered run on the future TEST**, with the entry +15 s / 30 s exit fixed in
   advance. That cell was picked on VALIDATION, so only TEST could confirm it.

Without materially lower costs than modelled, buying after a detected bundle snipe has no edge, with or
without group recognition. This is the same conclusion as the post-detection-edge study, now with the group
structure included.
