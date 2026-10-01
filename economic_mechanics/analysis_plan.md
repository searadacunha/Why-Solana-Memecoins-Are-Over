# Economic mechanics of coordinated groups: analysis plan, written before any measure

Question: do the coordinated groups found in `coordination_detection` follow a repeatable economic
operating structure: funding, creation, coordinated buys, supply held, price impact, coordinated
exits, redistribution, reuse on later launches?

No price outcome defines anything. The groups are the frozen labels of `coordination_detection`
(`derived/C_results.json`, committed in `ec0651c`), taken as they are. Prices after the creation slot
appear in one section only (price impact), after every group, role and architecture is fixed. TRAIN
and VALIDATION as before; the future TEST is not touched; no RPC call; nothing is pushed. The report
keeps four levels apart: observable facts, statistically abnormal structures, inferred economic roles,
hypotheses about control or intent.

## Groups (fixed now, from the frozen labels)

- COORDINATED: launches labeled MULTI-SIGNAL_COORDINATION (two of the four coordination labels or
  more): 884 TRAIN, 520 VALIDATION.
- CONTROL: launches with one label or none (131 and 122); STRICT CONTROL: NO_SHARED_STRUCTURE (28 and
  25). Every coordinated-against-control comparison is given for both.
- The group of a launch is its snipers (the detector's tickets, the creator included when its own buy
  is 5 SOL or more).

## Data (coverage measured on 2026-10-01, no RPC call)

- From the frozen coordination table: snipers, funders (last before the buy, 97.4 %; genesis, 88.9 %),
  sources, hub status, the deployer and its funders, early buyers, sniper exits up to alert + 30 s.
- Added from the same cache: tokens bought, each exit's tokens, SOL received and balance after, the
  token recipients of transfers out, the creation slot's SOL by buyer and the bonding-curve or pool
  state after it, the deployer's last 20 transactions before the creation (transfers to funders), and
  for every sniper that snipes again later, its transactions between the two launches as recorded
  before its next buy (complete for 1,601 of 2,970 such records).
- Not observable: where the SOL goes after an exit for snipers that never snipe again in the corpus,
  anything after alert + 30 s (exits at 60 s and 5 min after the buy are censored), the slot of a
  funding transaction (its time to the second is known, and whether several snipers share it).

## Measures

1. Role graph and architectures, per launch, from the last funders (genesis funders as a sensitivity),
   hubs never shared:
   - C: the deployer itself funds two snipers or more;
   - A: a funder of two snipers or more received SOL from the deployer (in the deployer's last 20
     transactions, or as its genesis funder), or funded the deployer;
   - B: a common funder of two snipers or more, no deployer link;
   - D: two funders or more, each funding two snipers or more, or linked by a common source;
   - E: no two snipers share a funder and none is linked to the deployer;
   - UNRESOLVED: a sniper's funder unknown. A launch can be C and D at once; both are reported.
2. Funding mechanics: SOL funded in total and per wallet, wallets funded, dispersion of funding
   times (s) and amounts (CV), funding to creation and funding to buy, share funded less than 1, 10
   and 60 minutes before, snipers funded in one same transaction, funders funded by the deployer.
   Median, Q25, Q75, Q90, minimum and maximum, coordinated against control.
3. Capital lifecycle per sniper: SOL received (last funding), SOL spent (ticket), SOL received from
   exits up to alert + 30 s, residual native balance, tokens bought and sold, share of the position
   gone by alert + 30 s, time to the first exit, time to a complete exit (99 % or more, censored
   otherwise), token transfers out and their recipients; for snipers seen again: SOL sent out between
   the two launches and to whom (the first launch's funder, its deployer, another sniper, another
   wallet), and the funding of the second launch (same funder or not).
4. Supply: tokens bought by the group, their share of the supply, the largest sniper's share, HHI,
   the group's net position change before the alert.
5. Price impact (descriptive, after everything above is fixed): the curve's initial price, the price
   after the creation slot, P0, the maximum within 10 s, 30 s, 60 s and 5 min of the creation (window
   reads to alert + 30 s, then the detector's series), the creation slot's SOL by the group against
   the others. Attribution inside the slot is only by SOL share: the order of transactions inside a
   slot is not known.
6. Exits: share of snipers exiting within 5, 10 and 30 s of their buy (60 s and 5 min censored),
   share of the position, exits in one slot, the spread of exit times, the similarity of the sold
   fractions, coordinated against control.
7. Recurrence: per sniper, funder, deployer, sniper pair: launches, time between launches, repeated
   funder-to-sniper and deployer-to-funder relations, the same architecture again.
8. Clusters from information at or before each launch only: a union of wallets joined by a sniper
   pair in one launch, a non-hub funder-to-sniper relation, a deployer-to-funder relation or a common
   source. Number, sizes, launches per cluster, dominant architecture, how many operator clusters of
   the previous studies each one spans, and whether TRAIN clusters reappear in VALIDATION.

## Null models (1,000 permutations, inside each split)

- Funding: funders permuted among the split's sniper records, launches, snipers and funding counts
  kept (shared funder, one funding transaction for several snipers).
- Timing: the snipers' funding delays shuffled across the split's records (funding-time spread).
- Pair recurrence and clusters: the wallet-launch bipartite graph rewired by swaps, degrees kept
  (recurring pairs, launches per cluster).
- Exits: exit delays shuffled across the split's exiting snipers, who exits kept (exits in one slot,
  spread of exit times); the sold fractions shuffled likewise (similarity).
- Proceeds: for snipers seen again, the first launch's funder replaced by a random funder of the same
  split (outflows reaching the first launch's funder).
Each gives the observed value, the null mean and 95 % interval, the percentile, the empirical p and an
effect size (observed over null mean).

## Robustness

Full corpus; without the dominant operator; inside the operators with 30 launches or more; without
the 10 most frequent sniper wallets; known non-hub funders only; genesis funders only.

## Roles and hypotheses

Behavioral roles (deployer, upstream funder, sniper, exit wallet, collection wallet, funding service,
recurring infrastructure wallet), each with the observation that supports it. The hypotheses: A
independent traders, B one trader splitting an order, C a coordinated group, D a bundling or
execution service, E deployer-controlled wallets, F another structure; for each, which observations
are consistent and which discriminate. No winner is named unless an observation separates them.

## Classification of each mechanism

- ROBUST STRUCTURAL EVIDENCE: null p below 0.01 in TRAIN and VALIDATION, holding without the dominant
  operator and the dominant wallets.
- PROBABLE STRUCTURAL EVIDENCE: null p below 0.05 in both, one robustness check failed.
- NULL-COMPATIBLE: null p 0.05 or more in either split.
- INSUFFICIENT DATA: observed for fewer than half the relevant records, or not observable.
