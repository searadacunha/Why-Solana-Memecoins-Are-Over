# Exit-wallet destination and loop closure: protocol, written before any new data is collected

Question: after a sniper moves its tokens to its recurring exit wallet, does the same economic network keep
the capital, and where does it end? Does the loop funder -> snipers -> exit wallets -> ... -> funder close?

No price, ATH, multiple, market cap, migration or profit defines any group, wallet, cluster, role, path or
classification, and no price file is read in this study. The coordination labels and the
economic-mechanics groups and clusters are taken unchanged from their frozen tables
(`coordination_detection` sha256 `eb710709...`, `economic_mechanics` sha256 `e6b4fdd8...`). The live
detector, the future TEST, the frozen tables and the earlier results are not touched; nothing is pushed.

## 1. What the corpus already holds (inventory of 2026-10-01, no call)

- 5,710 exit wallets received a sniper's tokens by transfer up to alert + 30 s; 1,737 of them in two
  launches or more (8,148 events; an event is one exit wallet in one launch, its receipt the earliest
  transfer it got from a sniper of that launch); 267 from two snipers or more; 30 in both TRAIN and
  VALIDATION; the dominant operator holds 12 % of these events.
- 1,296 of the 8,148 events already show a sale of the token by the exit wallet before alert + 30 s.
- The window collection read one page of earlier signatures for 288 of the 300 wallets selected below, and
  the genesis funding of 263; these are reused. What exit wallets do after alert + 30 s, where their SOL
  goes and the signatures themselves are not in the corpus.
- From the cached timestamps (2,822 events whose window is fully inside a cached page), the number of
  transactions of an exit wallet within 2 h of a receipt: median 6, p75 11, p90 20.

## 2. Population and selection (`code/ed_00_select.py`, frozen tables only, committed with this plan)

Population: the 1,737 recurring exit wallets. Score: launches (capped at 10) + 3 if fed by two snipers or
more + 3 if present in TRAIN and VALIDATION + 2 if most of its events have a non-hub funder that funds
snipers in two launches or more. Ranked by score, then events, then address; no economic-mechanics cluster
above a quarter of the sample. Result: 300 wallets, 3,963 events, 20 economic-mechanics clusters (largest 60
wallets), 16 operators, 174 fed by two snipers or more, all 30 TRAIN-and-VALIDATION wallets, 205 with a
recurring funder. Wallets with few transactions are not favoured: the activity known from the cache is not
used for selection.

Sampled events: per wallet, up to 5 events evenly spaced (indices round(i (n-1)/4)) over its events in time
order, its last event in the corpus excluded (that receipt is the listing cursor): 1,457 events (787 TRAIN,
670 VALIDATION; 283 wallets with 5, 4 with 4, 13 with 2).

## 3. Collection (`code/ed_10_collect.py`, Helius, transaction version 1)

Pace 2 calls per second per key, so that the live detector keeps its share. Every response is cached on
disk; an RPC failure raises and the item is recorded as failed, never as an empty history.

1. Listing, per wallet. Stage A: signatures strictly before the receipt of its last corpus event, paged back
   until 5 signatures before its first corpus receipt (at most 10 pages; beyond, the earlier events are
   "history not reached"). Stage B, only when a sampled window ends after that cursor: newest-first pages
   down to the cursor, at most 3; if not reached, those windows are cut at the cursor and flagged.
2. Before exit (prior association): the wallet's genesis funding (cached for 263, read for the others when
   its history has fewer than 3,000 transactions) and the 5 transactions immediately before its first
   corpus receipt.
3. After exit, per sampled event: the successful transactions after the receipt and within 2 h of it, in
   time order, at most 10, stopping early once (a) at most 1 % of the largest balance of the launch's token
   held in the window remains and (b) an outgoing SOL transfer of 0.1 SOL or more has followed the last
   sale (or no sale brought 0.1 SOL). The receipt itself is known from the corpus and not read again; a
   transaction already in the window cache is not fetched.
4. Hops: every outgoing SOL transfer of 0.1 SOL or more by the exit wallet in the event window starts a
   branch. A destination that is not a terminal (section 5) is read: its signatures newest-first (at most 3
   pages to reach the inflow; otherwise "too active, unresolved"), its hub status (3,000 or more
   transactions before the inflow, at most 3 pages back, measured once per address at its first inflow in
   this study) and its successful transactions within 2 h after the inflow, at most 5; the largest outgoing
   SOL transfer of 0.1 SOL or more among them is followed, the others are recorded and classified without
   being read. Maximum 5 hops from the exit wallet; a path still open after hop 5 is UNRESOLVED MULTI-HOP
   FLOW.
5. Order and budget: wallets in a seeded shuffle (seed 20261001); all listings and event windows first,
   then prior association, then hops breadth-first (hop 1 of every branch, then hop 2, ...), so a budget
   stop shortens the deepest hops evenly. Hard cap 18,000 calls (estimate below); at the cap the collection
   stops and every open item is "unresolved, budget". The collection also stops if more than 2 % of calls
   fail after retries.

Estimated calls: listings ~700, event windows ~8,700 (1,457 x ~6), prior association ~1,600, hops
~4,500; about 15,500, about 1 h at the pace above. Code: `ed_trace.py` (reading rules), `ed_10_collect.py`
(order, budget; the offline build calls the same function on the cache).

## 4. Classification of transactions (balance changes, never instruction names)

From the point of view of the wallet being read (fee added back for the signer, SOL = native + wrapped):
- token sale: its balance of the launch's token falls and its SOL rises, or a known venue (pump.fun curve,
  PumpSwap, a router) takes the token: economic liquidation;
- token transfer: its balance falls and another owner's balance of the same mint rises, no SOL received:
  a position transfer, not a liquidation; the recipient is classified (section 5) and not read further;
