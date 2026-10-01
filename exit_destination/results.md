# Exit-wallet destination and economic loop closure: results

Protocol: [analysis_plan.md](analysis_plan.md), committed with the selection and the collector (d75fd05) before
any call. Frozen table: `derived/ed_table.json.gz`, sha256 `c09b0e77...` (`derived/ED_FREEZE.json`); integrity
report `derived/ED_INTEGRITY.json`. Tables `tables/B_tokens.md` to `tables/J_fingerprint.md` are the
pre-registered analysis; `tables/K_posthoc.md` holds the checks added after reading them, all descriptive and
marked post hoc below. No price, multiple, migration or profit defines anything here, and no price file was
opened (an audit hook refuses it).

Data: 300 recurring exit wallets chosen from the frozen tables, 1,457 sampled events (an exit wallet in one
launch), 148 launches (117 TRAIN, 31 VALIDATION), 25 operators. Every event was read: 1,096 to the end of the
selling, 361 stopped by the 10-transaction cap. 9,757 Helius calls (plus 11 of a smoke test not in the counter)
out of the 18,000 cap, no failure. The live detector logged no confirmation failure and no freeze during the
collection (10:07 to 10:37 UTC, 2026-10-01).

## A. Executive summary

- **Tokens.** Each exit wallet sells the tokens itself, on PumpSwap, a median 81 s after the sniper hands them
  over (6,049 sales of 6,049, all paid by the exit wallet). No token is passed on: the sniper's transfer is a
  position transfer, the exit wallet's sale is the liquidation.
- **SOL.** All 1,280 outgoing SOL transfers have one shape. A transaction with four signers moves the exit
  wallet's SOL through a one-time address and wrapped SOL to a recipient that pays the fee. The exit wallet
  signs, the recipient signs, and the one-time address has no other transaction in its history. In 85 % of
  them the exit wallet is left with nothing.
- **Return to the funder.** 62 % of these transfers (67 % of the 13,645 SOL) go straight to the wallet that
  funded the launch's snipers, the same launch, 28 s after the last sale (median). Under the plan's strict
  rule, which classes 157 of them as hubs because the funder is very active, the share is 49 % (H1). That is
  against 3 % under the null, in TRAIN and in VALIDATION.
- **Operator by operator.** 17 of the 24 operators with transfers send 80 to 100 % of them to the launch's
  funder. The 7 others send them to a separate, very active collector that appears nowhere in the frozen
  tables. No operator is in between.
- **Same cluster.** An exit wallet keeps its first SOL destination in 42 % of cases (null 1 %) and its cluster
  in 44 % (null 0.3 %). Within an operator, routing is fixed.
- **Recycling.** 52 % of the events with a transfer (null 29 %) send capital to a wallet that funds a sniper of
  a later launch, a median 18 minutes later. That later launch always has the same snipers and the same
  cluster; in 95 % of cases it has the same exit wallet, in 76 % the same funder, and never the same deployer
  network.
- **Deployers.** No path reaches a deployer or a deployer's funder. Paths stop at the first known wallet,
  usually the funder, so what the funder does next is not observed here.
- **One unit or a service?** The co-signed sweep proves that one signing process held the keys of the exit
  wallet, of the recipient and of two one-time addresses. That fits one economic unit, and it also fits an
  execution service that holds its clients' keys. The data do not separate them. Independent traders do not
  fit the co-signatures.
- **Still open.** Where the capital of the 7 collector operators ends up (304 transfers to wallets too active
  to follow). Where funders and collectors send capital after they receive it. Who controls any key.
- **Does the loop close?** For 17 operators out of 24, yes, and every step is an observed transfer:
  funder → snipers → exit wallets → sale → sweep back to that same funder → the same snipers funded again.
  For the other 7, the loop is not seen to close within 2 h and 5 hops. It is open, not refuted.

## B. Token exit paths

Sniper → exit wallet → token (`tables/B_tokens.md`, `K_posthoc.md` sections 2 and 6).

| exit wallet's disposal of the token | events | % |
|---|---:|---:|
| sold, nothing left | 1,131 | 78 % |
| sold in part when the 10-transaction cap stopped the reading (median 10 sales read) | 326 | 22 % |
| transferred onward / other contract / held to the end of a complete reading | 0 | 0 % |

- Amounts: 56 % of the tokens were sold within the transactions read. The remaining 44 % sit only in the
  capped readings, in the middle of a run of sales; that is unread selling, not holding.
- Delay from the sniper's transfer to the exit wallet's first sale: median 81 s (p25 35, p75 143, p90 330, max
  641).
