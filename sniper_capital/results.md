# Sniper capital: results

The question: does the capital a sniper really had before its buy, and the share of it the sniper
risked, say which launches double quickly, beyond the entry premium and the operator?

**No relation survives.** Ticket over capital separates winners from losers on its own, but it adds
nothing once premium, operator and the number of snipers are known, and its effect between
comparable launches changes sign from week to week. Every threshold rule chosen on TRAIN either falls
back to the base on VALIDATION or holds only by setting the grouped operators aside.

Option 1 of the owner: only the data already collected, no RPC call. Table frozen in `250fda9`
(sha256 `84569edb...`) with the plan before any rate; scripts `code/sc_20_analysis.py` and
`sc_30_trade.py`; tables `tables/S1` to `S4`. The previous studies, the future TEST and the live
detector were not touched. Nothing was pushed.

## What the data are

6,822 sniper records over 1,657 launches; labeled launches (confirmed 2x within 15 min of the alert,
as frozen before): 896 TRAIN, 606 VALIDATION, base 22.4 % and 26.4 %.

The snipers are close to identical, winners and losers alike. Median capital before the buy 25 SOL,
median ticket 20 SOL, ticket over capital 0.80 to 0.85, last funding 24 to 25 SOL received a few
minutes before the buy, from a balance of zero: for most snipers the capital is the last funding,
so ticket / capital, ticket / last funding and capital after / before (about 1 minus the ratio)
carry the same information.

| family | launches where every sniper is OBSERVED, TRAIN / VALIDATION (labeled) |
|---|---|
| ticket / capital, capital after / before, counts by fraction, other aggregates | 896 / 606 (100 %) |
| last funding: amount, time, ticket / funding, funding about the ticket | 827 / 536 (92 % / 88 %) |
| genesis topology (funder, hub, source) | 734 / 531 (82 % / 88 %) |
| funding received over 1 h, 6 h, 24 h, 7 days; SOL spent in the history | not tested (see the end) |

No value was imputed; a launch with one sniper not OBSERVED is out of that family's test.

## The central test: ticket / capital

The launch median of ticket / capital (`a_med`), fixed in the plan:

- alone, a lower ratio goes with more 2x: ROC-AUC 0.622 in TRAIN, 0.727 in VALIDATION;
- on top of premium + operator + number of snipers (TRAIN boosting, measured on VALIDATION): +0.013
  of ROC-AUC [-0.029, +0.057], nothing established;
- between comparable launches (same week, premium tercile, operator family, number of snipers),
  ratio above its TRAIN median against below: +1.8 points [-5.8, +9.6] in TRAIN, -22.8 points
  [-32.3, -13.2] in VALIDATION. The two periods disagree. Week by week, among single-operator
  launches, the high-ratio launches double less in the weeks of 08-23, 08-27, 09-15, 09-17 and 09-24
  and more in those of 09-03 and 09-10 (31.7 % against 20.9 %, 52.1 % against 29.3 %). The sign
  follows the operators active that week; it is not a stable signature.

## Answers

**A. Does the sniper's capital carry information?** On its own, a little: the launch's total capital
reads ROC-AUC 0.60 (TRAIN) and 0.68 (VALIDATION). Not beyond premium and operator.

**B. Is ticket / capital better than the absolute ticket?** On its own, slightly: 0.62 and 0.73
against 0.60 and 0.64 for the sum of tickets. Neither is independent of premium and operator.

**C. Does the recent funding add something?** The amount of the last funding does not separate
(ROC-AUC 0.54 and 0.53); its best TRAIN rule falls back on VALIDATION (TRAIN OVERFIT). The funding
received over 1 h to 7 days was not tested (option 1).

**D. Does the timing of the funding add something?** Winners' snipers were funded somewhat earlier
(median 247 and 292 s before the buy against 157 and 154 s; ROC-AUC 0.61 and 0.66), but the best
TRAIN rule does not beat its permutations (p 0.105, NO SIGNAL) and the premium explains it (lift
beyond premium +1.7 points [-5.5, +9.7], odds ratio within premium and operator 0.87).

**E. Are several snipers funded by the same source a signal?** No. A shared genesis funder reads
ROC-AUC 0.49 and 0.47, a shared last funder 0.50 and 0.46. Funding by a hub reads 0.63 in both
splits but is explained by the premium (lift beyond it +6.3 points [-0.6, +12.8]).

**F. Do the signals survive the premium?** Ticket / capital does not (above). Two family rules keep a
lift beyond premium, actor and snipers, and fall at the next check.

