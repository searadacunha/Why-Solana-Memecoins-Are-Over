# Funder network and final capital destination: results

Protocol: [analysis_plan.md](analysis_plan.md), scope B chosen by Benjamin after the call estimate, committed with
the collector (b87f571) before any flow was read. Frozen table: `derived/fn_table.json.gz`, sha256 `1a6cec6a...`
(`derived/FN_FREEZE.json`); integrity report `derived/FN_INTEGRITY.json`. Tables B to J are the pre-registered
analysis; `tables/K_posthoc.md` holds the checks added after reading them, descriptive and marked post hoc below.
No price, multiple, migration or profit is used, and no price file was opened (an audit hook refuses it).
Nothing dated at or after the start of the future TEST (2026-09-29 11:23 UTC) was read.

Data:
- Population: 62 primary wallets, the recipients of the exit-wallet sweeps (42 H1 funders, 20 collectors with 3
  in both, and 3 launch funders classified as hubs). They belong to 24 operators.
- Activity: 38 are short-lived (whole history under 1,000 transactions) and 24 very active (40,000 to 140,000
  transactions a day).
- Collected: 55 upstream chains, 408 downstream branches carrying 31,693 SOL at hop 1, and 1,058 transactions
  read.
- Calls: 3,553 Helius calls including the 62 of the probe, 0 failures, under the 6,062 cap. The live detector
  logged no confirmation failure and no freeze during the run.
- The very active wallets are sampled, not censused. For the short-lived wallets, only the last 10 transactions
  of the median 521 that follow their last sweep were read. Every result below is bounded by this.

## A. Executive summary

