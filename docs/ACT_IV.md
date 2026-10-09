# Act IV — The Signal Still Exists. The Edge Doesn't.

> **Status: exploratory, not validated out of sample.** Everything new in this chapter (sections 3 to 12,
> the `alpha_patterns/` analyses) was computed on the 1,015 detector alerts of 21 August to
> 14 September 2026, the DISCOVERY and SELECTION blocks of `alpha_patterns/`, which is also the TRAIN
> block of the forensic studies (`post_detection_edge/` split its own TRAIN at 29 August, 325 alerts).
> The verdicts recalled in section 2 quote each earlier study's own hold-out block, read once there; for
> `post_detection_edge/` (TEST), `entry_zone/` and `known_group_reentry/` (VALIDATION) that block is
> 15 to 29 September 2026, 642 alerts. In `alpha_patterns/` the VALIDATION block was read once, for one
> pre-declared rule, which failed, and the OOS block was never read by this study (those alerts had
> served as the earlier studies' hold-out, which is why the plan calls any confirmation prospective).
> A separate, pre-registered confirmatory study on the same detector keeps its own TEST block unread
> and is not used here. Nothing below is a trading result; several things below are the absence of one.

Act III established that the public bonding curve of a successful pump.fun launch is now bought in
the creation slot by a coordinated group. This chapter asks the question that follows for anyone who
once traded Act I: **once that group is visible on chain, can what it reveals still be traded?**

Nine pre-registered studies and one systematic search later, the answer, within what was tested, is
no. The reason is more specific than "the edge is gone". The
chain still shows *who* is launching and *how*. It no longer shows, early enough, *whether the launch
will work*. The structural signal survived the change of mechanism. The predictive signal did not.

---

## 1. The data: a live detector, 1,657 alerts

The detector described in Act III ran live from 21 August 2026. It alerts when at least four wallets
each put 5 SOL or more into a token's bonding curve in the creation slot, 73 to 90 SOL in all, 75 to 81 %
of the supply (the rule as applied live, `post_detection_edge/results.md`). By the snapshot of
29 September 2026 11:23 UTC it had alerted on **1,657 launches**
(`post_detection_edge/data/SNAPSHOT.json`). Every launch in this chapter is therefore a bundle snipe
by construction: the population is the detector's, not pump.fun's.

Time was cut before any outcome was read, on alert counts alone (`alpha_patterns/PLAN.md`, §3):

| block | period (UTC) | alerts | with an observable 1 h outcome | role |
|---|---|---:|---:|---|
| DISCOVERY | 21 Aug → 7 Sep | 643 | 363 | everything exploratory below |
| SELECTION | 7 Sep → 15 Sep | 372 | 249 | everything exploratory below (read here from 6 October; an earlier, unpublished signal search had read it on 2 October) |
| VALIDATION | 15 Sep → 22 Sep | 292 | 232 | read once, for one pre-declared rule (§7) |
| OOS | 22 Sep → 29 Sep 11:23 | 350 | 295 | never read by this study |

An outcome is observable when the detector's 5 s price sampling was active, an entry price was read
between 5 and 15 s after the alert, and the following hour was recorded. **GOOD** means the price was
read at twice the entry price on two consecutive reads within that hour; **BAD** means it was not.
Over the 612 observable launches of DISCOVERY and SELECTION, 168 are GOOD: **27.5 %**
(`alpha_patterns/tables/team_absorption.json`, `population.Y2`). A ×3 happens in 9.6 % of launches (59 of 612), a
×5 in 2.3 % (14 of 612) (`alpha_patterns/tables/operator_forensics.json`, `population.base`). The trade attached to every test was declared in advance: buy at alert + 5 s, sell at ×2
on the next read, exit at 1 h otherwise, $500, the cost model of `post_detection_edge/code/trade.py`.
On the 363 DISCOVERY launches (base rate 25.1 %, 91 of 363) that trade loses 34.7 % per launch; it
breaks even at a precision of **45.8 %**, a lift of 1.83 over the DISCOVERY base rate (`alpha_patterns/tables/BILAN_2026-10-06.md`, §2). Every rule in this
chapter is measured against that bar.

---

## 2. The path: nine studies, then three mechanisms

The question was approached from the outside in. Each study was written as a plan before its rates
were computed and ended with a verdict; the studies that tested a signal read the alerts after
15 September as their hold-out, one after another, and the capital-flow studies (5 to 7) are
descriptive, with TRAIN and VALIDATION as two periods rather than a hold-out. The chain is
reproduced here because the order matters: each negative result sent the next study one layer deeper.

| # | study (directory) | question | verdict |
|---|---|---|---|
| 1 | `post_detection_edge/` | Does buying right after the alert still pay, and does anything at the alert separate the launches that will double? | **Statistical signal, no tradable edge.** Of 12 signals locked before the test, one survived on the TEST block (15 to 29 September, 642 alerts): a logistic score lifting P(×2 within 15 min) from 31.0 % to 45.7 % on 164 launches, net −23.3 % per trade on its declared strategy [−35.9, −12.0], −8.1 % [−21.7, +1.6] for the best pre-declared alternative. |
| 2 | `post_detection_forensics/` | Does the on-chain structure of the bundle (wallets, funding, tickets) separate the quick doublers beyond the entry price and the operator family? | **No robust on-chain separation.** |
| 3 | `entry_zone/` | Is there a market-cap or premium zone where a ×2 is clearly more likely? | **No robust zone.** Rules chosen on TRAIN fall back to the base on VALIDATION or hold only as the premium or one operator. |
| 4 | `sniper_capital/` | Does the share of capital a sniper risks say which launches double? | **No relation survives** once premium, operator and the number of snipers are known. |
| 5 | `coordination_detection/` | Independent of price: do the buying wallets act as a group? | **Coordinated on-chain activity in about four launches out of five.** |
| 6 | `economic_mechanics/` | How does the group operate? | **A repeatable loop**: one funder, four snipers funded in the same second about three minutes before launch, 78 % of the supply bought in the creation slot, tokens moved to a recurring exit wallet, SOL back to the funder, the same snipers funded again a median 21 minutes later. |
| 7 | `exit_destination/`, `funder_network/` | Where does the capital go? | **The loop closes for 17 of 24 operators**; the exit wallet sells a median 81 s after receiving the tokens; operators do not form one network, two groups are bridged. |
| 8 | `known_group_reentry/` | Is "this group is one we have seen" a live trading signal? | **No incremental signal.** In VALIDATION (alerts from 15 September, entry +5 s), known-group alerts reach +50 % within 15 min more often (61.2 % against 33.6 %), but matched on launch size and price the difference is not distinguishable from zero, and every strategy loses after costs (−17.3 % per trade on known groups). |
| 9 | `alpha_patterns/` (this chapter) | A systematic search over 415 features, then three mechanism studies: the teams, their rhythm, the absorption of their inventory. | **No exploitable pattern found.** Details below. |

Studies 1 to 8 are each a directory with `README.md`, a plan (`analysis_plan.md`; `methodology.md` and
`tables/LOCK.json` for study 1) and `results.md`. Study 9 is
`alpha_patterns/`, whose front page lists what was published and what was not.

---

## 3. The mechanical search, and why it had to stop

`alpha_patterns/` began as what its name says: a rule search. From 415 features cut at the alert
(the funding of the snipers, the shape of the bundle, the external buyers already present, the
creator, the operator's history, the time of day, the entry premium), 3,100 atoms were formed and
every single atom, every allowed pair of atoms from different families, and the triples grown from the
300 best passing pairs were evaluated on DISCOVERY against the ×2 label: **3,237,943 rules** (3,100
singles, 3,103,093 pairs, 131,750 triples; `alpha_patterns/tables/discovery_summary.json`, `Y2.evaluated`).
37,296 passed the DISCOVERY screen. On the same features with the outcomes shuffled at random,
26,655 passed (`alpha_patterns/tables/BILAN_2026-10-06.md`, §1). The best DISCOVERY precision, 72 % on 25 launches, is what
the shuffled outcomes also produce. DISCOVERY generates; it does not judge.

The chain was then calibrated on synthetic outcomes before any hold-out block was read
(`alpha_patterns/code/ctl_00_controls.py`, `alpha_patterns/controles/ctl_00_controls.log`): a planted rule at three
times the base rate on 8 to 15 % of the alerts survives the full chain in 16 of 24 worlds; at 2.2 times,
in 3 of 24; at the break-even lift of 1.83, in 1 of 24. A negative result from this search therefore
excludes only large effects. Rather than freeze ten mechanical candidates per target, the author
pre-declared a single rule, SWARM + CHEAP ENTRY (at least 30 external wallets already in by alert − 10 s,
entry premium in the cheapest tercile): a hypothesis born from DISCOVERY, its swarm half from the
autopsy of D1 below and its cheap-entry half from an earlier robustness read, and declared as such in
`alpha_patterns/tables/validation.json`. He froze it (`alpha_patterns/SELECTION_FREEZE.json`) and read
VALIDATION once (§7).

Before that, a library of 32 composite patterns written in advance (demand, organic relay, buying
sequences, coordination, wash trading, funding, creator, bundle geometry, scripts) was scored on
DISCOVERY only. None reached the break-even precision; the best, D1, made 16 of 40 (40 %, lift 1.60)
at a net of −12 % per trade, and its autopsy showed it measured the size and earliness of the swarm of
recurring bots, not a funding structure (`alpha_patterns/tables/BREAK_THE_LOOP_2026-10-06.md`). Most of the
"wash trading" filters pointed the wrong way: launches with more pre-alert wash volume or round trips
doubled more often, not less (E1 17 of 49, E2 23 of 63, against a base of 25.1 %); only the
repeated-sizes filter E3 went the expected way (13 of 70). The search over properties of the launch was going in circles; the three studies
below look at the actors instead.

The test registry of `alpha_patterns/` (`alpha_patterns/registre/tests.jsonl`, chained) counts **31,656,419
comparisons on real data** across this search and the studies before it on the same alerts. The
Bonferroni threshold on that count is 1.6 × 10⁻⁹. No p-value in this chapter approaches it; the
q-values quoted below are Benjamini–Hochberg corrections inside pre-registered families, which is the
honest unit, not a global one.

---

## 4. The teams: identity exists

`alpha_patterns/tables/BUNDLE_OPERATOR_FORENSICS_2026-10-06.md`, pre-registered in
`alpha_patterns/tables/OPERATOR_FORENSICS_PREREG_2026-10-07.md`, figures in `alpha_patterns/tables/operator_forensics.json`.

Across the 1,015 launches, 2,189 distinct sniper wallets appear; 1,767 of them (81 %) are used once.
Launches were linked by shared sniper wallets, by a shared dominant funder, by an identical ticket
configuration and by a shared creator, then merged into connected components. The links confirm each
other far above chance: two launches sharing a sniper wallet also share a funder 30.0 % of the time
against 0.17 % for two launches of the same week, and a configuration 36.5 % against 0.71 %; the
corroboration runs from 47 to 212 times the baseline across the link types (the report rounds this to
45 to 220; `alpha_patterns/tables/operator_forensics.json`, `groupings.corroboration`). Wallets, funders and
configurations are three faces of the same identities. (A shared funder two hops back does not corroborate the wallets or the funders, below chance on
both, and follows only the configuration; a coarse ticket signature fuses 39 % of the launches into one
group. Both were rejected: they describe a shared tool, not a team.)

The union identity gives **188 groups**; 33 have at least five launches with an observable outcome
(456 launches), 19 have at least ten (368 launches), 3 have at least twenty
(`alpha_patterns/tables/operator_forensics.json`, `groupings.stats.U`). The 45 groups with five or more launches cover 764 of the 1,015; three operating modes account
for 708 of them and the remaining 56 are mixed:

| mode | groups | launches | median active life | ×2 rate |
|---|---:|---:|---|---:|
| fixed team: a fixed set of wallets reused from one launch to the next (four wallets in 14 of the 22 groups) | 22 | 271 | 1 day | 28 % |
| fixed script, fresh wallets every time, one or two configurations | 19 | 213 | 3 days | 26 % |
| one diffuse population: 311 wallets, 60 funders, 112 configurations, chained by reuse | 1 | 224 | 18 days | 33 % |
| mixed | 3 | 56 | 7 days | 10 % |

So the actors are real and recognisable. Most "teams" are bursts of 5 to 23 launches (the larger ones 12 to 23) over one to
three days, then they disappear; the largest group (22 % of launches) is not a team but a population
of sniper wallets reused by several hands.

**Their ×2 rates differ, a little more than chance.** Among the 19 groups with ten or more observable
launches, rates run from 0 % to 58 %. A χ² of 41.4 on 18 degrees of freedom gives p = 0.0008 against
reshuffled outcomes, p = 0.0017 when the reshuffling is done within the calendar day, p = 0.0012
within day and entry-premium tercile (`heterogeneity.U.Y2.10`). The between-group standard deviation
of the true rates is about 13 points around 27 %. For the ×3 there is no heterogeneity at all
(p = 0.62, 0.44, 0.53). A mixed logistic model puts the group effect at 0.68 in logit against 0.43 for
the day: the operator weighs more than the day, on the ×2 only (`mixed_model`).

**But the same teams make GOOD and BAD, and their history does not say which comes next.**

- No sequence inside a group. Across the 19 groups with ten or more launches (349 consecutive pairs),
  P(×2 after a ×2) is 32.0 % and P(×2 after a failure) is 25.8 %; the gap is exactly what the
  heterogeneity between groups produces, and a permutation within each group gives p = 0.92
  (`sequences.U.Y2`). After two failures the next launch doubles 21.3 % of the time, against 34.0 %
  otherwise. There is no "one pump in three": the market-wide ×2 rate is one in 3.6, the ×3 one in 10.
- A group's past does not predict its next launch. With the group identity built chronologically (a
  launch becomes known 60 s after its alert, an outcome only once resolved, one hour later) and the
  prior rate shrunk toward the market, the gain in log-loss over the market rate with five or more
  antecedents is **−0.016 on DISCOVERY, +0.038 on SELECTION, +0.003 [−0.021, +0.046] on both**
  (`history_prediction.U`, `Y2_nprev5`). The AUC of the prior rate is 0.43, 0.66 and 0.56. It helps in
  one week and hurts in the two before it. The same inversion had already appeared in an earlier,
  unpublished history search of 2 October, not part of this repository, whose features held on that
  week and failed on 15 to 29 September (forensics report, §8).
- The high-confidence rule fixed in advance (ten or more antecedents and a 90 % Wilson lower bound of
  the group's rate above the market) fires 29 times and is right **3 times (10.3 %)**, against 44.1 %
  for the launches with a long history that it does not select (`history_prediction.U.ALL.Y2_HC1`).
  Its expected value at $500 is −55 % per trade.
- A regime change is visible in one of the three groups large enough to test: the fresh-wallet script
  g169 doubled 5 of 11, then 0 of 8, then 5 of 6 in three consecutive weeks (p = 0.006 within the group,
  uncorrected over the three; the other two are stable). A team can be good, then dead, then good again
  (`regimes.U.per_group`).

Why identity does not translate into prediction: most fixed teams live one to three days and an
outcome is known an hour after the launch, so by the time a team has ten resolved antecedents its
burst is usually over; the long-lived identities (the diffuse population, the fresh-wallet scripts) sit
at the market rate or change regime. The operator is the right unit to **describe** this market. It is
not a unit that **predicts** the next launch.

---

## 5. The rhythm, and GOOD against BAD inside the same team

`alpha_patterns/tables/BUNDLE_TEAM_RHYTHM_2026-10-07.md`, pre-registered in
`alpha_patterns/tables/TEAM_RHYTHM_PREREG_2026-10-07.md` (amendment 1 after a blind code review,
`alpha_patterns/audit/TEAM_RHYTHM_PREAUDIT_2026-10-07.md`), figures in `alpha_patterns/tables/team_rhythm.json`, synthetic
controls in `alpha_patterns/controles/team_rhythm_controls.json`.

**The rhythm is real.** Within a session (launches of one team without a pause above 90 minutes), the
gap between two launches has a median of **20.6 minutes** (quartiles 15.1 and 29.5, 634 gaps), and only
4.7 % of all gaps between consecutive launches of one team (39 of 827, sessions pooled) are under
10 minutes, against 47.2 % of the gaps between consecutive alerts of the whole market
(`rhythm_descriptive`). The coefficient of variation of a team's gaps is 0.37 in the median (a
memoryless process would give 1). Five fixed-wallet teams of ten launches or more worked exactly one
session of four to five hours, one launch every 18 to 24 minutes, then vanished. The cadence is close
to the refinancing cycle measured in `economic_mechanics/` (a median 21 minutes from one launch of the
same snipers to the next); the two numbers are compatible with the cadence being set by the capital
loop, which was not tested.

**The rhythm does not determine the outcome.** Seventeen pre-registered tests on hour of day, gap since
the previous launch, rank in the session, session size and sequences (after a GOOD, after two BAD,
after three BAD, rank modulo 3, runs): none passes the correction, the best q is 0.26
(`rhythm_vs_outcome`, `sequences`). After two BAD a team makes a GOOD 21.6 % of the time (40 of 185),
not "almost always". The one regular lead, launches from the seventh of a session onward (41 of 103,
40 %, against 84 of 310, 27 %, for ranks 1 to 6), has q = 0.34, and 40 % is under the break-even
precision anyway.

**Nothing measured before the alert detectably separates a team's GOOD from its BAD.** Inside the 28 teams that
have both (413 launches, 125 GOOD), 32 variables were compared with a within-team AUC: configuration
(tickets, number of snipers, SOL, share of supply, order of the snipers in the slot), wallets (age, new
to the team, overlap with the previous launch), funders (number, shared with the previous launch,
delay from funding to buy, synchronisation), rhythm (gap, rank, launches in the hour), the swarm of
external buyers already present at −5 and −10 s, the presence of other teams, the market's rate over
24 h and the entry premium. **None passes** (`within_team`, best q = 0.13). The strongest, the swarm at
−5 s (AUC 0.64), comes from the diffuse population on DISCOVERY alone: 0.67 on DISCOVERY, 0.46 on
SELECTION, 0.49 without the largest group. Changing configuration, wallets, funder, number of snipers
or stake between two launches is associated with no detectable change in the team's rate
(`configuration_changes`, the five C1 tests, every q ≥ 0.998; the heterogeneity of a team's rate across
its configurations, funders and wallet sets, C2, q 0.47 to 1.0; power not measured for these tests).
Other teams' outcomes within ±60 minutes show no detectable association with a launch's outcome
(correlation 0.001, p 0.20 within the day; power not measured). Four pre-specified prediction models trained on one block and tested on the other
(market rate; team history; configuration and rhythm; pre-alert reaction; all of them) announce nothing
in both directions (`prediction`).

Power, measured on synthetic outcomes with the real teams and sessions, for the within-team AUCs and
the after-a-BAD sequence only: a within-team effect of
AUC 0.68 planted on one variable is recovered in 47 of 50 worlds; a sequence dependence of +20 points
after a BAD in 46 of 50, of +15 points in 31 of 50, of +10 points in 5 of 50. The negative result makes
an effect near AUC 0.68, or a sequence of +20 points, improbable. It does not exclude AUCs between 0.5
and 0.68, or dependences up to 15 points. No power was measured for the configuration changes, the
interactions between teams or the four prediction models; there, "nothing passes" does not mean
"nothing".

Against the classification scheme fixed before the computation, the result falls in **C: same teams,
GOOD and BAD essentially unpredictable within the team with what is measured.**

---

## 6. The absorption hypothesis

`alpha_patterns/tables/TEAM_ABSORPTION_MECHANISM_2026-10-07.md`, pre-registered in
`alpha_patterns/tables/TEAM_ABSORPTION_PREREG_2026-10-07.md` (amendment 1 after `alpha_patterns/audit/TEAM_ABSORPTION_PREAUDIT_2026-10-07.md`),
measures in `alpha_patterns/code/feat_48_absorption.py`, tests in `alpha_patterns/code/mech_48_absorption.py`, figures in
`alpha_patterns/tables/team_absorption.json`, controls in `alpha_patterns/tables/team_absorption_checks.json`.

The last hypothesis was the simplest: perhaps a GOOD launch is one where enough outside buyers arrive
to absorb the team's inventory, and perhaps that demand is visible early. Every successful transaction
of every launch from the creation to alert + 30 s was reconstructed (308,520 transactions,
`alpha_patterns/tables/team_absorption_checks.json`, `K1`), with the team's inventory, its sales, the transfers to its exit
wallets and every external buyer, at fixed cuts before and after the entry. Because the detector's
price lags the pool by one to two seconds, every "decision at T" uses measures stopped at T − 3 s.

What the reconstruction shows, GOOD against BAD inside the same teams (medians,
`mechanism.descriptive`, `mechanism.timeline_medians`, `mechanism.price_after_entry`):

| | GOOD (n = 125) | BAD (n = 331) |
|---|---:|---:|
| share of the supply held by the snipers after the creation slot | 77.7 % | 77.8 % |
| value of that inventory at the alert price | 294 SOL | 297 SOL |
| exit wallets at alert + 29 s | 4 | 4 |
| first transfer sniper → exit wallet, from the creation | 8 s (98 of 125) | 7 s (239 of 331) |
| detector alert, from the creation | 12.6 s | 12.3 s |
| first sale by the team, from the alert | +8.8 s (107 of 125) | +8.4 s (282 of 331) |
| share of the inventory sold at creation + 30 s / + 40 s | 2.0 % / 4.6 % (+ 40 s: 78 of 125) | 1.8 % / 4.5 % (+ 40 s: 213 of 331) |
| external buyers at the alert / + 2 s / + 29 s | 37 / 42 / 86 | 35 / 40 / 84 |
| external SOL paid, as a share of the inventory's value, at + 2 s / + 27 s | 3.0 % / 11.0 % | 3.0 % / 9.9 % |
| price 30 s / 60 s / 2 min / 5 min after the entry | ×1.09 / 1.16 / 1.27 / 1.55 | ×1.01 / 1.00 / 0.96 / 0.64 |

Until 30 s after the alert, the GOOD and BAD launches of a team have the same inventory, the same
number of exit wallets, the same delays, and almost the same demand. The price then separates.

- **Before the entry, demand does not separate.** Of 19 pre-entry metrics (buyers, SOL, velocity,
  acceleration, demand over inventory, team sales), none passes; the best, the number of external
  buyers at the alert (AUC 0.60, p = 0.027, q = 0.41), inverts on SELECTION (0.64 against 0.45) and
  vanishes without the diffuse population (0.48, `sensitivity.explanatory_without_largest_group`)
  (`explanatory`). About 80 % of the external buyers
  present before the entry are bots already seen buying on at least five earlier launches, as many on
  the GOOD as on the BAD.
- **At the moment of decision, demand does not separate either.** Ten metrics at four decision times
  (+5, +10, +20, +30 s after the alert), each against the ×2 from an entry at that time: 40 tests, none
  passes, the best q is 0.91 (`tradable`). Entering later lowers the ×2 rate (27.5 % at +5 s, 24.5 % at
  +30 s) and nothing accumulated in between compensates.
- **Later, something appears, but it is already the price.** At alert + 29 s the ratio of external SOL
  to inventory value is higher on the GOOD than on the BAD in 12 of the 13 teams with at least three GOOD and three BAD
  (sign test, nominal p = 0.003) and the within-team AUC is about 0.60. By then the price move that defines the label has
  started; stratified on the price already made, the effect is not distinguishable (AUC 0.58,
  p = 0.14, `equal_price`). A post-hoc look without the diffuse population finds the velocity of
  demand at +17 to +27 s separating a little for a late entry (within-team AUC 0.61 to 0.65, DISCOVERY
  p = 0.012 to 0.03, SELECTION p = 0.14 to 0.18, `team_absorption_posthoc_nobig.json`): same direction
  on both blocks, not significant on SELECTION alone, chosen after reading a sensitivity. It is a lead
  for a prospective test, not a result.
- **No rule.** Five rules with thresholds fixed in advance (absorption ratio, demand over inventory,
  demand velocity, "the team sells and the price holds", "the team has not sold and demand is strong")
  at four decision times: none reaches 45.8 % on both blocks with enough cases; the only cell above
  it rests on 12 launches, 2 of them on SELECTION (`rules`).

Against the classification scheme fixed before the computation, the result falls in **D: hypothesis
not supported as an early predictive mechanism.** Absorption in the proper sense, during the liquidation, is not measurable with these
data: the team has sold about 4 % of its inventory when the observation stops, and its exit wallets
begin selling a median 81 s after receiving the tokens (`exit_destination/results.md`, another
sample). The hypothesis is neither demonstrated nor refuted; what is established is that the demand
observable before the decision does not carry the answer.

---

## 7. The one pre-declared rule, read once on VALIDATION

SWARM + CHEAP ENTRY (`alpha_patterns/tables/CANDIDATE_SWARM_CHEAP_ENTRY.md`, frozen in
`alpha_patterns/tables/CANDIDATE_SWARM_CHEAP_ENTRY_FREEZE.json` and `alpha_patterns/SELECTION_FREEZE.json`) was the only candidate carried
to a hold-out block. On VALIDATION it fired 13 times: 5 successes, **38.5 % against a block base rate
of 30.6 %**, lift 1.26, p = 0.39 by the pre-declared test, expected value −11.6 % per trade at $500
(`alpha_patterns/tables/validation.json`, `alpha_patterns/tables/CANDIDATE_SWARM_CHEAP_ENTRY_RESULT.md`). Verdict: **fail**. The OOS block was
not opened for it or for anything else. With VALIDATION consumed, the mechanical selection that the
plan had designed could no longer be run cleanly on this snapshot and was abandoned.

---

## 8. Where the information moves

![F5. Where the information sits](../figures/f5_act_iv_information_timing.png)

*Figure F5, `code/f_act_iv_timeline.py`, from `docs/out/a9_g2y_prelaunch.json`, `data/v05_creation_block.json`,
`data/v07_exit.json`, `alpha_patterns/tables/team_absorption.json` and `alpha_patterns/tables/x2_timing_summary.json`.*

Put the two eras on one clock and the result of this chapter becomes a statement about time.

In 2024 the signal preceded the move. The reference case of Act I had nine fresh wallets funded with
the same amount within 343 s, **7.6 hours before the token existed**; the accumulation they announced
then happened in public, one wallet after another. Whoever read the funding had hours to see it and
minutes to act while the move was still ahead.

In 2026 the signal and the move start together, and the outcome comes later than either. On the
456 launches of the 33 teams (the figure's population), the snipers hold about 78 % of the supply from
the creation slot (77.7 % on the GOOD, 77.8 % on the BAD; the reconstructed inventory matches the
detector's live share on all 1,015 alerts within 0.012); the tokens leave the sniper wallets within
seconds (first transfer a median 7 to 8 s after the creation, on the 337 launches with an observed
transfer; on the 42 hand-verified launches of June–July the median delay per sniper wallet was 17.5 s,
`data/v07_exit.json`, a per-wallet statistic on another sample, not the same measure); the detector
alerts at about 12 s; an entry is read a median 7.7 s after that. Everything that can be seen by then is structure: who the snipers are,
how they were funded, what they hold. At 40 s after the creation (about 27 s after the alert, close to the end of the
transaction window), the team has sold about 4.5 % of what it holds (4.6 % GOOD, 4.5 % BAD, on the 78 and
213 launches observed that long) and outside buyers have paid for about one tenth of its value (11.0 %
and 9.9 % at alert + 27 s). The price of a GOOD launch is at ×1.09 after 30 s, ×1.27 after two
minutes, ×1.55 after five; the BAD at ×1.01, ×0.96, ×0.64. The confirmed ×2, when it comes, comes a
**median 375 s after the entry** (10th percentile 118 s, 90th 1,503 s); 1.2 % of the GOOD launches have
confirmed it within 30 s, 10.7 % within two minutes, 42.3 % within five (`alpha_patterns/tables/x2_timing_summary.json`).

So the problem is not only that the Act I signal disappeared. The new mechanism **moved the useful
information along the time axis**. Coordination became visible at once, in the first slot; the demand
that decides the outcome became visible minutes later, inside the price itself. The window between the
two is exactly where an entrant has to decide, and it is empty of what the entrant needs.

---

## 9. Structural signal, predictive signal

Two different things were being called "the signal". They have to be kept apart.

A **structural signal** says something about the participants: that a launch is a bundle snipe, that
its snipers were funded together, that they belong to a team seen yesterday, that the team launches
every twenty minutes. Act III and studies 5 to 7 establish this signal against every null model they tested; it is
observable on chain within seconds and it is informative about how the market is organised. (Team
membership here is an on-chain linkage, wallets, funders and configurations that corroborate each
other, never a claim about who holds the keys.)

A **predictive signal** says something about the future price: that this launch, rather than that
one, will double. Studies 1 to 4 and 8 and the three mechanism studies looked for it in the entry
price, the bundle's geometry, the snipers' capital, the operator's identity and history, the team's
rhythm, its configuration, and the early demand. None of them found it at a level that survives its
own hold-out block or pays for the trade.

The bundle can be real, coordinated and informative about the structure of the participants without
being predictive of the subsequent return. That is the defensible statement of this repository:

> A strong structural signal of coordinated launch-time accumulation is observable on chain. The
> analyses performed did not establish that this signal, or anything else observable before the
> entry, was sufficient to predict which launches would subsequently produce the measured price
> outcome.

---

## 10. The falsification path

| # | hypothesis | what would have confirmed it | what the data said | verdict |
|---|---|---|---|---|
| H1 | identifying the team is enough | a team with a stable identity, an abnormal rate and a history available before each launch that predicts it | teams exist and their rates differ (p ≈ 0.001), but the history gain is −0.016 / +0.038 / +0.003 by block, the high-confidence rule is right 3 times in 29 | **no** (§4) |
| H2 | identifying the team's rhythm is enough | a position in the session, a gap or a sequence that lifts the team's rate above its own | 17 tests, best q 0.26; after two BAD 21.6 % | **no** (§5) |
| H3 | the bundle's configuration separates GOOD from BAD | a within-team difference in tickets, wallets, funders, synchronisation or concentration | 32 variables, best q 0.13, the strongest inverts between blocks | **no** (§5) |
| H4 | early external demand separates GOOD from BAD | more or faster outside buying before the entry on the GOOD | 42 against 40 buyers at +2 s; 19 pre-entry metrics, best q 0.41, inverts on SELECTION | **no** (§6) |
| H5 | absorption of the inventory explains the pump | the ratio of demand to inventory predicting the ×2 from the decision time | 40 tradable tests, best q 0.91; the ratio only separates the GOOD from +27 to +29 s, when the price is already part of the label | **no as an early signal** (§6) |

What remains is not an absence of structure. It is an absence of predictive information early enough
to act on.

---

## 11. What we could not predict

We could detect, within seconds of a launch:

- that a coordinated group existed and had bought the curve in the creation slot;
- that several wallets were run together, through shared funding, shared wallets and
  an identical ticket configuration confirming each other 47 to 212 times above chance;
- that about 78 % of the supply was held by that group;
- that the execution mechanism of 2024 had been replaced by this one.

We did not show that we could predict:

- which launch would reach ×2, or ×3;
- which launch of a given team would be its GOOD;
- when the external demand would become sufficient, or whether it would;
- which launch would be tradable with a positive expectation under the declared costs.

The boundary between the two lists is the result.

---

## 12. What survived, what did not, and what is not claimed

**Survived.** Coordinated launch-time accumulation as the norm (Act III); a repeatable operating loop
with a 20 minute cadence; recognisable teams whose ×2 rates differ by about 13 points around the
market's 27.5 %; the temporal asymmetry of §8.

**Did not survive.** Every candidate for an early predictive signal listed in §10; the only
pre-declared rule carried to VALIDATION; the "one pump in three" story; the idea that the early swarm
of buyers announces the outcome (it is mostly the same recurring bots, on every launch).

**Not claimed.** That no signal exists: the mechanical search would have frozen a lift of three on 8 to 15 % of the
alerts in 23 of 24 planted runs and carried it to OOS in 16 of 24 (`alpha_patterns/tables/BILAN_2026-10-06.md`,
§4), so a miss of that size is unlikely, and smaller effects stay open; the within-team AUCs between 0.5 and 0.68 are not
excluded; the post-hoc lead on demand velocity for late entries is untested. That absorption during
the liquidation is not the mechanism: that phase was not observed. That these results hold after
14 September 2026: DISCOVERY and SELECTION are 25 days (21 August to 14 September 2026) of one detector, SELECTION had been read by
an earlier search, and nothing here was validated out of sample. That the operators' own economics
are what this chapter measures: they sell into the swarm within seconds of the alert and are not
measured by a ×2 from our entry.

---

## 13. Provenance and reproduction

Every figure in this chapter comes from a committed file. The three mechanism studies and the
mechanical search are in `alpha_patterns/`; its `README.md` maps each claim to the JSON field or report
section that carries it, lists what was published (reports, pre-registrations, result JSON, scripts,
the test registry, the audits) and what was not (the feature matrix, the labels, the 7 MB of synthetic
controls), and records the three integrity checks a clone can run offline
(`alpha_patterns/code/chk_00_integrity.py`: frozen hashes, pre-registration hashes, registry hashes).
The scripts that produced the results need the unpublished derived files and the frozen tables of the
nine earlier studies; they are published so the method can be read, not re-run from a clone. Figure F5
regenerates offline from the committed JSON with `python3 code/f_act_iv_timeline.py`.

The headline figures of Act IV quoted in the root `README.md` are checked against these files by
`code/p1_readme_check.py` at every run of the test suite, like every other figure on the front page.
