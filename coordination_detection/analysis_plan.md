# Coordination detection: analysis plan, written before any coordination rate is computed

Question: at the launch, can the on-chain data tell a launch whose buying wallets act as a
coordinated group from one whose buyers look independent?

This study does not predict any price outcome. No 2x, no ATH, no future market cap or volume is used
to define coordination, and no performance is computed. The frozen tables of the previous studies,
the future TEST and the live detector are not touched; nothing is pushed. "Manipulation" is not a
label: what can be shown is COORDINATED ON-CHAIN ACTIVITY, and the intent behind it is not observable
on-chain.

## Population and what it already is

The 1,657 alerts of the first snapshot, split as before: TRAIN before 2026-09-15 00:00 UTC (1,015),
VALIDATION after (642). Every one of them is a bundle snipe by the detector's own definition: at
least 4 wallets buying 5 SOL or more in the creation slot. Same-slot buying by several wallets is
therefore universal here and cannot separate launches; every comparison is made inside this already
selected population. Two existing structures are carried along, never redefined: the detector's
"grouped" launches (at least two snipers inside one transaction) and the operator clusters of the
previous studies (alerts linked by a shared sniper wallet, the same creator or the same ticket
configuration, which is partly wallet reuse by construction).

## Data (coverage.md)

Snipers (the detector's tickets, the creator's own buy included at 5 SOL or more): wallet, ticket,
slot, time, transaction; genesis funder (88.9 %), its source (88.9 %), last funder before the buy
(97.4 %). Creator: genesis funder (98.9 %) and last funder (99.3 %). Early buyers (everyone else
buying before alert - 1 s): wallet, amount, slot, time; their funders are not used (12.8 %
observed). Exits of the snipers (sell or transfer out) up to alert + 30 s, for the secondary
section only. A funder's hub status is the one measured before its earliest funding in the corpus;
a last funder without that measurement has an unknown status and is reported apart.

## Measures per launch (at alert - 1 s; no price)

1. Common funding, among snipers, separately for genesis funders and last funders, hubs excluded:
   number of funders, snipers per funder, `shared_funder_ratio` (snipers of the dominant funder over
   all snipers, only when every sniper's funder is known), share of the funded SOL from the dominant
   funder, HHI and Gini of the funding by funder, funding depth reconstructed (1 to 3 hops), number
   of distinct sources and the most funders on one source. Indicators: one funder for 2, 3, 4 snipers
   or a majority; two funders or more with the same source.
2. Synchronisation: snipers in one transaction (the most per transaction, share in multi-wallet
   transactions); the snipers' last funding times (spread, coefficient of variation, funding to buy
   delay); early buyers before the alert: share of buys sharing a slot with another, buys within
   1 / 5 / 10 s of the creation, burstiness ((sd - mean) / (sd + mean) of the gaps) and coefficient of
   variation of the gaps. Counts within 30 and 60 s use the window up to alert + 30 s and are
   descriptive only.
3. Tickets of the snipers: identical pairs (within 0.001 SOL), near-identical pairs (within 1 %),
   round tickets (within 0.01 of an integer), tickets within 0.5 SOL of 5, 10 and 20, max over
   median, HHI, Gini, entropy, top 1 / 2 / 3 shares, and whether the same ticket (to 0.01 SOL)
   appeared in an earlier alert.
4. Funding graph: nodes deployer, snipers, genesis and last funders, sources; edges the funding
   transfers and the buys. Components holding a sniper, the largest one in snipers, density, highest
   degree, the pairs of snipers joined only through the top funder, the deployer-to-sniper distance
   and the snipers joined to the deployer. Architectures, per launch: A, the deployer within two
   hops of a funder of two snipers or more; B, a source behind two funders or more who together fund
   two snipers or more; SHARED, a funder of two snipers or more without A or B; INDEPENDENT, every
   sniper in its own component.