- Venue: PumpSwap for all 6,049 sales. Every sale is signed and paid by the exit wallet itself.
- One sniper per exit wallet per launch: no event had two snipers sending the same token to the same exit
  wallet.
- Fan-out (frozen corpus, post hoc): a sniper usually feeds one exit wallet (3,603 sniper-launches), but a
  family of operators splits each sniper's tokens over 7, 8 or 15 exit wallets (174, 178 and 262
  sniper-launches).

## C. SOL destination

Exit wallet → SOL, direct, after its first sale. These are the pre-registered categories of section 5
(`tables/C_proceeds.md`).

| category | events | % | SOL | TRAIN | VAL | launches | exit wallets |
|---|---:|---:|---:|---:|---:|---:|---:|
| A remains on the exit wallet (complete reading) | 0 | 0 % | | | | | |
| B back to the event's sniper | 0 | 0 % | | | | | |
| C the launch's funder (non-hub) | 588 | 40 % | 7,692 | 256 | 332 | 72 | 182 |
| D another known wallet | 7 | 0.5 % | 123 | 4 | 3 | 3 | 6 |
| E a deployer | 0 | 0 % | | | | | |
| F a hub | 179 | 12 % | 1,812 | 179 | 0 | 10 | 63 |
| G split | 0 | 0 % | | | | | |
| H recipient unknown at hop 1 (followed in D) | 385 | 26 % | 3,970 | 90 | 295 | 26 | 128 |
| H untraceable: cap reached before any transfer | 298 | 20 % | 10,717 (sale proceeds) | 258 | 40 | 116 | 102 |

Direct and multi-hop (`tables/D_return.md`): 1,260 of the 1,280 transfers end at hop 1, 10 at hop 2, 7 at
hop 3, 3 at hop 4. The sweep happens a median 152 s after the receipt of the tokens and 28 s after the last
sale before it. 62 distinct recipients take all 1,280 transfers, and only one event split its SOL between two
recipients.

## D. Capital return

Each of the 1,280 outgoing transfers (0.1 SOL or more) is followed to its first terminal (pre-registered H1-H6).

| first terminal | transfers | % | SOL | % SOL | events with one |
|---|---:|---:|---:|---:|---:|
| H1 the launch's funder | 631 | 49 % | 7,698 | 56 % | 590 of 1,161 (51 %) |
| H2 same cluster | 7 | 1 % | 123 | 1 % | 7 |
| H3 deployer network | 0 | 0 % | 0 | 0 % | 0 |
| H4 known wallet, other cluster | 0 | 0 % | 0 | 0 % | 0 |
| H5 hub | 300 | 23 % | 2,685 | 20 % | 249 |
| H6 unresolved | 342 | 27 % | 3,140 | 23 % | 322 |

- H6 breaks down as 304 transfers to wallets too active to reach the inflow in 3 pages of signatures, 35
  retained by an unknown wallet, and 3 cycles.
- 296 read events had no transfer before the reading stopped.
- Split: TRAIN H1 46 %, H5 41 %, H6 13 %; VALIDATION H1 53 %, H5 6 %, H6 41 %. The recipients changed between
  the periods; the shape of the transaction did not.
- Post hoc (`K_posthoc.md` section 3): 788 transfers (62 %, 9,168 SOL, 67 %) go to the launch's own funder
  whatever its hub status. 157 of them (1,470 SOL) go to funders that the plan's activity rule, 3,000
  transactions or more, classes as hubs (H5), mainly D6HE3knc. These are the launch's own funder, not an
  exchange. The recipient co-signs the sweep and pays its fee, which an exchange deposit address does not do.
- Return to cluster: H1 + H2 = 50 % of transfers. External destination: H4 is empty. Hub: 23 %. Unresolved:
  27 %.

## E. Exit-wallet recurrence

Exit wallets with two read events or more (`tables/E_recurrence.md`): the share whose events all share the
relation. The null permutes values among events, 1,000 permutations.

| relationship | observed | null mean [95 %] | p | ratio |
|---|---:|---|---:|---:|
| sniper → same exit wallet (always the same sniper, all corpus events) | 0.42 | 0.00002 [0, 0] | 0.001 | n/a |
| exit → same funder | 0.30 | 0.003 [0, 0.011] | 0.001 | x109 |
| exit → same cluster | 0.44 | 0.003 [0, 0.010] | 0.001 | x143 |
| exit → same deployer network | 0.00 | 0.001 [0, 0.003] | 1.0 | n/a |
| exit → same first SOL destination | 0.42 | 0.010 [0, 0.023] | 0.001 | x41 |
| exit → same collection (terminal) wallet | 0.36 | 0.022 [0.005, 0.041] | 0.001 | x16 |
| exit → same hub | 0.60 | 0.17 [0.09, 0.26] | 0.001 | x3.5 |
| exit → same return category | 0.52 | 0.09 [0.07, 0.12] | 0.001 | x5.5 |

