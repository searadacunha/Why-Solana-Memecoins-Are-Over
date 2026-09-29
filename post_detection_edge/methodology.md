# Methodology

The question: once a bundle snipe is detected, does buying right after still yield large multiples,
and can anything observable at detection tell the launches that will from those that will not? The
study was set up to refute that, not to confirm it. Everything below was fixed before the TEST split
was read, except where a section says otherwise.

## 1. Why the repository's own data could not answer it

The dossier's earlier populations do not contain a prospective denominator with a price path:

- the 42 launches verified transaction by transaction (`data/v05`, `v06`, `v07`) were selected by
  membership of four operator fleets, inside a capture corpus biased toward launches that graduated;
- the 70 tokens of `data/v09_signature_gros_tokens.json` and the pump.fun ranking frame are selected on
  an ATH of at least $500k;
- population A (`data/dataset_socle.json`) is a detector log over three days whose detection arrives
  275 s after creation in median, with no price series, only an API ATH.

The only corpus that lists every bundle snipe of a period, with a price at detection and a path after
it, is the live detector's journal: a separate, unpublished project that has alerted on bundle-sniped
pump.fun launches since 2026-08-21. This study freezes a copy of it.

## 2. The snapshot

`code/snap_00_freeze.py` copied the detector's journal and price series once, cut every line at a single
instant (T_SNAP = 2026-09-29 11:23:00 UTC), dropped what the study must not see (message texts, palier
and 8-minute verdict messages), and wrote `data/SNAPSHOT.json` with a sha256 per file. The files are
read-only; the script refuses to run twice. A second, deliberate freeze on the same T_SNAP applied the
repository's write-time redaction of slur-vanity identifiers (`code/redact.py`, injective, so no count
moves); it is recorded in the manifest's `history`. `code/snap_01_solusd.py` froze hourly SOL/USD
(Binance, keyless) over the same window. No data was added after the snapshot. Later alerts belong to
a separate, future test.

Contents: 1,657 launch alerts, 7,005 rejected candidates with their creation-block measurements,
1,650,815 price reads, the detector's outage lines (158 machine freezes, 172 WebSocket gaps, 26
restarts), and the five caches of the protocol pre-registered on 2026-08-29.

## 3. Unit, clock and prices

**Unit of analysis**: one alert, i.e. one launch, i.e. one potential buy decision.

| time | definition | resolution in the data |
|---|---|---|
| T0 | creation of the token: the creation slot | slot |
| T1 | the bundle's purchases | the same slot as T0 by construction of the definition; only the transaction index inside the block separates them, never a time |
| T_DETECT | the alert: the moment the detector had read the creation block and decided | wall clock, 0.1 s; 11.8 s after the creation block in median (q10 7.5 s, q90 15.9 s), set mostly by the detector's 10 s polling |
| T_ENTRY | the first price available at or after T_DETECT + L, L in {0, 5, 10, 15, 20} s (30 and 60 s in one descriptive table) | reads about 5 s apart for the first 180 s after the alert (alerts from 2026-08-25 21:47 UTC), 45 s otherwise |

An earlier detection is possible in principle: the information sits entirely in the creation block and
becomes readable once that block is confirmed. The corpus has no price between the creation block and
the alert, so nothing faster than the detector's own latency is measured, and +1 s / +3 s entries are
not measurable either.

**P0** is the spot price the detector read at the alert: from the PumpSwap pool reserves (1,551
alerts) or from the bonding curve (106). It is already after the bundle's impact, and in some pools
after the creator's own purchase of the pool in the creation block. It is not an execution price.
Every result is labelled as spot, and execution is estimated separately (§8).

## 4. Targets and censoring

For a horizon H and a threshold k, from an entry at T_ENTRY:

    MFE_H = max(price read in (T_ENTRY, T_ENTRY + H]) / entry price
    TARGET_kX_H = 1 if MFE_H >= k

H in {10 s, 30 s, 60 s, 5 min, 15 min, 1 h, 24 h}; k in {1.5, 2, 3, 5, 10}.

