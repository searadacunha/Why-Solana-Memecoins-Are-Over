# Funder network and final capital destination: protocol (scope B), frozen before any flow is read

Question: after the sniper → exit wallet → funder loop, do apparently separate operator networks converge into a
common capital network, or do their flows end in distinct networks?

No price, ATH, multiple, market cap, migration or profit is read or used. Coordination labels, groups, operators
(the frozen `cluster` label), snipers, exit wallets, funders and collectors are taken from the frozen tables of
`coordination_detection`, `economic_mechanics` and `exit_destination` (table sha256 `c09b0e77...`). Nothing
dated at or after 2026-09-29 11:23 UTC (start of the future TEST) is read: no transaction content, no
signature page beyond what is needed to find the boundary. The live detector is not touched; nothing is pushed.
No wallet is attributed to a person; graph structure is never read as ownership or intent.

## 1. Inventory and scope (done before this plan, commit 7ec0c62)

- Population (frozen): the 62 distinct recipients of the 1,280 sweeps of `exit_destination`: 42 H1 funders, 20
  collectors (3 wallets carry both labels) and 3 launch funders classified as hubs by the activity rule
  (D6HE3knc, 7xXmSDd2, BAKRUbZT). These complete the "42 funders and 20 collectors" to the 62 recipients; no
  other wallet enters the primary population.
- Already available: sweeps received (exit study), sniper and deployer fundings (frozen tables), the earlier
  status of 9 of the 62 in `genesis_hop`, signature pages of 20 collectors read by the exit study (all dated
  1 October, after TEST start: not used).
- Activity probe (62 calls): one page of signatures before each wallet's last sweep. 38 wallets have their whole
  history before that sweep in the page (100 to 800 transactions, "short-lived"); 24 have 1,000 transactions
  within 15 to 30 minutes ("very active", 40,000 to 140,000 a day). They receive 968 of the 1,280 sweeps and are
  the only wallets of 15 of the 24 operators.
- A 7-day census of all outflows was estimated at ~9.3 million transactions: above the 15,000-call ceiling.
  Benjamin chose scope B: lifecycle endpoints of the 38 short-lived wallets, a fixed sample of the 24 very
  active ones, the cached upstream data.

## 2. The graph