- The fixed-pair rate (42 %) is lower than the 81-91 % of the economic-mechanics study. That is selection: the
  score gave 3 points to wallets fed by two snipers or more, and the fan-out operators rotate exit wallets
  among their snipers.
- Null 5 (exit-wallet pairs together in two launches or more, degree-preserving rewiring): 4,130 observed
  against 17,700 under the null, so no excess. With up to 60 sampled exit wallets in one launch (VALIDATION
  median 18), this statistic counts launch size, not togetherness. No conclusion is drawn from it.
- Downstream, the exit wallet keeps its recipient: 77 % repeat their first destination at least once (null
  43 %).

## F. Capital recycling

Launch A → exit wallet → recipient → funding of a sniper in launch B (`tables/F_recycling.md`).

- 607 of 1,161 events with a transfer (52 %; null, path wallets exchanged among transfers: 29 % [28, 31]).
  Time from A to B: median 18 min (p25 15, p75 24, max 73). SOL on the transfer: median 7.9.
- Every link goes through a funding of B's snipers, and in 600 of the 607 the wallet that funds them is A's
  own funder (`K_posthoc.md` section 7). B has the same snipers in 100 % of cases, the same cluster
  in 100 %, the same exit wallet in 95 %, the same funder in 76 % and the same deployer network in 0 %.
- Chains among the sampled launches: 44 of two launches, 5 of three, 1 of five, 1 of six.
- Example (TRAIN): launch 3Swr5ygB, exit wallets 2oaCduxL, 79PgRQvY and 99eLxTAR sweep to 92hhkb9q, which
  funds the snipers of launch ungbn47J 12 min later; the same pattern repeats 16 min later into DMJr5qcP.
- By operator (post hoc): 12 of the 17 operators that return capital to the funder fund a later launch from
  it, against 1 of the 7 that send it elsewhere. The last week (W40) shows 0 % because the corpus ends: no
  later launch can be seen.

So the same capital does circulate through the same structure, with a new deployer each time.

## G. Deployer linkage (strict non-hub)