- SOL transfer out: native SOL falls by 0.1 SOL or more with no change in its token balances other than
  wrapped SOL; the recipient is the non-token account with the largest lamport gain (Jito tip accounts and
  token accounts excluded);
- next launch: it receives or buys another pump token;
- other: everything else (other swaps, account openings and closings), recorded, not followed.
Failed transactions are skipped. A SOL transfer after the wallet's next corpus receipt is flagged "pooled"
(the proceeds of two launches may be mixed).

## 5. Known wallets, terminals and return categories (fixed now)

Roles come from the frozen tables and count only if visible at or before the flow's block time (a launch
with t not later than it): snipers, their last and genesis funders and their sources, deployers and their
last and genesis funders, token recipients (exit wallets), and the non-hub funders of the snipers' funders.
Hub: measured before the relevant point only, from the frozen tables' hub fields, `genesis_hop` (status before
the address's earliest funding in the corpus) or here (3,000 or more transactions before the inflow). The
`genesis` cache counts histories up to its collection date and is not used for hub status. Known non-hub:
measured below the threshold there or here, or a sniper with fewer than 1,000 earlier transactions. A path stops at a hub, any known
wallet, no outgoing transfer of 0.1 SOL or more within 2 h, hop 5, or the budget.

Token disposal (B): sold / transferred / held at window end / other contract / untraceable (cap reached
with tokens left). Measured: delay from receipt, shares sold / transferred / remaining, token recipients,
several snipers sending the same token to the same exit wallet.

Sale proceeds (C), per event, the exit wallet's SOL movements in the window after its first sale:
A remain on the exit wallet; B to the event's sniper; C to the launch's funder (the sniper's non-hub last
funder); D to another known wallet of the corpus (those seen in two launches or more reported apart); E to a
deployer (of this or another launch); F to a hub; G split (two or more destinations among A-F, each at
least 0.1 SOL); H untraceable (cap reached, or a non-terminal unknown recipient).

Capital return (D), per branch, the first terminal reached, direct (hop 1) or multi-hop:
H1 the launch's funder; H2 another wallet of the launch's economic-mechanics cluster (its snipers, non-hub
funders and sources, exit wallets, deployers and their non-hub funders); H3 the deployer network (the
launch's deployer, its non-hub funders, any deployer of the same cluster and its non-hub funders); H4 a
known wallet outside the cluster; H5 a hub; H6 unresolved (stays, too active, hop limit, budget, window).
Precedence when one wallet fits several: H1, H3, H2, H4, H5. A hub never counts as H1, H2 or H3. An event
returns to H1 if any branch reaches H1; its SOL-weighted share is reported beside the count.

Direct transfer = hop 1; indirect flow = hops 2-5; structural association = a relation seen in the frozen
tables or in the prior history with no transfer observed (shared funder, same cluster, same genesis funder).

## 6. Recurrence, recycling, deployer linkage

- Recurrence matrix, exit wallets with two sampled events or more, share whose events all have: the same
  sniper, funder, economic-mechanics cluster, deployer network (frozen tables); the same first SOL
  destination, terminal wallet, hub, return category (new data).
- Recycling: launch A -> exit wallet -> path -> a wallet that funds a sniper or a deployer of a later
  launch B (its funding of B's sniper or deployer recorded in the frozen tables, after the flow). Time from
  A to B, SOL on the path, same funder, snipers, exit wallet, cluster, deployer network; chains of cycles.
- Deployer linkage: branches reaching H3, hubs never counted; null: the deployer network of another
  multi-launch cluster drawn at random.

## 7. Null models (1,000 permutations, seed 20261001)

1. Destination: first SOL destinations permuted among events with a resolved destination, each wallet's
   number of events kept; statistic: share of wallets with a repeated first destination; H1 rate.
2. Funder: the launch funders permuted among events (amounts carried); statistic: H1 rate.
3. Exit pairs: the sniper of each transfer permuted among the transfers of the sample, frequencies kept;
   statistic: share of exit wallets always fed by the same sniper.
4. Capital return: terminal wallets permuted among branches of the same hop depth, amounts kept;
   statistics: H1, H2, H3 rates.
5. Cross-launch: the exit wallet - launch bipartite graph rewired by degree-preserving swaps; statistic:
   exit-wallet pairs together in two launches or more.
Reported: observed, null mean and 95 % interval, percentile, empirical p = (1 + #)/(1 + N), effect.

## 8. Robustness and time

Full; without the dominant operator; without the 10 exit wallets with the most sampled events; known
non-hub (paths through a measured hub excluded); strict non-hub (paths through any wallet without a
measured non-hub status also excluded); TRAIN; VALIDATION; within operators with 30 sampled events or
more. Time: ISO calendar weeks of the receipt (return to funder, exit-wallet recurrence, downstream
recurrence, deployer linkage, recycling).

## 9. Integrity checks before any interpretation

Unique signatures; addresses and mints well formed; token amounts consistent with balance changes; SOL
flows consistent with lamport changes; times in order along each path; no transfer counted twice; no
negative balance; no flow counted twice across branches; no measured hub classified as a private wallet; no
role used before it is visible; no transaction after an event's window used for it; no price file opened.
Every failure is reported, none silently repaired.

## 10. Classification of mechanisms and report

ROBUST STRUCTURAL EVIDENCE: null p below 0.01 in TRAIN and VALIDATION, holding without the dominant
operator and the top 10 wallets. PROBABLE: p below 0.05 in both, one check failed or not run.
NULL-COMPATIBLE. INSUFFICIENT DATA. The report follows sections A to J and ends with the four sections asked
for. The central question is whether the loop closes, not whether anyone made money.
