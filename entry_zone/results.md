# Entry zone: results

The question: can a few simple filters on the entry market cap or premium, the SOL already engaged,
and the funding and spending capacity of the buyers mark a zone where a 2x is clearly more likely
than the base rate?

**No robust entry zone was found.** Every rule chosen on TRAIN either falls back to the base on
VALIDATION or, where it holds, turns out to be the premium or one operator.

Everything below comes from the frozen table (`derived/EZ_FREEZE.json`, sha256 `b6ce070c...`,
committed in `7af5c6f` with the plan before any rate was computed) and from `code/ez_20` to `ez_40`;
the tables are `tables/E0` to `E4`. The frozen model, table and results of `post_detection_forensics`
were only read. The future TEST was not touched. Nothing was pushed.

## Coverage and base rates

Primary label: a 2x from the entry price at the cut-off, confirmed by two reads within 15 minutes.

| cut-off | entry | TRAIN labels / base | VALIDATION labels / base |
|---|---|---:|---:|
| T0, creation (entry at the alert) | P0 | 896 / 22.4 % | 606 / 26.4 % |
| D, alert | P0 | 896 / 22.4 % | 606 / 26.4 % |
| +5 s | first read in [5, 15 s] | 755 / 21.7 % | 605 / 25.3 % |
| +10 s | | 753 / 21.4 % | 605 / 25.3 % |
| +20 s | | 769 / 18.7 % | 605 / 24.1 % |
| +30 s | | 768 / 17.1 % | 605 / 23.0 % |
| +60 s | | 758 / 15.7 % | 605 / 20.0 % |
| +2 min | | 765 / 13.9 % | 604 / 21.0 % |
| +5 min | first read in [300, 346 s] | 876 / 11.1 % | 597 / 15.2 % |

Every second of waiting costs: the base rate falls from 22 % (TRAIN) and 26 % (VALIDATION) at the
alert to 11 % and 15 % at +5 minutes. The TRAIN losses at +5 s to +2 min are the first four days,
before the detector sampled prices every 5 s.

Not measurable: the SOL the early buyers received in the 1 h to 7 days before the launch (73 % of
them already have 1,000 earlier transactions, the collection's cap, and a full scan of seasoned bots'
inflows is out of reach), and trades after alert + 30 s (the windows end there; later cut-offs keep
the trades up to + 29 s and add the price). The snipers' recent funding is complete for about half
of them (49 % at 7 days, 56 % at 1 h), from their genesis and their last 5 earlier transactions.

## The search

Per family, every TRAIN decile as a bound, every interval between two deciles, and the declared grids
(SOL engaged 1 to 100 SOL and 20-40 / 40-60 / 60-80 / 80-100, market cap in 5k / 10k / 20k / 25k USD
tranches, wallet counts 1 / 2 / 3 / 5), at each of the nine cut-offs. Combinations: 2 to 4 bound
atoms of one cut-off; 1.4 to 1.9 million pairs per cut-off, then a beam. One metric chose everything:
the Wilson lower bound of the TRAIN rate minus the TRAIN base, with 40 TRAIN alerts or more.
VALIDATION was read once, for the rules TRAIN chose.

## Answers

**A. Is there a market-cap zone where the 2x rate rises strongly?** No. The best TRAIN zone,
30k to 35k USD at +5 s (47.4 %, 27/57), gives 31.4 % (11/35) on VALIDATION against a 25.3 % base,
lower bound 18.6 %. The same zone at the alert and at +10 s falls to 26 to 27 %. What the market cap
does show, stably, is a ceiling: above about 98k USD at the alert (the TRAIN 80th percentile), a 2x
within 15 minutes almost never happens, 2.8 % (5/179) in TRAIN and 1.7 % (2/115) in VALIDATION. Below
it the rate is the base plus 5 to 6 points (27.3 % and 32.2 %). That ceiling is the operator: 99 %
and 100 % of the launches above it are "grouped", at a median premium of x10 to x12, and among the
single-operator launches not one is above it. USD bins also drift between the two periods (263
VALIDATION alerts in the 43k to 98k decile against 90 in TRAIN), as SOL/USD moved.

**B. Is there a threshold of SOL engaged by the buyers?** No threshold of the grid came out on top.
The best TRAIN rule is a narrow band, 97.3 to 101.7 SOL bought by + 20 s: 42.9 % (33/77) in TRAIN,
37.2 % (16/43) on VALIDATION against 24.1 %. It holds by 0.3 points and fails every control: explained
by the premium (lift beyond it +8.1 points [-10.2, +25.4]), gone without its dominant operator (11 of
43 alerts) or without the grouped launches, and at 11.1 % (4/36) once the largest buyer is removed.

**C. Is there a threshold of spending capacity?** No. The best TRAIN rule, largest buyer balance
between 25 and 35.4 SOL in the creation slot (43.3 %, 39/90), gives 34.3 % (12/35) on VALIDATION
against 26.4 %, lower bound 20.8 %.

**D. Is there a pattern of recent funding?** Only an operator's signature. The best TRAIN rule is a
ratio, the snipers' ticket over their funding of the last 24 h, at 0.9708 to 0.9710: one operator
funds its snipers and has them spend 97.08 % of it. On VALIDATION it selects 8 launches (5 double),
all of them "grouped", and its lift is explained by premium and actor. Share funded with about 1 SOL,
share funded by hubs, funder concentration and funding amounts did not come out on top in any window.

