# Economic mechanics of coordinated groups: results

How the coordinated groups of `coordination_detection` operate, from funding to reuse on the next launch.
No price outcome defines any group, role, architecture or cluster; the groups are that study's frozen labels,
unchanged. Protocol: plan and table committed before any measure (`4d84e62`, table sha256 `e6b4fdd8...`,
prices in a separate file); TRAIN, VALIDATION, null models of 1,000 permutations; robustness; no RPC call; the
future TEST and the live detector untouched; nothing pushed. Tables `B` to `K` in `tables/`.

Four levels are kept apart below: **[fact]** what a transaction shows; **[abnormal]** a structure outside its
null model; **[role]** a behavioral label inferred from facts; **[hypothesis]** a claim about control or intent.

Groups: COORDINATED, launches with two of the four coordination labels or more (884 TRAIN, 520 VALIDATION);
CONTROL, one label or none (131, 122); STRICT CONTROL, none (28, 25).

## A. Executive summary

- **There is a repeatable economic structure.** [abnormal] A funder sends about 25 SOL to each of four sniper
  wallets in the same second, a median 3 minutes before the creation; the snipers buy 78 % of the supply in
  the creation slot; within seconds most of them move all their tokens to a wallet of their own; the SOL left
  goes back to the same funder, which funds the same snipers again a median 21 minutes later.
- **Dominant architecture:** a common funder not linked to the deployer (59 % of coordinated launches); a
  funder tied to the deployer in 27 to 28 %; the deployer funding the snipers itself in 1 to 2 %.
- **Capital flows are concentrated.** [fact] 91 to 92 % of coordinated launches have one funder for two
  snipers or more; one transaction funds several snipers in only 1 to 6 %: the funder sends separate
  transfers, in the same second, of nearly identical amounts.
- **Entries and exits are synchronized.** [abnormal] Funding spread 0 s (median); the snipers' first exits
  fall in one slot 65 to 78 % of the time against 4 to 7 % under the null; the sold fractions are alike.
- **Groups recur.** [abnormal] 651 sniper wallets come back (a median of 4 launches, up to 47), 1,014 sniper
  pairs recur, 176 clusters hold 1,513 launches; the deployer changes almost every time (1,645 deployers for
  1,657 launches).
- **Capital recycles.** [abnormal] Of the snipers seen again, 60 % (TRAIN) and 92 % (VALIDATION) send SOL back
  to the funder of their previous launch, and 63 % and 94 % are funded again by that same funder, against 2 to
  10 % under the null.
- **Each sniper has its own exit wallet.** [abnormal] The wallets receiving tokens from snipers in two launches
  or more are fed by the same sniper 81 to 91 % of the time, against under 1 % under the null.
- **The common economic actor hypothesis** is consistent with every observation and contradicted by none;
  independent traders are ruled out by the SOL loop. One trader, a team and an execution service run per
  client cannot be told apart from on-chain data, except that in 26 % of launches the deployer itself is funded
  from the snipers' own network.
- **Unproven:** who controls the wallets, whether the funder is one person, a team or a service's account,
  where the tokens moved to exit wallets are finally sold and to whom that SOL goes, and any intent.

## B. Role graph

Primary architecture per launch from the last funders before the buy (hubs never shared):

| group | split | launches | C deployer funds 2+ snipers | A funder tied to the deployer | D several funders | B common funder | E none | unresolved |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| COORDINATED | TRAIN | 884 | 22 (2 %) | 237 (27 %) | 7 (1 %) | 521 (59 %) | 72 (8 %) | 25 (3 %) |
| COORDINATED | VAL | 520 | 3 (1 %) | 146 (28 %) | 2 (0 %) | 305 (59 %) | 41 (8 %) | 23 (4 %) |
| CONTROL | TRAIN | 131 | 0 | 0 | 2 (2 %) | 0 | 78 (60 %) | 51 (39 %) |
| CONTROL | VAL | 122 | 0 | 0 | 0 | 0 | 72 (59 %) | 50 (41 %) |