| | transfers | events |
|---|---:|---:|
| direct to the deployer network | 0 | 0 |
| indirect (hops 2-5) | 0 | 0 |
| null-compatible (another cluster's network) | 0 observed, 0 under the null | |
| unresolved (H6) | 342 | 315 |

No path touches a deployer or a deployer's funder. The test has no power: no path, real or permuted, reaches
any deployer network. Paths stop at the first known wallet, which is usually the funder, so payments from the
funder to a deployer lie beyond the terminal. The economic-mechanics study found deployers funded from the
snipers' own network in 26 % of launches; this study neither confirms nor contradicts that.

## H. Hypothesis comparison

| observation | value | A one unit | B execution service | C independent traders |
|---|---|---|---|---|
| sweep co-signed by the exit wallet and its recipient, through one-time keys | 1,280 of 1,280 | fits | fits, if the service holds client keys | does not fit |
| SOL goes back to the launch's own funder | 17 of 24 operators | fits | fits, if the funder is the service's wallet | does not fit |
| routing fixed within an operator, never mixed | 24 of 24 | fits | fits, one route per client | weak |
| one shape of transaction across all operators | 24 of 24 | fits | fits, one tool | does not fit |
| one recipient wallet shared by two operators | D6HE3knc | fits | fits | does not fit |
| 7 operators sweep to separate collectors outside the corpus | 7 of 24 | possible, a second treasury | fits, client withdrawals | possible |
| capital funds the same snipers again, new deployer | 52 % of events, 12 operators | fits | fits, the service re-funds | does not fit |
| capital reaches the deployer network | 0 | not observed | not observed | not observed |

**Independent traders (C) is not supported:** every sweep is co-signed by the receiving wallet. **One unit (A)
and an execution service holding its clients' keys (B) cannot be distinguished** with these data. Both
predict co-signed sweeps, fixed routes and refunding of the same snipers. What would separate them is where
the capital goes after the 42 funders and the 20 other recipients: to one owner, or to several. That is not
collected here.

## I. Robustness and nulls

Pre-registered classification (`tables/I_robustness.md`, 1,000 permutations, p 0.001 = the smallest
possible):

| mechanism | full | without dominant operator | without top 10 wallets | TRAIN | VALIDATION | class |
|---|---|---|---|---|---|---|
| capital reaches the launch's funder (events) | 0.51 vs 0.03 | 0.51 vs 0.04 | 0.49 vs 0.03 | 0.49 vs 0.02 | 0.53 vs 0.08 | ROBUST |
| transfers ending in H1 | 0.49 vs 0.02 | 0.50 vs 0.04 | 0.47 vs 0.03 | 0.46 vs 0.01 | 0.53 vs 0.08 | ROBUST |
| same first destination repeated | 0.77 vs 0.43 | 0.82 vs 0.45 | 0.80 vs 0.45 | 0.56 vs 0.38 | 1.00 vs 0.88 | ROBUST |
| same terminal wallet | 0.36 vs 0.02 | 0.37 vs 0.03 | 0.38 vs 0.02 | 0.36 vs 0.04 | 0.36 vs 0.06 | ROBUST |
| same return category | 0.52 vs 0.09 | 0.47 vs 0.12 | 0.50 vs 0.09 | 0.75 vs 0.15 | 0.27 vs 0.06 | ROBUST |
| same funder | 0.30 vs 0.003 | 0.34 vs 0.0002 | 0.31 vs 0.003 | 0.10 vs 0.004 | 0.50 vs 0.001 | ROBUST |
| same cluster | 0.44 vs 0.003 | 0.64 vs 0.01 | 0.46 vs 0.003 | 0.38 vs 0.009 | 0.53 vs 0.001 | ROBUST |
| capital funds a later launch | 0.52 vs 0.29 | 0.46 vs 0.27 | 0.51 vs 0.29 | 0.62 vs 0.36 | 0.44 vs 0.27 | ROBUST |
| fixed sniper-to-exit-wallet pairs | 0.42 vs 0 | 0.36 vs 0 | 0.43 vs 0 | 0.36 vs 0 | 0.41 vs 0 | ROBUST |
| transfers ending in H2 | 0.005 vs 0.008 | | | | | NULL-COMPATIBLE |
| transfers ending in H3 / deployer network | 0 vs 0 | | | | | NULL-COMPATIBLE (no power) |

Known non-hub: funder return 0.64 vs 0.04. Strict non-hub: only 51 events keep a transfer, because most
terminals have no measured hub status; funder return there is 0.53 vs 0.10.

**These p-values overstate the evidence.** The nulls permute among events of all operators, but inside an
operator the behaviour is all or nothing. Within-operator rows read 0 or 1 with degenerate nulls, and the
VALIDATION events come from 31 launches only (median 18 events per launch). The unit that carries the
information is the operator (`K_posthoc.md` section 4):

- 24 operators have transfers. 17 send 80 % or more to the launch's funder, 11 of them seen in TRAIN only, 5 in
  VALIDATION only and 1 in both. 7 send 20 % or less, 3 in TRAIN only and 4 in VALIDATION only. None is in
  between. Both modes exist in both periods.
- Where an operator rotates its funders, its capital still goes back to that launch's own funder, not to just
  any funder of the operator. Operator k:21.13 (23 distinct recipients) reaches 0.48 under the strict H1 rule
  against 0.03 under the within-operator null; operator HxYy reaches 1.00 against 0.25. This is the one within-operator test with
  power, and it holds.
- Time (ISO weeks): the funder-return rate swings from 15 % (W37) to 100 % (W39) with the mix of operators
  active that week. The mechanism of each operator does not change; the population does.

Departures from the plan, all reported:

1. The first collection pass took the first System transfer as the recipient of a SOL transfer. Section 4 of
   the plan says the account with the largest lamport gain. The 4-signer sweep routes through a one-time
   address, so all 1,280 transfers first looked "retained by an unknown wallet". The code was brought back to
   the plan (commit aa4502a); the 1,280 calls spent on those one-time addresses are counted above.
2. 11 calls of a smoke test are not in the call counter.
3. The selection score lowers the fixed-pair rate (section E).
4. Null 5 measures launch size here (section E).
5. The hub rule, which is about activity, classes very active funders as hubs (section D).
6. The 10-transaction cap stopped 361 readings in the middle of selling.
7. Recycling is right-censored at the end of the corpus.
8. Integrity: one failure, a token balance that differs from receipt plus changes in one event. It is reported,
   not repaired. Every other check passed: unique signatures, well-formed addresses, recipient gain equal to
   the wallet's loss, times in order, no transfer counted twice, no measured hub kept private, no role used
   before it is visible, no transaction outside its window, no price file opened.

## J. Behavioural fingerprint

Clusters with 10 read events or more (`tables/J_fingerprint.md`). No intent is attached.

- **Common to all.** 22-25 SOL per sniper, funded 3-24 minutes before creation (cluster medians), 4 snipers per launch. The exit
  wallets sell on PumpSwap within minutes. The sweep is co-signed through a one-time address, and the deployer
  network never appears downstream.
- **Funder-return, fixed pairs** (e.g. W:2b6Yfh: 15 launches, 34 exit wallets, always the same sniper). SOL
  goes 100 % to the funder, the funder is the same in 88 % of cases, and 93 % of events fund a later launch.
  Cadence: one launch every 18-48 minutes.
- **Funder-return, fan-out** (e.g. W:vF9GBS, W:8E2rmK, W:DjJMVM). Each sniper splits its tokens over 7-15
  exit wallets that rotate among snipers. The funder changes every launch, yet the SOL goes 100 % to that
  launch's own funder, and 75-100 % of events fund a later launch.
- **Collector** (e.g. W:HdM8f1 with collector 3fzT6gaf, W:4qGFfh with 35Lopfe9, W:D1Kimk with 7934tgWT and
  EaPUR4G9). Same funding and buying. The SOL goes to one very active wallet outside the corpus: 80-100 %
  unresolved or hub. 0 % of events fund a later launch.

## WHAT THE BLOCKCHAIN PROVES

- In all 1,457 events, the exit wallet sold the tokens it received from the sniper on PumpSwap, paying the
  fee itself, a median 81 s after receipt. It passed none on.
- All 1,280 outgoing SOL transfers of 0.1 SOL or more are transactions signed by four keys: the exit wallet,
  the recipient (which pays the fee) and two addresses. The SOL passes through one of these, which has no
  other transaction in its history, before reaching the recipient through wrapped SOL. One signing process
  therefore had the authority of the exit wallet and of the recipient at the same moment.
- 788 of these transfers (9,168 SOL) went to the very wallet that had funded the snipers of the same launch.
  In 600 events, that same wallet then funded the same snipers for a later launch, a median 18 minutes after
  the first. The circuit funder → snipers → exit wallets → funder → snipers is a chain of observed transfers,
  closed for 17 of 24 operators.
- No observed path reaches a deployer or a deployer's funder.

## WHAT THE STRUCTURE STRONGLY SUGGESTS

- For most operators, the capital stays under the control of the funder's signing process from funding to
  refunding. The sniper and exit wallets are disposable stages of one loop, and the deployer is new each time.
- Each operator has one fixed route. The same transaction shape across all operators points to a common tool.
- The 7 collector operators run the same machinery but keep the proceeds in a separate, very active wallet,
  rather than in the funder.

## WHAT CANNOT YET BE DISTINGUISHED

- **A single economic actor**, holding every key, versus **an execution or bundling service** that holds its
  clients' keys and sweeps each client's proceeds back to that client's funder. Both give co-signed sweeps,
  fixed routes and refunding.
- **Multiple clients of one tool** versus **one actor with many sub-accounts**. One shared recipient
  (D6HE3knc, two operators) and the uniform tool are compatible with both.
- **A deployer-controlled network**: not observed downstream, but paths stop at the funder, so it is neither
  shown nor excluded.
- **Other explanations for the 7 collectors**, such as a platform treasury, an exchange-facing hot wallet or a
  second treasury of the same actor. Their activity (more than 3,000 transactions after the inflow) blocks the
  reading within this budget.
- **Who owns or controls any key, and with what intent.** This is not observable on-chain.

## NEXT MOST INFORMATIVE TEST

Follow the capital one step past the terminal: the outgoing SOL of the 42 funders and the 20 other
recipients, over the period of the corpus. If the capital of different operators converges into one wallet,
or a few, one economic unit or a shared treasury becomes the better reading. If it diverges into unrelated
wallets per operator, execution-service clients become the better reading. The test needs a pre-registered
protocol and budget. The 7 collectors alone hold thousands of transactions, so a reasonable estimate is 5,000
to 15,000 calls, to be fixed before collecting.

**Does the economic loop close?** For 17 of the 24 operators observed, yes. The SOL from the exit wallets'
sales is swept, in a transaction the recipient co-signs, back to the wallet that funded that launch's snipers,
and that wallet funds the same snipers again about 18 minutes later. For the other 7, the swept capital leaves
for wallets this study could not follow, and the loop is not seen to close.