The detector's machine slept for long stretches, so many windows have holes. A window is **observed**
when no two consecutive reads inside it (the entry included) are more than G apart and the reads reach
H. G = 25 s inside the first 180 s of fine sampling (the 99th percentile of gaps there is 23.9 s),
135 s elsewhere (three missed 45 s rounds; 99th percentile 51.2 s). The rule was set from the sampling
alone, before any outcome was computed. Then, per alert and horizon:

- **hit**: a read at or above k inside the window (a read is a real price, even in a window with holes);
- **observed miss**: the window is observed and no read reaches k;
- **censored**: no hit and the window is not observed;
- **missing**: no series, or a horizon shorter than 180 s for an alert sampled every 45 s.

The primary estimator is **complete-case**: hits over observed windows, whether hit or not. Because the
set is decided by coverage alone, it does not lean toward winners as long as the outages are unrelated
to the tokens, which machine sleep is. Bounds are printed next to it (censored scored as miss, then as
hit). Coverage at P0: 1 h is observed for 1,297 alerts, 24 h for 47, so the 24 h horizon never carries a
conclusion.

**Primary target: 2x within 1 h.** It is the longest horizon observed for at least 75 % of alerts. It
was chosen on coverage, before any rate was computed. 5 and 15 minutes were added as targets of the
multivariate search after the univariate screen showed effects there in TRAIN that kept their
direction in VALIDATION.

## 5. Features known at T_DETECT

Read from the alert record, or built from journal lines strictly older than the alert.

