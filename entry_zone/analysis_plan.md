# Entry zone: analysis plan, written before any rate is computed

Question: among the facts observable at a launch, is there a combination of a few simple filters
(entry market cap or premium, SOL already engaged, funding and spending capacity of the buyers) that
marks a zone where a 2x is clearly more likely than the base rate?

This is a new rule search, separate from `post_detection_forensics`. It does not modify that study's
frozen table, frozen model or results, and it does not touch the future TEST (alerts after
2026-09-29 11:23 UTC). Nothing is pushed.

## Data

- Alerts: the 1,657 alerts of the first snapshot (`post_detection_edge/data/journal.jsonl.gz`),
  split as before: TRAIN before 2026-09-15 00:00 UTC (1,015), VALIDATION after (642). VALIDATION
  was read by the two previous studies; it is not a pristine sample.
- Context read, not recomputed, from the frozen table of `post_detection_forensics`
  (`derived/analytic_table.jsonl.gz`, sha256 `9d2fd31f...`): split, operator cluster, actor label,
  entry premium over the operator and market cap at the alert (previous hour's SOL/USD).
- On-chain: the windows (every transaction on the mint from the creation slot to alert + 30 s) and
  wallet files of `post_detection_forensics/data/onchain_cache/`, read only.
- Prices: the detector's spot series (`post_detection_edge/data/series.txt.gz`): reads every
  ~5 s for 3 min after the alert (from 2026-08-25 21:47 UTC), then every ~45 s.
- The table built here (`derived/ez_table.jsonl.gz`) is frozen with its sha256 in
  `derived/EZ_FREEZE.json` and committed before the search.

## Cut-offs

A cut-off is the moment the decision is taken. Features use only transactions with a block time at
or before the cut-off minus 1 s, and only price reads at or before it. The entry price is the first
read at or after the cut-off, within 10 s (46 s at +5 min, the sampling step after 3 min); no read,
no entry.

| cut-off | trades used | market cap / premium | entry |
|---|---|---|---|
| T0, creation | the creation slot | not observable from the series | at the alert (P0): nobody can buy at T0 after a detection |
| D, alert | up to alert - 1 s | at the alert | P0 |
| +5, +10, +20, +30 s | up to cut-off - 1 s | last read before the cut-off | first read after |
| +60 s, +2 min, +5 min | up to alert + 29 s (the windows end at + 30 s) | last read before the cut-off | first read after |

Coverage per cut-off is reported. The windows stop at alert + 30 s, so after +30 s the trade
features are frozen at + 29 s; that is less information, never later information.

## Labels (per cut-off, from its entry price)

Primary: a 2x confirmed by two consecutive reads within 15 minutes of the entry, complete-case under
the coverage rule of `post_detection_edge/code/pde.py`. Also: 1.5x and 3x (confirmed, 15 min), time
to the first confirmed 2x, and the drawdown before the 2x (lowest read over the entry, from the
entry to the first 2x, or over the 15 minutes when there is none).

## Features (per cut-off)

- Price: market cap in USD, P0 and the multiple since the alert, premium over the operator, pool SOL
  reserve, SOL left on the bonding curve.
- SOL engaged: total bought, bundle (snipers and the creator's own buy), outside the bundle; per
  buyer mean, median, maximum; top 1, 2, 3 buyers; top buyer's share; concentration (HHI).
- Counts and timing: buyers, snipers, early buyers (everyone else), time since creation, buys in the
  first 5 and 10 s, time to the first buy outside the bundle.
- Capacity: each buyer's native SOL balance right before its first buy (from that transaction's
  `preBalances`) and right after; per launch, over all buyers, snipers and early buyers: sum,
  maximum, median, wallets holding 1 / 2 / 5 / 10 / 20 SOL or more, SOL spent over SOL available.
  Wrapped SOL is not counted.
- Funding, snipers only: first funding (amount, funder, whether the funder was a hub before its
  earliest funding in the corpus, delay to the launch); SOL received and number of funding
  transactions and funders in the 1 h, 6 h, 24 h and 7 days before the creation, from the genesis
  and the last 5 earlier transactions, kept only where they cover the window; share of snipers
  funded with about 1 SOL (0.9 to 1.1) and exactly 1 SOL (0.99 to 1.01); share funded by hubs; funder
  concentration; snipers sharing the top funder; ticket over recent funding.
- Early buyers' funding is not measurable: 73 % of them have 1,000 earlier transactions or more
  (the cap), and their SOL inflows before the launch would take a full scan of seasoned bots'
  histories. Only their activity counts (capped) and their balances are used.

## Search (TRAIN only)

Atoms, per variable and cut-off: every TRAIN decile as a lower and an upper bound, every interval
between two TRAIN deciles, and the declared grids: SOL engaged at 1, 2, 5, 10, 20, 30, 40, 50, 60,
70, 80, 90, 100 SOL and the zones 20-40, 40-60, 60-80, 80-100; market cap in USD tranches of 5k,
10k, 20k and 25k (intervals and bounds on the multiples); wallet counts at 1, 2, 3, 5.

Families: market cap, premium, SOL engaged, funding, capacity, counts and timing. Combinations: 2 to
4 atoms of one cut-off, from any family; pairs exhaustive, triples and quadruples by a beam of the
200 best.

Selection metric, the only one: the TRAIN lift lower bound, the Wilson 95 % lower bound of the
rule's primary rate minus the TRAIN base rate at that cut-off, with at least 40 TRAIN alerts.
"Best zone" of a family = its rule with the highest metric over all its variables and cut-offs; the
best combination likewise. Ties go to the larger N. VALIDATION is not read to choose anything.

Multiplicity: for each family and for the pairs, 200 permutations of the TRAIN labels within each
cut-off rerun the same search; the share of permutations whose best metric reaches the observed one
is the family's p. Triples and quadruples come from a larger search than the pairs and carry at
least the pairs' penalty.

## VALIDATION, once

For each family's best rule and the best combination: N, base, 1.5x / 2x / 3x rates, median time to
2x, median drawdown, Wilson CI, cluster-bootstrap CI of the lift, alerts excluded, ROC-AUC of the
variable where it is one. The VALIDATION rates of the 20 best TRAIN rules of each family are listed,
never used to choose.

## Controls against false signals (each kept rule)

1. premium, 2. operator, 3. number of snipers, 4. price already up since the alert: the lift beyond
TRAIN models (boosting, 150 rounds) of premium; actor; premium + actor; premium + actor + snipers +
run-up; on VALIDATION, observed minus expected inside minus outside, cluster-bootstrap CI. For
market-cap and premium rules the premium control is the rule itself and is not applied.
5. share of its VALIDATION alerts in its largest operator cluster; 6. VALIDATION halves and weeks;
7. for rules on SOL amounts, the same rule with the largest buyer removed; 8. VALIDATION without the
dominant operator; 9. VALIDATION without the "grouped" launches; 10. TRAIN against VALIDATION.

## Classification (one per discovery)

- NO SIGNAL: the family's permutation p is 0.05 or more.
- TRAIN OVERFIT: p below 0.05, and the VALIDATION Wilson lower bound is at or below the VALIDATION
  base.
- PRICE/OPERATOR CONFOUNDED: VALIDATION holds, but the lift beyond premium + actor has a CI reaching
  0 (not applied to market-cap and premium rules), or the VALIDATION lower bound falls to the base
  without the dominant operator or without the grouped launches.
- PROMISING BUT UNCONFIRMED: VALIDATION holds with at least 30 alerts, every control above passes,
  and the rate is above the base in both VALIDATION halves.
- ROBUST: needs the future TEST, because VALIDATION has been read by two studies; not reachable here.

## Trading simulation (rules whose VALIDATION lower bound is above the base)

Entry at the cut-off plus 0, 5, 10, 20 or 30 s; take profit at 1.5x, 2x or 3x, else exit at the
timeout of 5, 15, 30 or 60 min; no stop. The cost model of `post_detection_edge/code/trade.py`: 1 %
fee per leg, 0.005 SOL per transaction, constant-product price impact from the pool depth implied by
the price (K = 1.39e10, and x0.5), $100 / $500 / $1,000. TRAIN and VALIDATION, and all alerts with the
same exits as the reference.

## The operational sentence

"If I had to enter a launch, the observable conditions would be X + Y + Z, from a market cap between
A and B" is written only from rules classified PROMISING BUT UNCONFIRMED. Otherwise the report says
that no robust entry zone was found.