**G. Do they survive the operator?** No. Among single-operator launches only, every rule that holds
on VALIDATION stops separating: at most two snipers risking 90 % or more of their capital, 34.9 %
against 33.0 %; ticket within 90-100 % of the funding for at most a quarter of the snipers, 33.1 %
against 31.1 %; a hub-funded sniper, 30.8 % against 30.7 %. Their lift came from setting aside the
grouped operators, whose snipers spend 97 % of what they receive.

**H. A simple selection clearly above the base?** None that survives. The four selections that hold
on VALIDATION reach 31 to 35 % against 24 to 26 %, and all four are the operator.

**I. Positive after costs and entry delay?** No. 300 estimable VALIDATION cells (5 rules x 5 delays x
12 exits), none with a net mean whose CI is above 0; at 10 s, take profit 2x within 15 min, -30 % to
-38 % per trade, about what buying every alert gives (-32 %).

**J. How many observations?** 6,822 sniper records, 896 and 606 labeled launches, and per rule the
counts in the table below.

## Classification

| signal (best TRAIN rule of its family) | TRAIN | VALIDATION | VAL base | class |
|---|---|---|---:|---|
| 1 ticket / capital: 0.849 < mean <= 0.887 | 39.3 % (35/89) | 20.0 % (10/50) | 26.4 % | TRAIN OVERFIT |
| 2 capital after / before: 0.100 < mean <= 0.140 | 38.9 % (35/90) | 20.8 % (10/48) | 26.4 % | TRAIN OVERFIT |
| 3 ticket / last funding: 0.848 < median <= 0.887 | 39.0 % (32/82) | 29.7 % (22/74) | 24.1 % | TRAIN OVERFIT |
| 4 time since last funding: 102 < median <= 646 s | 27.8 % (115/413) | 29.8 % (79/265) | 24.1 % | NO SIGNAL |
| 5 last funding amount: HHI <= 0.25 | 34.3 % (57/166) | 29.7 % (27/91) | 24.1 % | TRAIN OVERFIT |
| 6 ticket within 90-100 % of funding for <= 25 % of snipers | 27.5 % (145/527) | 33.2 % (119/358) | 24.1 % | PRICE/OPERATOR CONFOUNDED |
| 7 at most 2 snipers risking >= 90 % of capital | 28.8 % (181/629) | 35.0 % (153/437) | 26.4 % | PRICE/OPERATOR CONFOUNDED |
| 8 a hub-funded sniper | 27.0 % (141/523) | 30.9 % (122/395) | 23.9 % | PRICE/OPERATOR CONFOUNDED |
| 9 ticket HHI <= 0.25 | 35.4 % (64/181) | 34.2 % (52/152) | 26.4 % | PRICE/OPERATOR CONFOUNDED |
| ticket / capital, central test | ROC-AUC 0.62 | ROC-AUC 0.73, +0.013 on top of the controls | | PRICE/OPERATOR CONFOUNDED |
| funding over 1 h / 6 h / 24 h / 7 d, SOL spent in the history | | | | INSUFFICIENT DATA |

Each family's base is that of the launches where its variable is OBSERVED. No signal is ROBUST or
PROMISING BUT UNCONFIRMED, so the sentence "at cut-off X, the launches with A + B + C..." is not
written: no relation survived.

## What is left untested, and its cost

The funding windows (ratios B, C, D, I of the brief) are OBSERVED for 49 to 56 % of the snipers,
nearly all of them fresh wallets (5 transactions or fewer before the buy); for snipers with a longer
history they are observed for 3 to 7 %. Completing them, from `coverage.md`: 44,000 calls for 1 h,
87,000 for 6 h, 120,000 for 24 h, 190,000 for 7 days (which covers all four), about 1 to 4 hours on
the Helius budget the detector shares. The SOL spent in the history (ratio E) would take 276,000
calls and stays unbounded for 758 records of wallets with 1,000 transactions or more. Given that the
last funding, which is the capital for most snipers, and its timing carry nothing beyond premium and
operator, this study does not recommend that collection; it was not launched.

## Notes

- Section 8's rule search used single conditions per family; the brief's combinations were not part
  of option 1.
- The residual lift beyond the TRAIN reference models also absorbs the drift of the base rate between
  the periods (single-operator launches double more often in VALIDATION than in TRAIN); the
  single-operator check is the direct one, and it is the one every surviving rule fails.
- The trading simulation entered at the alert plus the delay; at most a handful of entries are
  missed where the price was not read within 10 s.
