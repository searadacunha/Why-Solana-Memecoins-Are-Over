# Known group re-entry as a live trading signal: protocol, frozen before any outcome is computed

Question: at the moment of an alert, does recognising that the launch's snipers (or their funder) belong to a group
already seen in earlier alerts improve a real trading decision, beyond the live features already tested?

No new Helius call. Everything comes from frozen files: the economic-mechanics table (`economic_mechanics/derived/
em_table.jsonl.gz`, sha256 `e6b4fdd8...`) for wallets, funders and exits; the post-detection-edge snapshot
(`post_detection_edge/data/`, cut at 2026-09-29 11:23 UTC) for live features, spot price series and the cost
model. The future TEST (alerts after 2026-09-29 11:23 UTC) is not in these files and is not read. No price,
multiple, migration or profit enters any group definition: the group builder (`code/kg_10_features.py`) never
opens a price file, and an audit hook makes it fail if it does.

## 1. Population, splits, decision time

- 1,657 alerts. TRAIN: alerts before 2026-09-15 00:00 UTC (1,015). VALIDATION: 2026-09-15 to 2026-09-29 11:23
  (642). This is the split of the forensic studies. VALIDATION is the period the post-detection-edge study used
  as its test, read once there; its generic results (every strategy on all alerts loses after costs) are known
  before this study, its group results are not.