- **Where funder capital goes.** 64 % of the SOL the 62 wallets send out goes straight to very active wallets
  (more than 3,000 earlier transactions, the plan's "hub"). 32 % goes to wallets never seen in the corpus, and
  under 1 % goes back to snipers or deployers.
- **These are not exchange deposits.** In 408 of 408 outgoing transfers, the receiving wallet signs the
  transaction. It is the same four-signer sweep tool as in the exit study: the recipient must sign so that the
  tool can close its wrapped-SOL account. An exchange deposit address does not co-sign a third party's
  transaction.
- **Convergence is partial.** Under the plan's rule (hubs never link operators), 16 non-hub wallets are reached
  from two operators or more. The operators form two groups, one of 7 and one of 5, and 12 operators are
  connected to no other.
- **Below chance.** That sharing is lower than random rewiring with the same structure would give: 16 shared
  wallets against 25 to 28 under nulls A, B and C, and a largest group of 7 operators against 17. The operator
  networks are mostly separate, with a few bridges.
- **Capital moves from one operator to another, in order.** There are 13 ordered sequences through 8 bridge
  wallets (SOL in from one operator's path, later out to another operator's wallet). In the clearest one, the
  funder of c:Gug21 sends 682.5 SOL to DRUKt6L9, which 24 h later creates the funder of c:8uM3 with 160 SOL.
  One bridge, AyBdrsDJ, pools SOL coming from two operators.
- **Recycling stays inside the operator.** 115 of 119 indirect recycling links go back to the same operator's
  snipers (97 %, null 13 %), a median 10 minutes later. 3 go to another operator, 1 to a deployer.
- **A treasury per operator.** 12 very active wallets both create funders and receive their proceeds. 6 of them
  serve a single operator (for example 2DEEdv8H for c:9FJv: 4 funders created, 7,032 SOL received). The loop
  closes one level above the funder.
- **Deployers: almost nothing.** 3 paths touch a deployer network, carrying 6 SOL downstream.
- **Unresolved.** 13 % of the downstream SOL; the 7 very active wallets whose history is too long to reach
  their creation; the bulk of the short-lived wallets' transactions; and who holds the keys.
- **One network or a service?** If the co-signing very active wallets are allowed to link operators (post hoc),
  14 of 24 operators join one component, and no single wallet holds it together. One economic network and a
  key-holding execution service both predict that. Independent traders do not.

## B. Funder → destination map

Upstream: who funded the primary wallets (`tables/B_map.md`).

| terminal class | chains | operators |
|---|---:|---:|
| A very active wallet ("hub") | 52 | 16 |
| D deployer network | 1 | 1 |
| E cross-operator network | 1 | 1 |
| G unresolved (more than 5 hops) | 1 | 1 |

- 7 very active primaries have 3,000 transactions or more before their first sweep, so their creation is out of
  reach.
- 36 primaries were created directly by 18 very active wallets. 4 of these wallets created primaries of two
  operators or more.
- 2 non-hub wallets did the same: 27NsskNe (three funders, k:21.13 and k:20.32) and DRUKt6L9 (c:8uM3 and
  k:21.59). Source: `K_posthoc.md` section 3.

Downstream: where their SOL goes, by first terminal.

| class | branches | SOL | % SOL | operators |
|---|---:|---:|---:|---:|
| A very active wallet ("hub") | 217 | 22,159 | 70 % | 15 |
| C operator-associated | 150 | 4,466 | 14 % | 11 |
| E cross-operator network | 13 | 712 | 2 % | 3 |
| F new wallet that keeps the SOL | 6 | 246 | 1 % | 4 |
| D deployer network | 2 | 6 | 0 % | 1 |
| G unresolved (13 too active, 4 beyond 5 hops, 3 circular) | 20 | 4,104 | 13 % | 7 |

The very active primaries were sampled at the 10 signatures before each of up to three sweeps. That sample
holds 425 sweeps received and 258 SOL transfers out, and no sniper funding and no trade. Around the sweeps,
these wallets act as routers.

## C. Cross-operator convergence

Pre-registered rule (`tables/C_convergence.md`):
- 286 non-hub wallets were reached on some path. 269 are reached from one operator only, 16 from two, and 1
  (DRUKt6L9) from three. All 16 shared wallets were unknown to the frozen corpus.
- Under the plan's strict definition, a capital transfer is a path that ends on a wallet tied only to other
  operators. There is 1 such transfer: 0.2 SOL, the creation of 8bE9UzHp (funder of k:20.20+19.92) by a wallet
  tied to k:21.13.
- Shared infrastructure already in the frozen data: D6HE3knc funds and receives for two operators.

The three relations, kept apart (`K_posthoc.md` sections 3 and 5):

| relation | what is observed |
|---|---|
| capital transfer, ordered | 13 sequences through 8 bridges, 6 directed operator pairs. c:Gug21 → c:8uM3: 682.5 SOL into DRUKt6L9, 160 SOL out to create 8uM3's funder 24 h later. c:Gug21 → k:21.59: 0.2 SOL, 48 h. c:Fb2T → k:21.59: five fresh wallets each receive 4.0 SOL from the c:Fb2T collector, then send 1.5 to 3.2 SOL to k:21.59's funder 5 h later (W40). k:20.68 → k:20.32: 10 SOL into AyBdrsDJ through two intermediaries, then 180.5 SOL out to k:20.32's funder 0.4 h later. k:20.68 → k:21.13: the same bridge pays 389.4 SOL a week later. k:20.20 → k:21.13: 2.5 then 2.6 SOL. |
| capital pooling | AyBdrsDJ takes 287.9 and 389.5 SOL from two k:21.13 wallets and 10 SOL from k:20.68's path, then pays k:20.32's and k:21.13's funders. 27NsskNe takes 1,289 and 988 SOL from two k:21.13 wallets (one operator only) and, in W34-W35, created funders of k:21.13 and k:20.32. |
| shared infrastructure without a shown transfer | 27NsskNe creating funders of two operators (its creation of k:20.32's funder came before the inflows). D6HE3knc. Five fresh W40 wallets funded by both c:Fb2T and k:21.59. |
| common terminal | 8zHcWujH, reached at hop 4-5 by k:20.68 and c:2YKa paths. |

SOL is fungible. An ordered sequence shows that capital entered a bridge from one operator's side and left it
toward another operator's wallet. It does not show that the same lamports moved.

## D. Network components

Plan's rule (`tables/D_components.md`, `K_posthoc.md` section 4):
- **7 operators:** k:21.13, k:20.32, k:20.68, k:20.20+20.18, c:HxYy, c:2YKa, c:9TN2. 452 sweeps, weeks W34-W38.
- **5 operators:** c:Gug21, c:8uM3, k:21.59, c:Fb2T, c:5MSp. 451 sweeps, weeks W38-W40.
- **12 operators alone,** including k:20.80 (154 sweeps) and k:22.04 (135).
- At the level of primary wallets: 39 components, 4 with two primaries or more, 3 spanning two operators.

Post hoc (`K_posthoc.md` section 2):

| hubs | components | largest when any one hub is removed |
|---|---|---:|
| never link operators (the plan) | 7, 5, 12 x 1 | 7 (6 without H9tyeSef) |
| link only through a direct transfer they co-signed as recipient | 14, 10 x 1 | 13-14 |
| all hubs link (includes hubs that only funded wallets, as an exchange withdrawal would) | 18, 6 x 1 | 17-18 |

The middle line is the informative one. A hub that co-signed a receipt is not a passive deposit address.
106 hubs received a co-signed transfer, and 16 of them received from two operators or more.

## E. Capital recycling

| direct destination of a primary's outgoing SOL | transfers | SOL |
|---|---:|---:|
| very active wallet ("hub") | 153 | 20,320 |
| previously unseen wallet | 242 | 10,106 |
| sniper, same operator | 8 | 184 |
| sniper, another operator | 0 | 0 |
| deployer network | 2 | 6 |
| other known wallet | 2 | 1,077 |
| exit wallet | 1 | 0.4 |

Indirect recycling (a wallet on a downstream path later funds a frozen launch), 119 links:

| relation | links | SOL | median delay |
|---|---:|---:|---:|
| same operator's snipers | 115 | 6,587 | 10 min |
| another operator's snipers | 3 | 120 | 28 h |
| deployer funding | 1 | 1 | 6 days |

- 111 of the 119 links run through another of the 62 primary wallets.
- Null D draws the recipient launch from the same ISO week. Same-operator share 0.97 against 0.13 under the null
  (p 0.001): recycling follows the operator.
- The brief's strongest pattern (operator A → funder A → shared network → operator B) is observed. It is rare
  (the sequences of section C plus 3 recycling links). It repeats only within a single day (five times
  c:Fb2T → k:21.59 in W40); no pair recurs across weeks.

## F. Deployer relationships (strict non-hub)

| | paths | primary wallets |
|---|---:|---:|
| direct (hop 1) | 3 | 3 |
| indirect (hops 2-5) | 0 | 0 |
| own operator's deployer network | 2 | 2 |
| another operator's deployer network | 1 | 1 |
| with a measured non-hub status | 0 | 0 |

These carry 6.2 SOL downstream, plus one upstream creation. No test has power at this count. Capital reaching
deployer networks is negligible in what was read.

## G. Terminal destinations

Downstream SOL by class (`tables/G_terminals.md`):

| unit | A hub | D deployer | E cross-operator | C same operator | B other operator | F new, keeps | G unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|
| all, 31,693 SOL | 70 % | 0 % | 2 % | 14 % | 0 % | 1 % | 13 % |

- 14 of the 22 operators with downstream branches send 99 % or more of their SOL to one class, so the result is
  binary by operator.
- 8 of them send it to very active wallets: c:9FJv, c:YSUc, c:Fb2T, c:5MSp, c:9TN2, k:22.04, k:21.39 and
  k:22.02.
- 4 send it to their own operator's wallets, and 2 have it all unresolved.
- The largest operator, k:21.13 (15,826 SOL), splits: 51 % to very active wallets, 25 % to its own wallets,
  24 % unresolved.

## H. Nulls and robustness

`tables/H_nulls_robustness.md`, 1,000 permutations. A small p would mean more sharing than chance.

| subset | primaries | shared wallets | null A | null B | null C | largest group | null A |
|---|---:|---:|---|---|---|---:|---|
| full | 62 | 16 | 24.7 [22, 27], p 1.0 | 28.2 [19, 43], p 1.0 | 24.8 [22, 27], p 1.0 | 7 | 16.7 [14, 19], p 1.0 |
| without k:21.13 | 39 | 8 | 13.2, p 1.0 | 13.2, p 0.99 | 13.2, p 1.0 | 5 | 12.1, p 1.0 |
| without the 10 largest primaries | 52 | 9 | 17.2, p 1.0 | 16.7, p 0.99 | 17.2, p 1.0 | 6 | 9.7, p 1.0 |
| known non-hub | 62 | 4 | 13.6, p 1.0 | 16.6, p 1.0 | 13.5, p 1.0 | 6 | 11.7, p 1.0 |
| strict non-hub | 62 | 15 | 24.1, p 1.0 | 27.1, p 1.0 | 24.0, p 1.0 | 7 | 16.4, p 1.0 |
| TRAIN | 52 | 7 | 15.7, p 1.0 | 19.4, p 1.0 | 15.6, p 1.0 | 6 | 9.5, p 1.0 |
| VALIDATION | 10 | 7 | 7.0, p 1.0 | 7.0, p 1.0 | 7.0, p 1.0 | 5 | 6.9, p 0.96 |

- Cross-operator sharing exists in every subset, including without the dominant operator and in both periods.
  It is always below what random wiring with the same degrees would give. The bridges are specific, not a
  general mixing.
- Removing any one shared wallet leaves the largest group at 7 operators (6 without H9tyeSef). No single wallet
  carries it.
- The operator level is the principal layer: 24 operators, 14 binary in their terminals, 12 isolated under the
  plan's rule.
- **Time.** Every bridge is active one or two weeks:
  - TRAIN bridges (27NsskNe, AyBdrsDJ, H9tyeSef, the 7a2zhDAJ group, CrAtVXEZ) sit in W34-W37;
  - VALIDATION bridges (DRUKt6L9, CekCebfL, the five W40 wallets) sit in W38-W40.
- So the convergence is episodic, replicated in both periods but through different wallets each time, not one
  persistent hub.

## I. Behavioural network fingerprint

No intent and no owner are attached (`tables/I_fingerprint.md`).

**Group of 7 operators** (k:21.13 dominant, W34-W38; figures for its main component, 15 primaries of 6
operators, c:9TN2 joining through D6HE3knc):
- primaries created mostly by very active wallets;
- downstream: very active wallets 57, own operator 42, cross-operator 10, unresolved 16 branches;
- 47 of 128 branches recycle into a later launch;
- bridges pool and redistribute hundreds of SOL between k:21.13, k:20.68 and k:20.32 wallets;
- one funder (D6HE3knc) serves two operators.

**Group of 5 operators** (c:Gug21, c:8uM3, k:21.59, c:Fb2T, c:5MSp, W38-W40):
- 451 sweeps;
- two collectors (3fzT6gaf, 35Lopfe9) and three funders;
- created and fed by DRUKt6L9 and CekCebfL, which receive c:Gug21's capital;
- 0 of 53 branches recycle into a corpus launch, the corpus ending in W40;
- the five fresh wallets jointly funded by c:Fb2T and k:21.59 sit in W40.

**Isolated operators** (12):
- each its own circuit: one or two primaries, a very active wallet downstream;
- often a treasury that also created its funders: 2DEEdv8H for c:9FJv (7,032 SOL), C7ovdUck for c:YSUc
  (1,977 SOL); the same pattern exists inside the bridged groups (7KmKKVwm for k:20.68, 2,852 SOL);
- or SOL back to its own operator's wallets (k:20.80).

## J. Hypothesis comparison

| evidence | H1 one common network | H2 common execution infrastructure | H3 separate operator networks | H4 independent traders |
|---|---|---|---|---|
| recipient co-signs every step (1,280 sweeps, 408 outflows) | fits | fits | fits | does not fit |
| one sweep tool for all 24 operators | fits | fits | possible | does not fit |
| sharing below chance, 12 of 24 isolated (plan's rule) | against, as a whole | fits | fits | fits |
| recycling 97 % within the operator, null 13 % | against | fits | fits | does not fit |
| treasuries that create and receive for one operator | possible | fits | fits | does not fit |
| 13 ordered cross-operator sequences, 2 groups of 7 and 5 | fits locally | fits, the service moves capital | against, for these groups | does not fit |
| 14 of 24 joined through co-signing very active wallets (post hoc) | fits | fits | against, for these 14 | does not fit |

- **H4 is rejected by structure.** No step is a plain transfer between strangers.
- **H1 as one network over all operators is not supported.** Sharing stays below chance, recycling follows the
  operator, and 10 to 12 operators connect to nothing.
- **For the two bridged groups, and the 14 operators joined through co-signing wallets, H1 and H2 cannot be
  distinguished.** One actor holding all keys and a service holding its clients' keys produce the same
  co-signatures and the same occasional transfers.
- **H3 describes most operators most of the time:** each closes its own loop.

## WHAT THE BLOCKCHAIN PROVES

- The 62 wallets that receive the exit-wallet sweeps send 64 % of their outgoing SOL to very active wallets, and
  32 % to wallets never seen in the corpus. In all 408 outgoing transfers, the receiving wallet signed the
  transaction.
- 12 very active wallets both created primary wallets (genesis funding) and received SOL from them. 6 of those
  12 did so within a single operator.
- Specific wallets received SOL from one operator's wallets and later sent SOL to another operator's wallets: 13
  ordered sequences through 8 bridges. The largest: 682.5 SOL from c:Gug21's funder into DRUKt6L9, followed 24 h
  later by 160 SOL from DRUKt6L9 creating c:8uM3's funder. DRUKt6L9 also created k:21.59's funder. 27NsskNe and
  4 very active wallets created funders of two operators each, and D6HE3knc funds and receives for two
  operators.
- 115 of 119 recycling links bring capital back to the snipers of the same operator.

## WHAT THE NETWORK STRUCTURE STRONGLY SUGGESTS

- Most operators are separate circuits. Each recycles its own capital, often through its own very active
  treasury that creates its funders and collects its proceeds.
- A minority of operators are connected by bridge wallets that pool and redistribute capital between them, in
  two groups that do not overlap in time (W34-W38 and W38-W40).
- The very active destinations are not exchange deposit addresses: they co-sign their receipts. The same signing
  process, or the same custodian of keys, reaches across at least 14 of the 24 operators.

## WHAT REMAINS UNRESOLVED

- **Wallet ownership.** Co-signing shows shared signing authority at the moment of a transaction, not who holds
  a key.
- **Service and client relationships.** A bundling platform that keeps its users' keys would look like one
  network. Nothing here separates the platform from its users.
- **Ultimate beneficial ownership.** Where the very active wallets send capital next was not read. The scope did
  not allow it: they make tens of thousands of transactions a day.
- **Intent.** It is not observable.
- **Coverage.** 13 % of downstream SOL is unresolved. 7 very active primaries have no reachable creation. The
  short-lived wallets were read only at their ends, and the very active ones only around their sweeps.

## NEXT MOST INFORMATIVE TEST

Measure who else the 16 co-signing very active wallets shared by two operators sign for.

- If their co-signed receipts come almost only from this corpus's operator wallets, one network is the better
  reading.
- If they come from thousands of unrelated wallets, it is a platform serving many clients, and the operators
  are among them.

This needs a pre-registered sample of their co-signed receipts, around 50 per wallet. That is roughly 1,000 to
1,500 calls, depending on how many signature pages are needed to reach them; to be fixed before collecting.

**After the sniper → exit wallet → funder loop, do separate operator networks converge into a common capital
network?**
- **Not as a whole.** Most operators close their own loop, and they share fewer wallets than chance would
  produce.
- **Partly, through specific bridges.** Two groups of operators (7 and 5) exchange and pool capital through a
  few wallets, in order and in both periods.
- **Through co-signing wallets, wider.** The co-signing very active wallets link 14 of the 24 operators.
- **Not an identity.** These are shared signing authority and shared infrastructure, not a proven single
  owner.