Architecture A survives every sensitivity (383 launches from last funders, 359 from genesis funders, 359 with
known non-hub funders only). B falls from 826 to 80 when funders of unmeasured hub status are dropped: most B
funders were never measured, and in the coordination study they behaved as one operator's wallets (85 % seen
in one operator cluster only). `tables/B_roles.md` lays out one launch of each architecture, wallet by wallet.

Behavioral roles [role], each with its evidence (`tables/J_roles_hypotheses.md`):

| role | wallets | evidence |
|---|---:|---|
| deployer | 1,645 | signed the creation; 11 deployed twice or more |
| upstream funder (non-hub) | 1,053 | last SOL to 2+ snipers of one launch: 833 |
| sniper | 3,852 | 5 SOL or more in the creation slot |
| exit wallet | 5,710 | received a sniper's tokens by transfer; in 2+ launches: 1,737, nearly always from the same sniper |
| collection wallet | 124 | received SOL from 2+ returning snipers between launches |
| funding service | 9 | funded snipers of 3+ operator clusters; 7 of them are known hubs |
| recurring infrastructure wallet | 711 | the same wallet in 5+ launches in one role |

## C. Funding mechanics

Coordinated launches, median / Q25 / Q75 / Q90 (`tables/C_funding.md` for every group, minimum and maximum):

| measure | TRAIN | VALIDATION |
|---|---|---|
| SOL funded to the group | 95.9 / 91.3 / 100 / 100 | 96.0 / 91.5 / 100 / 100 |
| SOL per sniper wallet | 25.0 / 22.0 / 25.0 / 26.8 | 24.3 / 23.7 / 25.0 / 25.4 |
| spread of funding times, s | 0 / 0 / 0 / 1 | 0 / 0 / 0 / 1 |
| funding to buy, s | 165 / 4 / 358 / 579 | 185 / 9 / 416 / 790 |
| launches with one funder for 2+ snipers | 787 of 859 (92 %) | 454 of 497 (91 %) |
| one transaction funding 2+ snipers | 56 of 884 (6 %) | 7 of 520 (1 %) |
| the deployer funds a sniper | 22 (2 %) | 5 (1 %) |

Every coordinated sniper was funded within the hour before its buy, nearly all within 10 minutes; amounts are
near identical (median coefficient of variation about 0). Against the nulls (1,000 permutations): one funder for
2+ snipers 830 and 506 launches against 16 and 20 (x52, x25); funding spread 2.1 s and 31.6 s for the
coordinated launches against 527 s and 1,295 s; one transaction for several snipers 91 and 9 launches against
0.3 and 0.05. The control group's snipers are funded too, but by different senders or by hubs: 27 % of its
TRAIN launches have snipers paid in one transaction by a hub, an exchange batch that can carry many users.

## D. Capital lifecycle

Per coordinated sniper (TRAIN; VALIDATION in brackets):

- [fact] received a median 25 SOL, spent 20 SOL on the creation slot (85 % [86 %] of the funding);
- [fact] 75 % [79 %] moved tokens out by alert + 30 s; of those, 83 % [81 %] only by a token transfer to another
  wallet, 16 % [19 %] only by a sale; the first move came a median 11 s [7 s] after the buy, and 2,274 of 2,669
  [1,396 of 1,675] had moved 99 % of their tokens by then;
- [fact] a median 4.6 SOL [4.2 SOL] stayed on the sniper.
- [fact] between two launches (808 [398] snipers whose flows are complete): a median gap of 21 [18] minutes; SOL
  went out of 99 % [96 %] of them, to the first launch's funder in 60 % [92 %], to the next launch's funder in
  3 % [2 %], elsewhere in 36 % [5 %]; 63 % [94 %] were then funded by the same funder as before.
