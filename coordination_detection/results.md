# Coordination detection: results

The question: at the launch, can the on-chain data tell a launch whose buying wallets act as a
coordinated group from one whose buyers look independent? No price outcome was computed.

**Les données montrent une structure de financement/achat coordonnée observable on-chain. Elles ne
permettent pas, à elles seules, d'établir l'intention des acteurs.** (The data show a coordinated
funding and buying structure observable on-chain. They do not, by themselves, establish the actors'
intent.)

In this corpus the coordination is not the exception, it is the rule: in about four launches out of
five, the snipers were funded by one wallet, in the same second, a few minutes before the launch.
Every dimension tested lies far outside what random redistributions of the same wallets, funders,
timings and tickets produce, in both periods, in every week, without the dominant operator and without
the dominant wallets.

Protocol as required: coverage (`coverage.md`), plan (`analysis_plan.md`), table built, frozen
(sha256 `eb710709...`) and checked (nine integrity checks), committed in `c9de496` before any
coordination rate; then TRAIN, VALIDATION once, the five null models (200 permutations each),
robustness, this report. No Helius call; the previous studies, the future TEST and the live
detector were not touched; nothing was pushed. Tables `C1` to `C8`.

## What this population already is

All 1,657 alerts are bundle snipes by the detector's own rule: at least 4 wallets buying 5 SOL or
more in the creation slot. Same-slot buying is therefore universal here and was not used to separate
anything; every comparison is made inside a population already selected for a coordinated-looking
pattern. How common coordination is among all pump.fun launches cannot be read from this corpus.

## Answers

**A. Is there statistically atypical on-chain coordination?** Yes, on four dimensions, against every
null model (p = 0.005, the smallest 200 permutations can give, in TRAIN and in VALIDATION):

| measure | TRAIN observed | null mean [95 %] | VALIDATION observed | null mean [95 %] |
|---|---:|---|---:|---|
| launches with 2+ snipers on one non-hub funder (N1 wallets shuffled) | 790 | 17.7 [9, 26] | 454 | 20.2 [11, 29] |
| the same, funders shuffled (N2) | 790 | 15.5 [8, 23] | 454 | 18.8 [10, 27] |
| launches with a funding cluster of 3+ snipers or a majority (N2) | 828 | 1.5 [0, 4] | 507 | 0.9 [0, 3] |
| mean spread of the snipers' last funding times, s (N3; lower = together) | 481 | 1,125 [1,114, 1,136] | 42 | 1,219 [1,179, 1,237] |
| sniper pairs seen together in 2+ launches (N5, degrees kept) | 664 | 44 [31, 59] | 368 | 36 [26, 48] |
| early buyers sharing a slot, mean share (N3) | 0.786 | 0.706 | 0.754 | 0.724 |
| launches with near-identical tickets (N4) | 637 | 426 | 352 | 244 |
| launches with identical tickets (N4) | 106 | 46 | 20 | 25 (p 0.88) |
| launches with 2+ round tickets (N4) | 3 | 6.6 (p 0.97) | 0 | 0.4 (p 1.0) |

Round tickets are rarer than chance, and identical tickets do not hold in VALIDATION: a round or
repeated amount is not, here, a mark of coordination.

**B. The most frequent structure:** one funding wallet sends the SOL to all the snipers (four in nine
launches out of ten) in one go, a median of about 3 minutes (187 and 191 s) before the buy; the
spread of their funding times is 0 to 1 s. In the funding graph: a funder shared by the snipers, not
linked to the deployer (56 % and 55 % of launches), or linked to it within two hops (architecture A,
26 % and 24 %); fully independent snipers 18 % and 21 %; a source behind several funders almost never
(under 1 %).

**C. How many launches show strong coordination?** Two of the four labels or more:
884 of 1,015 in TRAIN (87 %), 520 of 642 in VALIDATION (81 %); three or four of them: 787 and 446.
No shared structure at all: 28 (2.8 %) and 25 (3.9 %).

**D. Common funding:** 790 of 944 decidable launches (84 %) and 454 of 585 (78 %). This counts last
funders whose hub status was never measured. Keeping only funders known not to be hubs: 300 and 160
launches (null 9 and 7.5); genesis funders only: 238 and 137 (null 4.5 and 4.6), still p 0.005. The
unknown-status funders behave like an operator's own wallets: among the launches where one funder
serves two snipers or more, that funder appears in a single operator cluster in 85 % of cases and in
that launch alone in 44 %; the three funders seen across 20 launches or more and many operators are
known hubs, excluded.

**E. Abnormal synchronisation:** the snipers' funding times are tighter than the null for 923 of 939
(98 %) and 555 of 569 (98 %) launches. Among the early buyers, buys share a slot slightly more than
under the null (0.786 against 0.706, 0.754 against 0.724).

**F. Recurring wallet groups:** 472 launches (47 %) and 232 (36 %) have two snipers or more that had
already sniped together in an earlier alert; 416 and 234 wallets belong to a recurring pair.

