# Sniper capital: analysis plan, written before any rate is computed

Question: does the capital a sniper really had before its buy, and the share of it the sniper put
on the new token, carry information on which launches double quickly, beyond the entry premium,
the operator and the number of snipers?

Option 1 of the owner (2026-10-01): only the data already collected, no new RPC call. The frozen
table, model and results of the previous studies, the future TEST and the live detector are not
touched. Nothing is pushed.

## Data and coverage

- Units: the 6,822 sniper records (sniper x launch) of `coverage.md`, aggregated per launch.
- Context and labels read, not recomputed, from the frozen table of `post_detection_forensics`
  (sha256 `9d2fd31f...`): split, operator cluster, actor, entry premium, number of snipers
  (`b_core_n`), and the labels.
- A sniper value is OBSERVED, or it is not used. A launch value is computed only when every sniper
  of the launch is OBSERVED for it; otherwise the launch is left out of that feature, and the number
  of launches kept is reported with every result. Nothing missing is set to zero.

## Sniper values (all strictly before the sniper's buy)

- capital: native SOL just before its first buy transaction, plus any SOL sent to it inside that
  transaction (6 records); after: the balance after its last buy in the slot; ticket: the SOL it
  sent to the curve.
- A = ticket / capital; G = capital after / capital before.
- Last funding: the most recent earlier transaction in which its SOL rose and someone else signed,
  among the 5 transactions before the buy (20 for the creator). OBSERVED when there is one: amount,
  time to the buy, sender, ticket / amount, amount / capital, the balance just before it.
- Genesis funder (wallets with fewer than 1,000 earlier transactions), whether it was a hub before its
  earliest funding in the corpus, and its own funder (the source).

## Launch features, by family (the owner's priorities)

1. ticket / capital: median, mean, minimum, maximum, p25, p75, total tickets over total capital.
2. capital after / capital before: median, mean, minimum, maximum.
3. ticket / last funding: median, minimum, maximum.
4. time since the last funding: median, minimum, maximum; share of snipers funded less than 1 h and
   less than 5 min before.
5. last funding amount: median, minimum, maximum, sum, concentration (HHI).
6. funding about the ticket: share and number of snipers whose ticket is 90 to 100 % of their last
   funding; share whose ticket exceeds it.
7. snipers by fraction risked: number with ticket / capital below 10 %, at or above 25, 50, 75 and
   90 %; share at or above 50 %.
8. topology: genesis funders (distinct, largest share of snipers on one funder, at least two snipers
   on one funder, share funded by hubs), sources (distinct, largest number of funders on one source),
   last funders (distinct, largest share, at least two on one), spread of the last fundings' times.
9. other aggregates: sum of tickets, sum of capital, HHI of capital and of tickets, the largest one,
   two and three capitals' share.

## The central test (ticket / capital, fixed now)

The launch median of ticket / capital (`a_med`):
- ROC-AUC on TRAIN and on VALIDATION, oriented on TRAIN;
- on VALIDATION, ROC-AUC of a TRAIN model (boosting, 150 rounds) of premium + actor + snipers +
  `a_med`, minus the same model without `a_med`, cluster-bootstrap CI;
- matched comparison: strata of week x premium tercile x actor x snipers (4 or 5 and more), `a_med`
  above against below its TRAIN median, Mantel-Haenszel risk difference, TRAIN and VALIDATION,
  stratified bootstrap CI;
- the same without the dominant operator and on single-operator launches only.

## Rule search (TRAIN only)

Per family: every TRAIN decile as a bound and every interval between two deciles, and the owner's
grids: ticket / capital < 1 %, 1-5, 5-10, 10-25, 25-50, 50-75, 75-90, >= 90 %; funding / capital
< 10 %, 10-25, 25-50, 50-75, 75-100, >= 100 %; time since funding < 1 min, 1-5 min, 5-30 min,
30 min-1 h, 1-6 h, 6-24 h, >= 24 h; counts >= 1, 2, 3, 4, 5 and = 0. Metric: Wilson 95 % lower bound
of the TRAIN rate of a confirmed 2x within 15 min minus the TRAIN base, at least 40 TRAIN launches.
Best per family; 200 permutations of the TRAIN labels rerun the family's search for its p.
VALIDATION read once for each family's best.

## Controls, for every family's best (not only the survivors)

TRAIN then VALIDATION with N and coverage; lift beyond TRAIN models of premium, of actor, of snipers,
and of premium + actor + snipers (VALIDATION, observed minus expected inside minus outside, cluster
bootstrap); VALIDATION without the dominant operator of the selection and without the grouped
launches; VALIDATION halves; logistic models fitted on TRAIN, signal alone, + premium, + operator,
+ premium + operator, against the same without the signal: VALIDATION ROC-AUC, PR-AUC, the AUC gain
with its cluster-bootstrap CI, and the Mantel-Haenszel odds ratio of the signal within premium
tercile x actor strata.

## Classification

- INSUFFICIENT DATA: the family's features are observed on fewer than half the launches, or the
  VALIDATION selection has fewer than 30 launches.
- NO SIGNAL: the family's permutation p is 0.05 or more.
- TRAIN OVERFIT: the VALIDATION Wilson lower bound is at or below the VALIDATION base.
- PRICE/OPERATOR CONFOUNDED: VALIDATION holds, but the lift beyond premium + actor + snipers has a
  CI reaching 0, or it fails without the dominant operator or without the grouped launches.
- PROMISING BUT UNCONFIRMED: every check passes and both VALIDATION halves are above the base.
- ROBUST: needs the future TEST; not reachable here.

The trading simulation of `entry_zone` (entry at the alert to + 30 s, take profit 1.5 / 2 / 3x,
timeouts 5 to 60 min, $100 / $500 / $1,000, the same costs) runs only for rules whose VALIDATION
lower bound is above the base. If a signal is PROMISING, the report gives the exact number of calls
needed to test it with the funding windows completed. The 7-day collection is not launched.

Labels, as frozen in the previous study: primary `A_conf_2x_15m`; also `A_conf_2x_5m`,
`A_conf_2x_1h`, `A_conf_1.5x_15m`, `A_conf_3x_15m` (the frozen table has no confirmed 3x within
1 h; its single-read version is `A_mfe_3600s` >= 3).