5. Reuse, the priority: `co_occurrence(i, j)` = launches where wallets i and j are both snipers, over
   the corpus; recurring pairs (co-occurrence 2 or more), recurring groups (components of the
   recurring-pair graph), recurring funders (a non-hub funder of snipers in two launches or more).
   Per launch and without look-ahead: sniper pairs already snipers together in an earlier alert,
   snipers already seen as snipers before, a funder already seen funding snipers before. The same for
   the early buyers, descriptive.

## Null models (200 permutations each, inside each split)

- N1 wallets shuffled, amounts kept: sniper records (with their funders) reassigned across the
  launches of the split, launch sizes kept.
- N2 funders shuffled: snipers stay, their funders are reassigned among the split's sniper records.
- N3 timing shuffled, identities kept: the snipers' last funding delays, and the early buyers' delays
  from the creation, redrawn from the split's pool, counts and window lengths kept.
- N4 tickets redistributed across launches, launch sizes kept.
- N5 degrees kept: the wallet-launch bipartite graph rewired by swaps, each wallet's number of
  launches and each launch's number of snipers kept (co-occurrence and recurring pairs).
For every measure: observed value, mean under the null, its percentile, empirical p and 95 % null
interval, at the population level (TRAIN and VALIDATION apart). Per launch, the same nulls give the
launch's own percentile.

## Labels (per launch, fixed now, no price)

- SHARED_FUNDER: two snipers or more share a non-hub funder (genesis or last), and the launch's
  shared-funder count is above its 95th percentile under N1.
- HIGH_SYNCHRONIZATION: the spread of the snipers' last funding times is below its 5th percentile
  under N3 (funded together).
- FUNDING_CLUSTER: the largest non-hub funding component holds three snipers or more, or a majority,
  and is above its 95th percentile under N2.
- RECURRING_WALLET_CLUSTER: two snipers or more of the launch were snipers together in an earlier
  alert.
- MULTI-SIGNAL_COORDINATION: two or more of the four above. NO_SHARED_STRUCTURE: none.
A transparent score (the number of the four labels) is reported only if the four dimensions are not
redundant with one another on TRAIN (pairwise phi below 0.5 for at least three of them).

## Order and controls

TRAIN first (labels, null tests), VALIDATION once with the same rules, then:
- structure (redundancy): label against number of snipers, bundle SOL, supply share, premium, market
  cap at the alert, grouped vs single, operator; REDUNDANT WITH EXISTING STRUCTURE when a TRAIN model
  of those (boosting) predicts the label on VALIDATION with ROC-AUC 0.85 or more, or when the label
  and "grouped" agree with Cohen's kappa 0.8 or more;
- robustness: by week, by number of snipers (4, 5, 6+), by median ticket tercile, without the
  dominant operator, without the 10 most frequent sniper wallets, TRAIN and VALIDATION;
- operators: all, without the dominant one, operators seen 2 times or more, 5 times or more;
- price, measured after: the premium and the market cap by label, within bundle-size strata, and the
  premium against bundle SOL and supply share (the mechanical part);
- exits (secondary, descriptive, the labels already fixed): share of a group exiting by alert + 30 s,
  in one slot, buy-to-exit delay.

## Classification of each discovery

- ROBUST COORDINATION PATTERN: population null p below 0.01 in TRAIN and in VALIDATION, present in
  every week, not redundant, holds without the dominant operator and without the dominant wallets.
- PROBABLE COORDINATION PATTERN: null p below 0.05 in both splits, one robustness check failed (not
  the operator or the redundancy).
- OPERATOR-SPECIFIC: gone without the dominant operator, or half of its launches or more in one
  operator cluster.
- PRICE/STRUCTURE REDUNDANT: meets the redundancy rule above.
- RANDOM / NULL-COMPATIBLE: null p 0.05 or more in TRAIN or in VALIDATION.
- INSUFFICIENT DATA: the measure exists for fewer than half the launches.