**E. Is there a simple combination of 2 to 4 conditions?** Not one that survives. The best TRAIN
combination, at the alert: premium <= 3.56, top 3 buyers under 60 SOL, SOL concentration (HHI) above
0.167 and more than 40 early buyers: 76.2 % (32/42) in TRAIN, 38.9 % (7/18) on VALIDATION against
26.4 %, lower bound 20.3 %.

**F. TRAIN 2x rate** and **G. VALIDATION 2x rate** and **H. tokens in the selection:**

| discovery | cut-off | TRAIN | VALIDATION | VAL base | class |
|---|---|---|---|---:|---|
| market cap 30k-35k USD | +5 s | 47.4 % (27/57) | 31.4 % (11/35) | 25.3 % | TRAIN OVERFIT |
| premium <= 3.30 | alert | 43.3 % (39/90) | 28.9 % (24/83) | 26.4 % | TRAIN OVERFIT |
| pool reserve <= 70.6 SOL | alert | 39.6 % (65/164) | 32.8 % (44/134) | 26.4 % | TRAIN OVERFIT |
| SOL bought 97.3-101.7 | +20 s | 42.9 % (33/77) | 37.2 % (16/43) | 24.1 % | PRICE/OPERATOR CONFOUNDED |
| 30-35 buys in the first 5 s | +5 s | 39.2 % (31/79) | 29.3 % (22/75) | 25.3 % | TRAIN OVERFIT |
| largest buyer balance 25-35.4 SOL | creation | 43.3 % (39/90) | 34.3 % (12/35) | 26.4 % | TRAIN OVERFIT |
| ticket / 24 h funding 0.9708-0.9710 | +5 min | 33.8 % (22/65) | 62.5 % (5/8) | 15.2 % | PRICE/OPERATOR CONFOUNDED |
| premium + top 3 + HHI + early buyers | alert | 76.2 % (32/42) | 38.9 % (7/18) | 26.4 % | TRAIN OVERFIT |
| market-cap ceiling (descriptive, not chosen by the metric) | alert | 27.3 % below, 2.8 % above | 32.2 % below, 1.7 % above | 26.4 % | PRICE/OPERATOR CONFOUNDED |

**I. Does a signal survive the premium and operator controls?** No. The two rules that hold on
VALIDATION are explained by premium and actor (the SOL band also by the premium alone), and the
market-cap ceiling is the grouped operator family.

**J. Trading simulation.** Run for the two rules whose VALIDATION lower bound is above the base,
with the cost model of `post_detection_edge` ($500, 1 % fee per leg, 0.005 SOL per transaction,
price impact from the implied depth). The SOL band: 60 VALIDATION cells (5 entry delays x 3 take
profits x 4 timeouts), every one with a negative net mean, from -4.8 % to -44.9 % per trade; all
alerts with the same exits lose -23 % to -50 %. The funding signature: at most 3 simulated trades in
any cell (the price is read every 45 s at +5 minutes), so no estimate. No estimable cell has a net
mean with a CI above 0.

## Classification

| discovery | class |
|---|---|
| best market-cap zone | TRAIN OVERFIT |
| best premium zone | TRAIN OVERFIT |
| best other price zone (pool reserve) | TRAIN OVERFIT |
| best SOL-engaged zone | PRICE/OPERATOR CONFOUNDED |
| best counts and timing | TRAIN OVERFIT |
| best capacity zone | TRAIN OVERFIT |
| best funding zone | PRICE/OPERATOR CONFOUNDED |
| best combination | TRAIN OVERFIT |
| market-cap ceiling | PRICE/OPERATOR CONFOUNDED |

No discovery is ROBUST (that needs the future TEST) or PROMISING BUT UNCONFIRMED.

## The operational sentence

No robust entry zone was identified. The conditions of the form "X + Y + Z, from a market cap
between A and B" that TRAIN produced do not survive VALIDATION, or survive it only as the premium or
one operator, and none makes money after costs in the simulation.

## Why TRAIN looked so good

Seven of the eight TRAIN winners have a permutation p of 0.005 or below: shuffling the TRAIN labels
produces a rule as good at most once in 200. They still fail on VALIDATION. The permutations shuffle alerts one by
one, while outcomes move by operator and by period; a rule that fits the operators active in late
August and early September beats shuffled labels and still says nothing about the second half of
September. Several TRAIN winners are narrow bands on one operator's constants (a top ticket of exactly
20 SOL, a 97.08 % spend ratio, a 25.35 SOL funding), which is what that looks like.

## Deviations and notes

- Precisions made in the code before the search ran, recorded at the end of `analysis_plan.md`:
  market-cap tranches up to the TRAIN 95th percentile, the SOL grid on SOL engaged only, "other
  price" as its own family, combinations on bound atoms.
- The plan's drawdown mixes the launches that never double (they often fall 99 %); `E3_controls.md`
  also gives the drawdown before the 2x among those that reached it (median -5 % for the SOL band).
- The trading simulator enters on a read within 10 s of the latency; at +5 minutes, where reads come
  every 45 s, that leaves few entries.
- A rule that holds on VALIDATION with fewer than 30 alerts is not counted as a confirmation.