**G. Do the same wallets reappear together?** Yes: 664 and 368 recurring pairs against 44 and 36
under the degree-preserving null. 499 and 292 launches have at least one sniper already seen as a
sniper before.

**H. Do the same funders reappear?** 318 and 276 launches have a non-hub funder already seen funding
snipers in an earlier alert. They stay with one operator: the funders that cross operators are hubs.

**I. Does the structure survive the permutations?** Yes for common funding, funding clusters,
funding synchrony, wallet reuse, near-identical tickets and early-buyer slot sharing; no for
identical tickets (VALIDATION) and round tickets.

**J. Is it independent of the number of snipers?** It is not redundant with it (the redundancy model
reaches ROC-AUC 0.64 to 0.79), but it lives in the 4-sniper launches, 91 % of the corpus: there,
84 % and 80 % share a funder and 98 % and 99 % were funded together; among the 5-sniper launches,
3 % and 10 % share a funder and 8 % and 5 % were funded together, while 58 % and 68 % still form a
funding cluster and 53 % and 22 % reuse wallets. The launches with no shared structure are mostly
5-sniper ones.

**K. Is it independent of the premium?** The labels never use the price, and a model of premium,
market cap, bundle size and grouped predicts none of the four with ROC-AUC 0.85 or more. The premium
of coordinated launches is a little higher (median 3.78 against 3.53 in TRAIN, 3.75 against 3.45 in
VALIDATION), and the premium follows the bundle's SOL mechanically (Spearman 0.33 and 0.59).

**L. Is it independent of one operator?** Yes. The largest operator cluster holds 11 to 28 % of each
label's launches; every label stays at p 0.005 without the dominant operator (214 and 106 launches),
among operators seen 5 times or more, among single-operator launches only, and without the 10 most
frequent sniper wallets. Wallet reuse is the operator clusters' own definition in part, and it is the
one label tied to "single" launches (kappa with grouped -0.36): grouped launches use fresh wallets.

**M. Can we speak objectively of COORDINATED ON-CHAIN ACTIVITY?** Yes, in the sense above: shared
funding wallets, funding in the same second, funding clusters and wallets reused together, each far
beyond what the same wallets, funders, timings and amounts produce when redistributed.

**N. What stays unproven about intent?** Everything. The chain shows that one wallet funds and
times the snipers; it does not show who controls that wallet, whether the snipers belong to one
person or to the clients of a bundling service, or what they meant to do. A single trader splitting
an order across wallets, a bundling tool, a market maker and a scheme to deceive later buyers can all
leave the same trace. The snipers' exits (below) are fast, but they are as fast where no structure
was found.

## Classification

| discovery | class |
|---|---|
| SHARED_FUNDER (two snipers or more on one non-hub funder) | ROBUST COORDINATION PATTERN |
| HIGH_SYNCHRONIZATION (snipers funded together) | ROBUST COORDINATION PATTERN |
| FUNDING_CLUSTER (largest funding component of 3+ snipers or a majority) | ROBUST COORDINATION PATTERN, nearly the same dimension as SHARED_FUNDER (phi 0.95) |
| RECURRING_WALLET_CLUSTER (snipers seen together before) | ROBUST COORDINATION PATTERN |
| early buyers sharing a slot | PROBABLE COORDINATION PATTERN: p 0.005 in both splits, a small effect, robustness not run |
| near-identical tickets | PROBABLE COORDINATION PATTERN: p 0.005 in both splits, robustness not run |
| identical tickets | RANDOM / NULL-COMPATIBLE (VALIDATION p 0.88) |
| round tickets | RANDOM / NULL-COMPATIBLE (rarer than chance) |
| NO_SHARED_STRUCTURE (the rare launches with none) | PRICE/STRUCTURE REDUNDANT (ROC-AUC 0.93; mostly 5-sniper launches) |
| early buyers' funding | INSUFFICIENT DATA (12.8 % observed) |

The four ROBUST labels meet the plan's rule: p below 0.01 in both splits, present in every week,
not redundant, holding without the dominant operator and without the dominant wallets.

## Secondary: what the groups do next (exits up to alert + 30 s)

Labels fixed before; descriptive only. Snipers exiting (sell or transfer out) within 30 s of the
alert: 73 to 91 % depending on the label, two snipers exiting in the same slot in 49 to 86 % of
launches, a median of 5 to 12 s after the buy. Recurring wallet groups exit most and most together
(88 % and 91 %; same slot in 68 % and 86 %). Launches with no shared structure exit nearly as fast
(77 to 80 %). After alert + 30 s nothing was observed.

## Limits

- The population is selected by the detector for bundle snipes; the prevalence figures describe it,
  not pump.fun.
- The hub status of most last funders was never measured; the strict version (known non-hubs only)
  is given beside every shared-funding figure.
- Funders are known for the snipers and the deployer, not for the early buyers.
- Early-buyer slot sharing and ticket similarity were tested against their nulls only, not through
  the robustness grid.
- No price outcome was computed: whether coordination relates to what the token does afterwards is
  not part of this study.