- Decision time: the alert (detector's T_DETECT). History for alert i: every earlier alert j with
  t_j + 60 s <= t_i (its 30 s window of exits is closed and margin added). Nothing of alert i itself after the
  alert is used: not its exits, not its `between` record, not its price after P0.
- The current snipers' funders (`last_funder`, the most recent SOL sender before each sniper's buy) and their hub
  status (measured before the funder's first funding in the corpus) are pre-alert facts. Live, they cost a few
  RPC calls per sniper (about 1 to 3 s): any feature that uses them is tested at entries of +5 s or later only.

## 2. Group recognition (frozen definitions)

Relations come from the frozen table exactly as stored; only their timing is restricted. Wallet roles in earlier
alerts: snipers (detector tickets, the creator included when it bought 5 SOL or more, as in the frozen table),
their non-hub last funders, the exit wallets their tokens went to by alert + 30 s.

- **G1, primary.** KNOWN: two current sniper wallets or more were snipers together in one earlier alert.
  PARTIAL: not KNOWN, and one current sniper was a sniper of an earlier alert, or the non-hub last funder of a
  current sniper funded a sniper of an earlier alert. UNKNOWN: neither.
- **G2, funder** (secondary). KNOWN: one non-hub last funder funds two current snipers or more and funded a
  sniper of an earlier alert.
- **G3, strong** (secondary). KNOWN under G1, and one non-hub funder funds two current snipers or more and funded
  a sniper of an earlier alert.
- **G4, exit structure** (secondary). KNOWN: a current sniper sent tokens to an exit wallet in an earlier alert.

Group history features at decision time (G1 basis): prior group launches (earlier alerts sharing two snipers or
more with the current one), prior appearances of the current snipers, time since the latest such alert,
recurring funder (G2), recurring exit structure (G4), current funding architecture (one non-hub funder for two
snipers or more).

Bins fixed now. Depth (prior group launches): 0, 1, 2 to 5, more than 5. Recency (since the latest group
launch): under 5 min, 5-15 min, 15-30 min, 30-60 min, 1-6 h, over 6 h. Stability: weak (exactly one current
sniper seen before, no recurring funder), medium (G1 KNOWN, not G3), strong (G3).

## 3. Features and models

- **Baseline (Model 1)**: n_snipers, log10 snipe_sol, supply_part, log10_mc_usd (market cap at P0),
  log10 entry_over_operator (premium), p0 on the pool (versus the curve), grouped actor (paquet_max >= 2). The
  pool reserve is a function of P0 under the cost model and adds nothing beyond the market cap. All from the
  post-detection-edge snapshot.
- **Group (Model 2)**: G1 KNOWN and PARTIAL indicators, log(1 + prior group launches), recurring funder, the
  recurrence of the exit structure.
- **Model 3**: Model 1 + Model 2, plus two interactions fixed now: KNOWN x log10 snipe_sol and KNOWN x
  n_snipers.
- Logistic regression on features standardised with TRAIN means, L2 penalty fixed at 1.0 (no tuning), fit on
  TRAIN, scored on VALIDATION.

## 4. Outcomes (from the frozen spot series)

- Entry: the first spot read at or after alert + L, L in {0 (P0), 5, 15, 30} s, under the snapshot's rules
  (a read within 10 s of L; coverage rule of `post_detection_edge/code/pde.py`).
- Returns from entry at 5 s, 10 s, 30 s, 60 s, 5 min, 15 min, 1 h: point return (the first read at or after
  entry + H, if the window is observed), maximum favourable and adverse excursion, drawdown before +50 %, time to
  +50 %.
- Binary targets: maximum favourable excursion of at least +10 %, +25 %, +50 % or +100 % within 60 s, 5 min,
  15 min or 1 h; complete-case (hits over observed windows), as in the snapshot's methodology.
- **Primary predictive target: +50 % within 15 min from an entry at +5 s.**

## 5. Trading simulation

The snapshot's simulator and cost model, unchanged: 1 % fee per leg, 0.005 SOL per transaction, constant-product
impact with the depth derived from price (K = 1.39e10 on the pool, the curve's virtual reserves otherwise),
take-profit filled at the target (resting order; "next read" as a sensitivity), stop filled at the read that
crosses it, a trade counted only if its whole holding window is observed. Failed transactions and front-running
are not modelled. Sizes: $500 primary, $100 and $1,000 secondary; K x 0.5 and x 2 as sensitivities.

- Entries: +0, +5, +15, +30 s.
- Strategy A, time exits: 10 s, 30 s, 60 s, 5 min, 15 min.
- Strategy B, target and stop with a 15-minute timeout: (+25 %, -10 %), (+50 %, -15 %), (+100 %, -20 %).
- **Primary strategy: entry +5 s, target +50 %, stop -15 %, 15-minute timeout, $500.**
- Populations traded: all alerts; G1 KNOWN; G1 UNKNOWN; G1 PARTIAL; the top 20 % of Model 1 and of Model 3
  (score at or above the TRAIN 80th percentile).
- Per strategy: trades, win rate, mean, median, expectancy, gross, fees, slippage, net, maximum drawdown of the
  cumulative equity in time order, worst trade, profit factor, average holding time, capital exposed, and
  break-even win rate before and after costs.

## 6. Primary hypothesis and tests

**Primary: on VALIDATION, G1 KNOWN alerts have a higher rate of the primary target than G1 UNKNOWN alerts, and
the primary strategy on KNOWN alerts has a positive mean net return.** TRAIN only says whether the comparison is
worth testing; VALIDATION decides.

- Predictive: rate difference KNOWN − UNKNOWN with a 95 % cluster-bootstrap interval (operators resampled,
  2,000 draws); Model 3 against Model 1 on VALIDATION: AUC, PR-AUC, Brier, log loss, calibration in five bins,
  and the log-loss difference with a cluster-bootstrap interval.
- Matched: coarsened exact matching of KNOWN and UNKNOWN on TRAIN tertiles of n_snipers, snipe_sol,
  supply_part, entry_over_operator and market cap; the stratum-weighted difference, cluster-bootstrapped.
- Operator controls (operator = the snapshot's union-find cluster, an inference label only, never a feature):
  full; without the dominant operator; within operators (Mantel-Haenszel difference over operators with both
  KNOWN and UNKNOWN alerts); operator-level aggregation (one mean per operator and status); leave-one-operator-out
  over the 10 largest operators; the funder definitions restricted to measured non-hub funders.
- Secondary, all reported: G2, G3, G4 (Holm across G1-G4 on the primary target in VALIDATION); depth, recency,
  stability; every target, horizon, entry, exit and size of sections 4-5. Anything positive outside the primary
  test is labelled exploratory.

## 7. Decision rule (exactly one class)

- **NO INCREMENTAL SIGNAL**: on VALIDATION the KNOWN − UNKNOWN difference on the primary target has a cluster
  interval that contains zero or the wrong sign after matching or within operators, and Model 3 does not lower
  the log loss of Model 1 (interval of the difference containing zero or worse).
- **STATISTICAL SIGNAL, NOT TRADABLE**: the predictive difference holds on VALIDATION (cluster interval above
  zero, same sign as TRAIN, holding within operators), but the primary strategy on KNOWN alerts has a mean net
  return at or below zero.
- **POTENTIAL TRADING SIGNAL**: the predictive difference holds and the primary strategy's mean net return on
  KNOWN is positive, but its cluster interval contains zero or one operator control fails.
- **ROBUST OUT-OF-SAMPLE TRADING SIGNAL**: all of the above with the cluster interval of the net return above
  zero, holding without the dominant operator, in leave-one-operator-out and in the matched comparison, costs
  included. TEST would still have to confirm before any live use.

## 8. Integrity checks

Every history alert precedes the decision by at least 60 s; no current-alert exit or `between` field read; no
price file opened by the group builder; splits and counts; unique mints; G1-G4 computed identically in TRAIN and
VALIDATION. Failures reported, not repaired.