Node: a wallet; a hub (a wallet with 3,000 transactions or more before the relevant inflow, measured here, or
recorded as such in the frozen caches or by the exit study); a program only as the venue of a trade.
Edge: a SOL movement (source, destination, SOL, block time, slot, signature), from net balance changes (the
destination is the non-token account with the largest lamport gain, as in the exit study); a frozen funding (a
funder to a sniper or deployer, from the frozen tables); a sweep (exit study); a signing relation (the
signers of a transaction). Each edge carries its launch association (the last launch whose sweep the source
received before the edge, for the primary wallets) and the destination's role: funder, sniper, exit wallet,
deployer, collector (one of the 62), known hub, or previously unseen wallet. Roles count only once visible
(the launch's creation time is not later than the edge).

## 3. Collection (code/fn_10_collect.py; Helius, transaction version 1, 2 calls per second per key)

Short-lived wallets (38):
1. Upstream: the oldest signature of the probe page is the wallet's genesis; it is read and its funder is the
   account with the largest SOL loss. Each upstream wallet U that is not terminal (section 4) is read the same
   way strictly before the edge's signature: up to 3 pages back; 3,000 or more earlier transactions = hub
   (terminal); otherwise its oldest transaction is read and its funder becomes the next node. At most 5 hops.
2. Downstream: newest-first signature pages of the wallet, at most 3, until a signature before TEST start is
   seen (otherwise: "active beyond the TEST boundary", end unresolved); then its last 10 successful
   transactions before TEST start (and after its last sweep) are read. Every outgoing SOL movement of 0.1 SOL or
   more among them starts a downstream branch.

Very active wallets (24):
3. Upstream: up to 3 signature pages before the wallet's first sweep; if its history ends there, its oldest
   transaction is read and followed as in 1; otherwise upstream "unresolved: 3,000 or more earlier
   transactions".
4. Sample: three anchors, its first, median and last sweep in the exit sample (fewer when it has fewer sweeps);
   for each, the 10 signatures immediately before the anchor (one page of 10), of which the successful ones are
   read and classified. Every outgoing
   SOL movement of 0.1 SOL or more in the sample starts a downstream branch.

Downstream branches (both kinds): a destination that is not terminal is read as in the exit study: its
signatures newest-first until the inflow (at most 3 pages, else "too active", unresolved), 3,000 or more
earlier transactions = hub, otherwise its first 5 successful transactions within 7 days after the inflow and
before TEST start; the largest outgoing movement of 0.1 SOL or more is followed, the others recorded and
classified without reading. At most 5 hops, then UNRESOLVED >5 HOPS. A cycle back to a node already on the path
ends it ("circular flow", never counted as new capital).

Order and budget: upstream chains, then short-lived ends, then very-active samples, then downstream branches
breadth-first (hop 1 of every branch, then hop 2 ...). Hard cap 6,000 calls (plus the 62 of the probe;
estimate ~4,500); at the cap every open item is "unresolved, budget". Stop if more than 2 % of calls fail. An RPC
failure is recorded, never read as an empty history. Responses of the exit study's cache are reused read-only.

## 4. Terminals and destination classes (fixed now)

A path stops at a hub, at any wallet known in the frozen tables (any role) or in the population, at no movement
of 0.1 SOL or more within the window, at 5 hops, at the TEST boundary or at the budget. Classes, first match in
this order:
- A KNOWN HUB: hub as defined in section 2 (an activity proxy, never an identified exchange or service).
- D DEPLOYER NETWORK: a deployer, or a non-hub funder of a deployer, in the frozen tables.
- E CROSS-OPERATOR NETWORK: a wallet tied to two operators or more, through the frozen tables (snipers, their
  funders and sources, exit wallets, deployers and their funders of those operators' launches) or through this
  study's edges from the primary wallets of two operators.
- C OPERATOR-ASSOCIATED: tied to exactly one operator, the same as the source's.
- B RECURRING PRIVATE WALLET: known in the frozen tables in two launches or more, non-hub, tied to another
  single operator than the source's (reported apart as "other operator").
- F NEW / UNKNOWN: unseen wallet that keeps the SOL (no movement of 0.1 SOL or more read after the inflow).
- G UNRESOLVED: too active, budget, more than 5 hops, TEST boundary, RPC failure.

## 5. Measures

- Funder → destination map: per primary wallet and per operator, the classes of its upstream source and of its
  downstream terminals, by count and SOL.
- Convergence: for every non-primary wallet reached (upstream or downstream), the operators, primary wallets and
  launches connected to it, SOL, first and last activity; destinations unique to one operator, shared by two,
  by three or more. Three relations kept apart: capital transfer (a path from one operator's wallet into another
  operator's wallet), shared infrastructure (one wallet used by two operators without a demonstrated transfer
  between them, including the frozen case of one funder serving two operators), common terminal (flows of
  different operators ending at the same wallet).
- Components: primary wallets joined when they share a non-hub upstream or downstream wallet (hubs never join);
  per component: wallets, operators, launches, downstream wallets, SOL, architecture.
- Recycling: a downstream wallet that funds, in the frozen tables, a sniper or deployer of a later launch after
  the edge: same operator, another operator, a deployer, another funder, unknown; amount, delay, repetitions.
- Deployer relationship: direct (hop 1) and indirect, strict non-hub, against null A.
- Terminal distribution per primary wallet and per operator, by SOL; an operator whose terminals are all one
  class is reported as such.
- Very active wallets: composition of the sampled transactions (sweep received, sniper funding, other SOL out,
  other SOL in, trade, other).

## 6. Null models (1,000 permutations, seed 20261001), preserving operator structure

- Null A, destinations: the primary wallet - destination edges rewired by degree-preserving swaps (each primary
  wallet keeps its number of destinations, each destination its frequency). Statistic: destinations tied to two
  operators or more; operators in the largest component.
- Null B, operators: operator labels permuted among primary wallets, each operator keeping its number of
  wallets. Same statistics.
- Null C, cross-operator: swaps allowed only between edges of different operators, each operator keeping its
  destinations count. Statistic: destinations shared by two operators or more.
- Null D, recycling: recycled capital's recipients permuted among the frozen funding events of the same time
  block (ISO week), amounts and times kept. Statistic: share of recycling links to the same operator.
Reported: observed, null mean and 95 % interval, percentile, empirical p, effect. With few shared destinations
these tests have little power; the counts themselves are reported first.

## 7. Robustness and time

Full; without the dominant operator (most primary wallets); without the 10 primary wallets with the most sweeps;
known non-hub (hub edges removed); strict non-hub (only wallets with a measured non-hub status join
components); TRAIN and VALIDATION (an operator's split from its launches); operator-level aggregation as the
principal layer. If convergence disappears without one wallet, it is said. Time: first and last appearance of
every shared wallet, ISO weeks active, operators over time (persistent, episodic, one period, one wallet).

## 8. Integrity checks before interpretation

Unique signatures; well-formed addresses; SOL from balance changes (recipient gain against source loss);
times and slots in order along each path (descending upstream, ascending downstream); no transfer counted twice;
no hop counted twice; no circular flow counted as new capital; no measured hub classified private; no role
used before it is visible; nothing at or after TEST start read; no price file opened. Failures reported, never
repaired.

## 9. Reading of results

Same destination, shared infrastructure, capital pooling and common economic network are kept distinct; a
single actor is never concluded from structure. The report follows sections A to J of the brief and ends with
WHAT THE BLOCKCHAIN PROVES / WHAT THE NETWORK STRUCTURE STRONGLY SUGGESTS / WHAT REMAINS UNRESOLVED / NEXT MOST
INFORMATIVE TEST. Coverage limits of scope B (no census of the very active wallets, intermediate outflows of
short-lived wallets not read) are stated with every result they bound.