| family | features |
|---|---|
| bundle | n_snipers, snipe_sol, supply_part, ticket_mean, ticket_median, ticket_std, ticket_cv, core_cv, ticket_min, ticket_max, max_share, hhi, ticket_range_rel, round_share (share of tickets within 0.01 SOL of an integer), sol_per_sniper |
| block | n_buyers, extra_buyers, ntx, nko, fail_ratio, complete_at_block, amorce (creator's first buy) |
| actor | paquet_max (core purchases per transaction), actor = grouped if >= 2 else single; 112 early alerts labelled afterwards from their creation block, which holds the same information |
| market at the alert | log10 p0, market cap in USD at P0, log10 operator VWAP, entry_over_operator = p0 / operator VWAP, p0_source, age_alert_s |
| time | hour (4-hour bins), weekday. The date itself is excluded: a rule on dates cannot transfer to a later split |
| context, causal | alerts and candidates in the previous hour, creator seen before, maximum prior reuse of the sniper wallets, prior uses of the same ticket configuration |

Not available, and therefore not used: intra-block timing (the bundle is one slot), signatures beyond
counts, anything about funding lineage after 2026-08-31 (never collected).

Forbidden, and absent from the feature path: any multiple, ATH, closure, palier, 8-minute verdict,
trade, volume, buyer or wallet behaviour after the alert, `t_mult*`, `t_buyable`.

**Operator clusters** (for inference only, never a feature): alerts linked by a shared sniper wallet,
the same creator or the same ticket configuration, by union-find over the whole snapshot. 319 clusters;
the largest holds 320 alerts.

## 6. Walk-forward

| split | alerts | window (UTC) | role |
|---|---:|---|---|
| TRAIN | 325 | 2026-08-21 17:35 to 2026-08-29 18:04 | exploration, feature and threshold choice, rule discovery. These are the alerts earlier campaigns had already searched; its end is the T0 of the protocol pre-registered on 2026-08-29 18:36 |
| VALIDATION | 690 | 2026-08-30 11:11 to 2026-09-14 23:04 | final selection, limited tuning (the logistic penalty, the tree depth) |
| TEST | 642 | 2026-09-15 10:46 to 2026-09-29 10:47 | read once, after the lock |

The dates proposed by the audit were kept. TRAIN is small (250 alerts observed at 1 h), and 207 of its
alerts have no horizon under 180 s. That limits discovery. It does not bias validation or test.

The test file was written separately (`derived/dataset_test.sealed.jsonl.gz`), and no script read it
before `tables/LOCK.json` existed. The lock, the code and the datasets were committed (`e310335`) before
the first read. `an_60_final_test.py` checks the datasets' sha256 against the lock and was first run
with `--rehearse`, which substitutes VALIDATION for TEST, to debug it without opening TEST.

## 7. Search, selection, lock

**Univariate** (`an_30`), TRAIN then VALIDATION: AUC, a label-permutation p (2,000 draws), TRAIN
quartiles, and the best quartile tested against the permutation null of the maximum over bins. Then a
secondary grid of AUCs over every threshold and horizon with at least 5 TRAIN positives, Benjamini-
Hochberg across it.

**Multivariate** (`an_40`), per target (2x within 5 min, 15 min, 1 h):

- rules: conjunctions of 1 to 3 conditions, each a feature against one of its TRAIN deciles (<= or >)
  or a categorical level; pairs exhaustive, triples by beam over the 100 best pairs; TRAIN support at
  least 20; TRAIN score = Wilson lower bound; duplicates on identical TRAIN rows collapsed. The 50 best
  go to VALIDATION, and the one with the best VALIDATION Wilson lower bound (VALIDATION N >= 30) is
  locked;
- ridge logistic regression on standardised features (TRAIN medians impute), penalty chosen on
  VALIDATION AUC; signal = score at or above the TRAIN 80th percentile;
- CART of depth 2 or 3 (chosen on VALIDATION AUC), leaves of at least 20; signal = the best TRAIN leaf.

**Hypotheses fixed before the study**, locked as stated: H1 grouped actor, H2 market cap under
$60,000, H2b market cap in [$40,000, $60,000), all on the primary target.

**Search budget**: 485 univariate tests; 1,461 conditions; 482,519 rules evaluated; 18 models fitted;
7,291 tree thresholds; 12 locked signals.

**Decision rules**, written into the lock before TEST:

- a signal **survives** if on TEST: N >= 30 alerts observed, one-sided Fisher p (signal against the rest
  of TEST) < 0.05 after Holm across the 12 locked signals, and a 95 % cluster-bootstrap CI of
  (P(signal) - P(rest)) above zero;
- a surviving signal is an **edge** only if its primary strategy, entered 10 s after the alert with
  $500 under the cost model below, has a mean net return on TEST whose 95 % cluster CI is above zero;
- the Wilson lower bound against 0.6 and 0.8 is reported, never used as a criterion.

## 8. Trading, costs, latency

Pre-declared exits: S1 TP 1.5x / SL -20 % / 5 min, S2 TP 2x / SL -20 % / 5 min, S3 TP 3x / SL -20 % /
5 min, and hold to 2x with a timeout of 5 min, 15 min or 1 h (each signal's primary strategy is the
hold matching its target horizon). A take-profit fills at exactly the TP (a resting order; the
alternative "sell at the next read" is shown). A stop fills at the read that crosses it, gaps
included. A trade counts only if its whole holding window is observed, decided before the exit is
looked at.

Costs are estimated, not measured: 1 % per leg for router and DEX fees, 0.005 SOL per transaction for
priority fee and tip, and constant-product price impact on both legs. The data holds no depth, so the
SOL reserve is derived from the price, reserve = sqrt(K x price), with K from one migration the
detector's audit read on chain (67.4 SOL against 206.9 M tokens, K ~ 1.39e10) and from pump.fun's
virtual reserves (30 SOL x 1.073e9 tokens) when P0 was read on the curve. K is varied x0.5 and x2.
Sizes $100, $500, $1,000 at the SOL price of the alert's hour. Front-running, failed transactions and
MEV are not modelled; each would lower the results.

Latency: entries at +0, +5, +10, +15, +20 s after the alert, on fine-sampled alerts.

## 9. Inference

Wilson intervals for proportions. Cluster bootstrap (operators resampled, 2,000 draws, fixed seed) for
differences of rates and for mean returns. Leave-one-cluster-out for the headline signal and every
survivor. Fisher tests are at alert level and therefore optimistic; the cluster CI is the check that
counts.

## 10. Limits

- One window, 2026-08-21 to 2026-09-29, one detector definition. June and July are not covered.
- The detector was down for at least ~600 of ~930 hours; launches in those hours are missing, and
  whether they differ is not measurable.
- Every price is a spot read of reserves, about 5 s apart at best. A peak between two reads is missed,
  so MFEs are slightly low; a read is never invented.
- Execution costs rest on a derived depth and stated fees, not on fills.
- 5,902 launches met the repository's broader definition (at least 60 SOL in the creation slot) and were
  never followed, 5,127 of them with a single sniper of 5 SOL or more. Nothing here speaks for them.