- [abnormal] proceeds back to the first funder: x37 [x12] the null; the same funder again: x13 [x13].

What is not observed: the sale of the tokens moved to exit wallets, its price, and where that SOL goes; any flow
after alert + 30 s for snipers that never snipe again in the corpus. No profit is computed.

## E. Supply control

[fact] The group holds a median 77.7 % [78.1 %] of the supply after the creation slot, its largest sniper 42 %
[43 %], token HHI among snipers 0.38, and it supplies 98.8 % of the creation slot's SOL. These are the
detector's selection rule (75 to 81 % of the supply), so the control group holds the same (78.3 % [77.8 %]).
What differs is timing: the control group's snipers have moved a median 64 % [100 %] of their tokens before
the alert, the coordinated ones 0 % [2 %].

### Price impact (read last, descriptive)

[fact, mechanical] The creation slot multiplies the bonding-curve price by a median 14.5 [13.9] (initial price
2.80e-8 SOL per token), and 99.6 % [99.5 %] of the log move from the initial price to P0 is done inside it: the
group does not enter an existing market, its own buying is the opening price. Inside the slot the order of
transactions is unknown, so the group's part is approximated by its 98.8 % share of the slot's SOL; an exact
attribution is not possible. Afterwards, the highest price within 10 s, 30 s, 60 s and 5 min of the creation is
1.06, 1.12, 1.18 and 1.34 times P0 for coordinated launches (1.15, 1.22, 1.31, 1.54 for the control group).

## F. Exit mechanics

| group | split | first move within 5 s / 10 s / 30 s of the buy | first moves in one slot (median share) | spread of first moves, slots (median) |
|---|---|---|---:|---:|
| COORDINATED | TRAIN | 25 % / 36 % / 69 % | 1 | 1 |
| COORDINATED | VAL | 35 % / 45 % / 75 % | 1 | 0 |
| CONTROL | TRAIN | 43 % / 57 % / 79 % | 0.75 | 9 |
| CONTROL | VAL | 68 % / 73 % / 86 % | 0.80 | 2 |

[abnormal] First moves in one slot: 0.65 and 0.76 against 0.05 and 0.07 under the null (x14, x12); sold
fractions alike (coefficient of variation 0.05 and 0.09 against 0.18 and 0.21). Fast exits alone prove nothing:
the control group leaves even faster. What is beyond chance is the synchrony and the similarity of the moves.
Destination: tokens are not pooled (two snipers of one launch feeding one wallet: 12 and 2 launches, null
compatible); each sniper sends to its own exit wallet, the same one launch after launch. 60 s and 5 min after
the buy are censored.

## G. Cross-launch recurrence

- [fact] 651 of 3,852 sniper wallets snipe 2 launches or more (median 4, Q90 11, maximum 47), a median 23 minutes
  apart (Q25 17 min, Q75 40 min); 199 of 1,053 non-hub funders fund snipers in 2+ launches; 428 funder-to-sniper
  relations repeat; 1,014 sniper pairs recur, each behind a median of 4 different deployers.
- [abnormal] recurring pairs 664 and 368 against 44 and 37 under the degree-preserving null.
- [fact] Clusters built only from information at or before each launch: 320 hold a launch, 176 hold 2 or more
  (1,513 launches); a median of 4 launches per cluster (Q90 14); the largest, 279 launches, is 87 % the dominant
  operator; most clusters stay inside one operator cluster of the previous studies (median 1, Q90 3).
- [abnormal] In 26 % of multi-launch cluster launches (243 of 941, 147 of 572), the deployer was funded by a
  non-hub wallet of its own cluster's sniper network, against 0 when the network of another cluster is used.

### Behavioral fingerprints (the 35 clusters with 10 launches or more, `tables/G_recurrence.md`)

Two operating modes repeat, each stable inside its clusters:

| | mode B, the recycling loop | mode A, deployer-tied |
|---|---|---|
| architecture | common funder (61 to 100 % of a cluster's launches) | funder tied to the deployer (100 %) |
| funding before the buy | 1 to 8 min | 1 to 2 s |
| snipers moving tokens by alert + 30 s | 48 to 100 %, most above 85 % | 21 to 82 % |
| moves by token transfer | 72 to 100 % | 0 % |
| proceeds back to the first funder | most clusters near all (60 of 60, 68 of 68, 40 of 40), a few not (0 of 8) | not observed (snipers rarely return) |
| days between launches | 0.01 to 0.02 | 0.05 to 0.55 |
| operator clusters of the previous studies | mostly 1 or 2 | 1 to 15, mostly 5 or more |

Mode A spans many of the previous studies' operator clusters because its snipers are fresh each time; the
funders tie them together.

## H. Null-model results

1,000 permutations, observed against the null mean, empirical p (`tables/H_nulls.md`, `tables/K_extra.md`):

| mechanism | TRAIN | VALIDATION |
|---|---|---|
| one funder for 2+ snipers (launches) | 830 vs 15.9 (x52), p 0.001 | 506 vs 20.0 (x25), p 0.001 |
| one transaction for 2+ snipers (launches) | 91 vs 0.29, p 0.001 | 9 vs 0.05, p 0.001 |
| funding spread (s, lower = together) | 481 vs 1,124, p 0.001 | 42 vs 1,221, p 0.001 |
| first moves in one slot (share) | 0.65 vs 0.05, p 0.001 | 0.76 vs 0.07, p 0.001 |
| sold fractions alike (CV, lower = alike) | 0.050 vs 0.182, p 0.001 | 0.091 vs 0.207, p 0.001 |
| tokens pooled to one recipient (launches) | 12 vs 6.0, p 0.021 | 2 vs 3.8, p 0.90 |
| proceeds back to the first funder | 0.60 vs 0.016, p 0.001 | 0.92 vs 0.074, p 0.001 |
| funded again by the same funder | 0.63 vs 0.050, p 0.001 | 0.94 vs 0.071, p 0.001 |
| fixed sniper-to-exit-wallet pairs | 0.81 vs 0.004, p 0.001 | 0.83 vs 0.003, p 0.001 |
| recurring sniper pairs | 664 vs 44, p 0.001 | 368 vs 37, p 0.001 |
| deployer funded by its cluster's network | 243 vs 0, p 0.001 | 147 vs 0, p 0.001 |

## I. Robustness

Every mechanism above except token pooling keeps p 0.001 without the dominant operator (214 and 106 launches),
without the 10 most frequent sniper wallets, and, for common funding, with known non-hub funders only (289 vs
3.6; 157 vs 2.7) and with genesis funders only (243 vs 1.2; 137 vs 1.2). Inside the largest operator (320
launches) every mechanism holds; inside the three next ones (38 to 40 launches), common funding and funding
synchrony hold and their snipers barely move tokens by alert + 30 s. The deployer linkage was tested against
its null on all launches only.

## J. Final classification

| mechanism | class |
|---|---|
| common funder for the group | ROBUST STRUCTURAL EVIDENCE |
| synchronized funding (same second, minutes before) | ROBUST STRUCTURAL EVIDENCE |
| one transaction funding several snipers (rare) | ROBUST STRUCTURAL EVIDENCE |
| exits in one slot | ROBUST STRUCTURAL EVIDENCE |
| similar exit sizes | ROBUST STRUCTURAL EVIDENCE |
| proceeds back to the first funder | ROBUST STRUCTURAL EVIDENCE |
| re-funding by the same funder | ROBUST STRUCTURAL EVIDENCE |
| fixed sniper-to-exit-wallet pairs | ROBUST STRUCTURAL EVIDENCE |
| recurring sniper pairs | ROBUST STRUCTURAL EVIDENCE |
| deployer funded from the snipers' network (26 %) | PROBABLE STRUCTURAL EVIDENCE (null p 0.001 in both splits; robustness not run) |
| tokens pooled to one recipient | NULL-COMPATIBLE |
| supply held (78 %) and the opening price set by the group | observable fact fixed by the detector's selection; no null applies |
| final sale of the tokens, its price and the destination of that SOL | INSUFFICIENT DATA |

### The one economic actor hypothesis

| observation | A independent traders | B one trader splitting an order | C coordinated group | D bundling or execution service | E deployer-controlled wallets |
|---|---|---|---|---|---|
| one funder, same second, same amounts | no | yes | yes | yes | yes |
| residual SOL back to that funder, then refunded | no | yes | yes | yes, if the funder is the client's account | yes |
| each sniper with its own reused exit wallet | no | yes | yes | yes | yes |
| funders confined to one operator; 9 cross-operator funders, 7 of them hubs | n/a | yes | yes | against one shared service; fits one per client | yes |
| a fresh deployer nearly every launch, sniper pairs behind 4 deployers | n/a | yes, if it rotates deployers | yes | yes, the deployers being clients | only where linked |
| deployer funded from the snipers' network in 26 % | no | yes | yes | against, for that 26 % | yes, for that 26 % |

Independent traders (A) are ruled out by the SOL loop and the dedicated exit wallets. B, C and per-client D
leave the same trace and are not separated by on-chain data; E holds for the 26 % where the deployer is funded
from the snipers' network, and is not observable elsewhere. No winner is named among B, C and D.

## WHAT THE BLOCKCHAIN PROVES

- In 91 to 92 % of the coordinated launches, one wallet sent the SOL to two snipers or more, usually about 25 SOL
  each, in the same second, a median 3 minutes before the creation.
- The snipers bought about 78 % of the supply in the creation slot and their buying set the opening price.
- Within 30 seconds of the alert, most snipers moved their tokens out, mostly by transferring them to another
  wallet, and kept about 4 SOL.
- The same sniper wallets came back on later launches, a median 23 minutes apart, behind different deployers;
  before coming back, most sent SOL to their previous funder and received SOL from it again.
- The wallets receiving a sniper's tokens are, launch after launch, mostly the same wallet for the same sniper.

## WHAT THE BLOCKCHAIN STRONGLY SUGGESTS

- These are not independent buyers: funding, timing, exits, the return of SOL to the funder and the fixed
  exit wallets are each far outside their null models, in both periods, without the dominant operator and
  without the dominant wallets.
- The groups run a repeatable operating loop, a treasury-like funder, a fleet of sniper wallets each paired
  with an exit wallet, and a fresh deployer per launch, in two stable modes: a fast recycling loop (common
  funder minutes before, tokens transferred out within seconds, SOL returned, a new launch every 15 to 30
  minutes) and a deployer-tied mode (funding a second before, tokens held longer).
- In a quarter of the launches the deployer belongs to the same funding network as the snipers.

## WHAT REMAINS UNKNOWN

- Who controls the funders, snipers, exit wallets and deployers, and whether a funder is one person, a team or
  a service's account for a client.
- Where and at what price the tokens moved to exit wallets are sold, and where that SOL ends.
- The hub status and the upstream of most funders, whose history before their first funding was never
  measured.
- What the actors intend. A trader splitting an order, a team and an execution service working for deployers
  can all leave this exact trace; nothing here establishes manipulation.

## NEXT MOST INFORMATIVE TEST

Follow the exit wallets forward. For a sample of the 1,737 exit wallets that recur across launches (300
wallets, about 2,000 RPC calls), read their transactions after they receive the tokens: where they sell, and
where the SOL from the sale goes. If it reaches the same funder as the snipers' leftover SOL, buy, exit and
treasury are one economic unit (B, C or E); if it scatters to unrelated wallets per deployer, it points to an
execution service working for clients (D). This is the observation that separates the hypotheses this study
leaves tied, and it needs the owner's go-ahead before any call is made.
