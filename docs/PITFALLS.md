# Methodological pitfalls

**What this chapter is.** Fourteen documented episodes in which this project produced a result that
looked like a finding and was not. Each one is a card: the misleading number we first obtained, the
specific test that exposed it, the fix, the value that survived, and the transferable lesson.

Eleven of the fourteen killed a positive result. That is the point. A pipeline that only ever confirms
its author is a pipeline whose failure modes have not been found yet — they have simply not been
looked for.

**Everything here is recomputed, not recalled.** `code/p0_pitfalls_check.py` reads only the published
files in `./data/` and prints every figure quoted below. Run it:

```
python3 code/p0_pitfalls_check.py
```

Three figures that circulate in the project's internal notes could **not** be reproduced from the
published data; they are listed in [What did not reproduce](#what-did-not-reproduce) rather than
quietly dropped.

---

## Reference populations

| id | definition | n | clusters | days |
|---|---|---|---|---|
| **A** | detector log, full-curve buyback (>= 60 SOL), after removing the corrupted rows of P3 | 93 | 34 | 3 |
| **B** | fast-graduation tokens with a verified peak, sane MC regime | 1 243 | 123 | 20 |
| **C** | subset of B carrying a swap-level capture (0-20 min) | 278 | — | 7 |
| **canonical** | tokens on which a 0.5 SOL round trip is actually executable at entry+120 s | 196 | 20 | 6 |

Clusters are 30-minute gaps between detections. Every rate below is reported with its `n`, because on
this corpus the effective sample size is the number of clusters and days, not the number of rows.

---

## Summary

| # | pitfall | the number that was wrong | the number after correction |
|---|---|---|---|
| 1 | selection on the outcome | 69.8 % of tokens double | 46.3 % (the base rate) |
| 2 | denominator artefact | any low-MC variable "predicts" the multiple | elasticity 0.88 explains it; residual target, rho 0.05 |
| 3 | silent default value | 35.9 % reach 3x | 30.1 % |
| 4 | confounding variable | +30.0 pt, p = 0.0032 | +5.4 / +7.7 pt, MH odds ratio 1.22, p = 0.97 |
| 5 | touched is not cashed | median peak = 1.87x entry | 0/10 exit policies profitable |
| 6 | mixed units | median +1 h = **29.97x**, 91.5 % profitable | **0.394x**, 14.9 % profitable |
| 7 | broken supervision probes | "process alive" = healthy | CPU-time delta; two probes silently wrong |
| 8 | unfilled-exit convention | tp50 median **+31.5 %** | **+3.3 %** |
| 9 | unpriced lookahead | trough entry +14.7 % median | −2.8 % on the live-safe mirror |
| 10 | null distribution of the maximum | best of 38 policies = +7.26 % | 5 % critical value = +26.3 % |
| 11 | non-random missingness | 54.6 % of captures lost | loss is time-clustered, outcome-neutral |
| 12 | shared infrastructure in a graph | giant component 63.8 % | 17.0 % |
| 13 | criterion with no null of its own | "shared funder" separates targets from controls | it fires on 88.9 % of random groups; retired |
| 14 | control group matched on the wrong thing | split signature, targets vs controls, p = 0.0007 | vs *graduated* controls, p = 0.44 — the effect was the outcome |

---

# The seven core pitfalls

## P1 — Selection on the outcome

A boolean built from the outcome, used as if it were a feature.

**Symptom.** A field named `t_buyable` marked a token as tradable when its all-time peak occurred at
least 60 s *after* detection — a sane-looking executability filter. Restricted to those tokens, the
corpus looked transformed: **69.8 %** reached 2x versus 16.3 % for the rest, and **50.3 %** reached a
200 k market cap versus 6.1 %. Median peak 200 314 versus 65 232, a factor **3.07**. Reproduced on all
three populations (A: x2.59, B: x3.07, C: x3.17).

**Diagnosis.** Read the definition, not the name. `t_buyable` is `peak_ts >= detect_ts + 60 s`. A
token whose price collapsed immediately after detection has its peak *before* detection and is
excluded **because it lost**. The filter therefore conditions on the future: it does not select
tokens that are buyable, it selects tokens that went up. The give-away is the shape of the
contrast — an eight-fold gap on the absolute target is far larger than any pre-trade feature in this
project ever produced, and a filter that outperforms every real feature by an order of magnitude is
almost always reading the answer.

**Fix.** `t_buyable` was demoted from feature to diagnostic. It is allowed to appear in tables
describing what happened; it is forbidden as an entry criterion or as a model input. All headline
rates are reported on the whole population.

**After correction.** The honest 2x rate on B is **46.3 %** (n = 1 243), not 69.8 %. On the absolute
target, **30.9 %** reach 200 k, not 50.3 %.

**Lesson.** Any variable whose definition contains a timestamp or a value from after the decision
point is an outcome, whatever it is called. Audit definitions, not names.

---

## P2 — Denominator artefact

Dividing by the entry price makes the entry price look like a signal — in the wrong direction.

**Symptom.** The natural performance metric is the multiple `peak / entry MC`. Under it, a whole
family of variables became "predictive": anything correlated with a low entry market cap ranked well.
An operator whose launches happened to be detected early looked like an operator whose launches pump
harder.

**Diagnosis.** Regress `log10(peak)` on `log10(entry MC)`, demeaned within day. The elasticity is
**0.884** on B (n = 1 243), 0.673 on A, 0.761 on C. It is below 1, so by construction

```
log10(multiple) = log10(peak) − log10(entry MC)   ->   slope = beta − 1 = −0.126
```

measured at **−0.1263**, exactly as predicted. The multiple is *mechanically* decreasing in the entry
MC. Two rank correlations settle it: `spearman(entry MC, peak) = +0.561`, but
`spearman(entry MC, multiple) = −0.057`. The same corpus says "big entries reach bigger peaks" and
"small entries have bigger multiples" — both true, and both statements about the denominator.

The mirror image matters just as much. On the *absolute* target, the entry MC dominates everything:

| entry-MC decile | median entry MC | P(peak >= 200 k) | P(multiple >= 2x) |
|---|---|---|---|
| D0 | 26 039 | 0.097 | 0.581 |
| D4 | 50 061 | 0.210 | 0.484 |
| D9 | 162 211 | **0.764** | 0.409 |

A **7.9x** spread on the absolute target and a flat-to-inverted one on the multiple. Any candidate
signal correlated with entry MC will therefore "work" on one target and "fail" on the other, with no
information involved. In the operator audit, this accounted for **50.9 %** to **62.2 %** of the
apparent advantage of the best-ranked launch operators.

**Fix.** A residual target: `log10(peak)` minus its within-day OLS fit on `log10(entry MC)`, then
binarised at the within-day upper tercile. By construction the entry MC carries no information about
it.

**After correction.** `spearman(entry MC, residual) = +0.048` (n = 1 243) — the artefact is gone.
Results are now reported on two targets, the absolute one and the residual one, and a candidate must
survive both.

**Lesson.** Before treating a ratio as an outcome, measure the elasticity of its numerator to its
denominator. If it is not 1, the ratio encodes the denominator and every correlate of the denominator
becomes a free "signal".

---

## P3 — Silent default value

Ten rows out of 103 supplied a quarter of the positive class.

**Symptom.** Population A showed **35.9 %** of full-curve buybacks reaching a 3x multiple, and
**22.3 %** reaching 5x. The top of the distribution was dominated by a handful of spectacular
outcomes: 8.4x, 9.1x, 9.3x, 9.5x, 12.6x, 12.9x.

**Diagnosis.** Sort by multiple and look at the raw rows. All the extreme cases shared two values:
`detected_at = 0` and `detect_mc = 15000` — a placeholder timestamp and a constant, written by a code
path that had failed to fetch the real market cap. Across the raw detector log, **31 of 211 rows**
carry that exact pair. Ten of them fall inside population A. With a denominator frozen at 15 000
against a corpus whose true median entry MC is **60 432**, a perfectly ordinary token mechanically
produces a 3x to 13x multiple. Observed range of the ten: **2.96x to 12.88x** — every one of them
above the 2x threshold.

**Fix.** A `poison_default` flag at dataset build time, and exclusion from every rate. The flag is
kept in the published data so the contamination itself is auditable.

**After correction.**

| target | positives | contaminated | rate before | rate after |
|---|---|---|---|---|
| >= 2x | 56 | 10 (17.9 %) | 54.4 % | **49.5 %** |
| >= 3x | 37 | 9 (**24.3 %**) | 35.9 % | **30.1 %** |
| >= 5x | 23 | 7 (**30.4 %**) | 22.3 % | **17.2 %** |

The bias grows with the threshold: the tighter the criterion, the more of the positive class is pure
artefact.

**Lesson.** Placeholders survive into analysis because they are plausible. Test every field for
suspicious constants and zero timestamps *before* computing anything, and check what share of the
positive class each anomaly supplies — not what share of the rows it represents.

---

## P4 — Confounding variable

A technical label that turned out to be the entry price wearing a costume.

**Symptom.** The detector tags some launches with a bot-family label. Tokens carrying that label
reached a 100 k market cap **83.3 %** of the time versus **53.3 %** for the rest — a **+30.0 point**
gap on n = 93, Fisher exact **p = 0.0032**, crude odds ratio **4.38**. It looked like the single best
discriminator in the project.

**Diagnosis.** Ask what else the label correlates with. Median entry MC: **113 296** for labelled
tokens versus **44 305** for the rest; the association between the label and "entry MC above median"
is itself significant at **p = 7.1e-05**. And "reaches 100 k" is nearly deterministic once you are
detected above 100 k. So stratify:

| stratum | labelled | rest | delta |
|---|---|---|---|
| entry MC below median | 0.429 (n = 14) | 0.375 (n = 32) | **+5.4 pt** |
| entry MC above median | 1.000 (n = 34) | 0.923 (n = 13) | **+7.7 pt** |

Mantel-Haenszel across entry-MC quintiles: **OR = 1.22, p = 0.974**, against a crude OR of 4.38. The
entire effect was the market cap.

The sign flip is the confirmation. On the *multiple* target — the one the denominator artefact of P2
inverts — the same label goes the other way: **41.7 % versus 57.8 %, −16.1 points**. And in the bottom
entry-MC tercile the two groups are indistinguishable: **50.0 % versus 52.4 %**. A real effect does
not change sign when you change the target's denominator.

**Fix.** Stratified reporting on entry MC for every categorical contrast, plus a systematic check
that the candidate variable is not a proxy for the entry price.

**After correction.** No usable effect: adjusted OR 1.22, p = 0.97.

**Lesson.** When a categorical variable looks strong, first test it against the dataset's dominant
covariate. Publish the stratified table alongside the crude one; a claim that only exists unadjusted
is not a claim.

---

## P5 — Touched is not cashed

A peak that was reached is not a price that was obtainable.

**Symptom.** The median token in population B peaks at **1.87x** its detection market cap, and 46.3 %
double. Read naively, buying full-curve buybacks is a coin flip with an asymmetric payoff.

**Diagnosis.** Put a clock on the peak. On B (n = 1 243), **43.8 %** of tokens reach their all-time
peak within 60 s of detection — before an alert can be read, let alone filled — and 21.3 % peak
strictly *before* detection. The median detection-to-peak delay is **2.0 minutes**. The multiple is a
number about the token's history, not about any reachable order.

The decisive test is to stop measuring peaks and simulate a round trip: entry at creation+120 s, exit
under ten explicit policies, 5.82 % round-trip drag (1 % fee + 2 % adverse slippage per leg), a
0.5 SOL position, order-book depth required for the fill, and unfilled exits marked −100 %.

**Fix.** Realised PnL replaces peak multiples as the primary metric. Peaks are still reported, always
labelled "touched, not cashed".

**After correction.** On the 196 executable tokens / 20 clusters / 6 days:

- **0 of 10** policies positive in both median and mean.
- Extended to a 38-policy sweep (42 measured cells): **0** with a positive mean; best **−6.1 %**.
- The single positive median in the grid (`tp50`, +3.3 %) has the *worst* mean of the grid (−12.9 %)
  and changes sign on every split.
- A perfect-foresight oracle on the same corpus returns **+27 % median / +52.9 % mean** — so the value
  exists; nothing available at purchase time locates it.

**Lesson.** Never let an extremum stand in for a realisable price. Measure the metric you would
actually be paid, including fees, depth and the possibility that there is no bid.

---

## P6 — Instrumentation bugs

Four, each of which silently changed the answer rather than raising an error.

### 6a — Mixed units: the same number, off by a factor of 75

**Symptom.** Extending the horizon beyond the 20-minute captures, a post-buyback entry held for one
hour returned a **median 29.97x**, with **91.5 %** of tokens profitable — and still **6.86x** at
+24 h with 88.4 % profitable. That would have been the strongest result in the project by an order of
magnitude.

**Diagnosis.** The fetch script carried an explicit comment asserting that "GeckoTerminal prices and
swap prices are in the same unit (SOL/token)". They are not: swap-level captures record **SOL per
token**, the OHLCV endpoint returns **USD per token**. Every ratio was multiplied by the SOL price.
The tell was the magnitude — a median 30x on a corpus whose own base rate is a 2.1x *peak* is not a
finding, it is a unit error — and the implied factor lands squarely on the SOL/USD quote.

**Fix.** An hourly SOL/USDC series (1 000 candles, 2026-06-17 to 2026-07-29, 64.1-83.6 USD), and
conversion of the entry price at its own timestamp before any ratio is taken. Unit conventions are now
declared at the top of the shared library.

**After correction.**

| horizon | n | mixed units | converted |
|---|---|---|---|
| +1 h | 94 | 29.97x, 91.5 % profitable | **0.394x, 14.9 %** |
| +2 h | 92 | 23.58x, 89.1 % | **0.325x, 15.2 %** |
| +4 h | 86 | 19.44x, 88.4 % | **0.269x, 11.6 %** |
| +24 h | 69 | 6.86x, 88.4 % | **0.092x, 13.0 %** |

Conversion factor actually applied: 70.5 to 82.7, median **75.2**. The result reverses completely: a
post-buyback entry loses roughly 60 % of its value in an hour and 91 % in a day.

### 6b — Default User-Agent, rejected silently

The OHLCV provider rejects Python's default `urllib` User-Agent. Verified live while writing this
chapter:

```
urllib default UA : HTTP 403 Forbidden
browser UA        : accepted (200, or 429 when rate-limited)
```

The retry wrapper treated any non-429, non-404 error as transient, slept, retried, and returned
`None` — so a 100 % failure rate looked like an empty dataset, not like an error. **Fix:** an explicit
browser User-Agent, and a fetch layer that distinguishes "no data" from "not allowed" and reports the
HTTP status.

### 6c — History depth mistaken for history

The provider retains ~1 000 candles regardless of granularity. Verified: the hourly pull returns
exactly **1 000 candles spanning 41.6 days**; the same cap at minute granularity is **16.7 hours**. A
minute-level backtest over a 20-day window would have silently analysed only its last day. **Fix:**
choose granularity from the required span, and record `n_candles` and the actual covered span in every
row.

### 6d — A censored outcome field

The detector logs a running maximum, frozen when the row is written. Against the true peak fetched
later: **41 of 103 rows (39.8 %)** are below it, p10 of the ratio **0.363**. Computing the 2x rate on
the logged field gives **39.8 %** instead of **54.4 %** — a 14.6-point understatement. **Fix:** the
field is flagged "censored, never use as an outcome" in the dataset metadata, and outcomes are
re-fetched with a maturity requirement.

**Lesson (P6).** Instrumentation fails silently far more often than it fails loudly. Assert units at
the boundary, test transport with a live probe rather than trusting a wrapper, record the provider's
limits alongside the data, and treat any field that "looks fine" but is written incrementally as
censored until proven otherwise.

---

## P7 — Broken supervision probes

Two monitoring probes were wrong within one hour, and neither produced an error message.

**Symptom 1 — process identified by command line.** The monitor located the running job with
`pgrep -f "<job> --auto --model"`. That pattern also matches the monitor's own shell wrappers, whose
command lines contain the search string. It was therefore watching an inert shell (0.04 s of CPU in
26 minutes) instead of the job, and would have declared a freeze after 20 minutes and killed a
perfectly healthy run.
**Fix:** select by executable name (`ps -eo pid,comm,args`, match on `comm`), never by full command
line.

**Symptom 2 — probe unsupported by the local tool.** The freshness check used
`find -newermt "-20 minutes"`. On this machine `find` is `bfs 4.1.1`, which rejects relative
timestamps. Verified live: `bfs: error: Invalid timestamp.` — and the exit status was still 0, so the
caller saw an empty result, i.e. "nothing recent", i.e. a fabricated alarm.
**Fix:** compute file age from `stat -f %m` and arithmetic. A broken probe is worse than no probe: it
converts silence into false information.

**Symptom 3 — liveness measured as existence.** "Process alive" cannot see a hang. A live data daemon
had frozen for two days in July with its PID intact and the watchdog reporting healthy.
**Fix:** liveness is a *delta* — CPU time consumed since the last check, plus files written since the
last check. Both must stall before an alarm fires, which covers both failure modes (dead, and alive
but stuck).

**Symptom 4 — health endpoint that is not metered.** The data provider's `getHealth` returns "ok" on
an API key whose quota is exhausted.
**Fix:** validate keys against a metered endpoint that actually returns data, and treat any health
check that cannot fail as decorative.

**After correction.** The measured consequence of the whole family is visible in P11: 352 of 645
captures are empty because upstream failures were never surfaced. Detection would have taken minutes;
the data loss was permanent.

**Lesson.** A probe is code and needs its own tests — ideally a deliberate failure injection. Prefer
probes that measure *change* (CPU delta, bytes written) over probes that measure *existence*, and
never trust a health check that has no way of returning "unhealthy".

---

# Further pitfalls found in the same corpus

## P8 — The unfilled-exit convention: one line, three fake edges

**Symptom.** In the round-trip simulator, an exit for which no bid exists must be scored somehow. The
hard convention scores it −100 % (you hold something unsellable). The soft convention drops the token
from the sample. Switching conventions:

| policy | hard | soft | unfilled |
|---|---|---|---|
| tp50 (median) | **+3.3 %** | **+31.5 %** | 24.0 % |
| time_10m (mean) | −10.3 % | **+8.5 %** | 22.4 % |
| tp2x (mean) | −10.9 % | **+10.5 %** | 27.0 % |
| tp2x (median) | −17.4 % | **+5.4 %** | 27.0 % |

Three policies flip from clearly losing to apparently winning, on a one-word change.

**Diagnosis.** The soft convention silently drops exactly the losers: a token has no bid because it is
dead. Excluding it is excluding the worst outcome and calling the remainder the average. The
mechanism is visible in the unfilled rate — the more aggressive the take-profit, the more tokens are
dropped, and the larger the fake gain.

**Fix.** The hard convention is canonical, stated in the method, and the sensitivity to the choice is
printed on every run (`code/m5_roundtrip.py` reports hard / soft / strict-book side by side).

**After correction.** tp50 median **+3.3 %**, and 0/10 policies positive on both statistics.

**Lesson.** Every "N/A" needs an explicit, documented policy, and the sensitivity to that policy must
be published. Dropping missing outcomes is a selection filter, not a cleaning step. This one recurred
in 3 of 4 independent analysis tracks in a single run, which is why it is now a standing check.

## P9 — Pricing your own lookahead by building the live-safe mirror

**Symptom.** Entering 120 s after the price trough looked genuinely good: **+14.7 % median** on tp50,
60.9 % winners (n = 138).

**Diagnosis.** The trough is defined retrospectively — you only know it was the trough once the price
has come back. So the rule was reimplemented as an exact mirror that uses only past data: enter when
the current bucket is the running minimum so far and the last closed bucket has recovered. Same
policies, same costs, same corpus.

| anchor | tp50 median | tp50 mean | n |
|---|---|---|---|
| retrospective trough | **+14.7 %** | +3.3 % | 138 |
| live-safe mirror | **−2.8 %** | −12.9 % | 162 |

**17.5 points of median** is the lookahead, measured rather than argued.

**Where it goes.** The mirror identifies the true trough **78 times out of 162 (48 %)**. On those:
tp50 **+38.0 %** median, 73.1 % winners. On the other 84: **−36.6 %**, 26.2 % winners. In 52 % of
cases the true trough arrives *after* the trigger (median +120 s, p75 +390 s). The mixture reproduces
the base rate exactly. The strategy is not a filtering problem — it is a 48 % capture rate, and none
of the 27 flow features moves it (best AUC 0.596; the hypothesis's central feature scores 0.495, i.e.
nothing).

**Lesson.** Do not argue about whether a rule leaks; build its zero-lookahead mirror and subtract. The
difference is the lookahead in the unit of the result, and the decomposition tells you whether the
idea is wrong or merely untimely.

## P10 — The null distribution of the maximum

**Symptom.** Sweeping 38 exit policies over the canonical corpus, the best returned **+7.26 %** on the
primary statistic (mean of cluster means). A plausible-looking winner.

**Diagnosis.** The right null is not "is this policy better than zero" but "is the *best of 38* better
than the best of 38 on noise". Cluster-level sign-flip permutation, 5 000 draws, Westfall-Young max-T
correction:

- raw p of the best policy: **0.279**
- max-T corrected p: **0.585**
- Bonferroni over 38: **1.000**
- 5 % critical value of the max-null: **+26.3 %**

The observed best is a quarter of the threshold. Sweeping 38 policies over 20 clusters of pure noise
typically produces a "best" *better* than the one actually observed.

**Lesson.** Report the number of cells swept, and test the statistic you actually selected on — the
maximum — not the one you would have tested had you looked only once. In a related track, 115 370
tests were run while the permutation floor at 4 000 draws was 2.5e-4 and the Bonferroni threshold
5.6e-7: no result could have passed, by construction. Count your tests before you run them.

## P11 — Missingness: is the data you lost random?

**Symptom.** 352 of 645 swap captures are empty (**54.6 %**) — silent upstream API failures. The
usable corpus is 2.2x smaller than the file count suggests, which alone invalidates any headline
quoting "645 captures".

**Diagnosis (three axes).**

1. *Are the losses random in time?* No. A runs test gives **10 observed runs against 320.8 expected**
   under randomness, p = 0.0002; the longest gaps are 168 consecutive empty captures over 4.7 h and
   140 over 36.5 h. These are outages, not dropout.
2. *Are they random with respect to the outcome?* On an outcome measured by a source **independent**
   of the capture pipeline, empty and non-empty tokens are indistinguishable: P(multiple >= 2)
   **49.1 % vs 50.7 %**, permutation p = 0.77; median entry MC 47 897 vs 50 120, p = 0.21. The loss is
   outage-shaped but outcome-neutral, so it costs statistical power without biasing rates.
3. *Trap inside the trap.* Measured instead on labels produced by the **same** pipeline, the gap looks
   enormous (+29 points). That is coverage, not signal: the label exists only when the capture
   succeeded. Comparing groups on a variable whose availability depends on group membership measures
   availability.

**Corpus selection, separately.** The captures cover only **278 of 805** eligible tokens in their
window (34.5 %) and mildly over-sample winners: P(peak >= 200 k) **32.7 % vs 28.3 %** (+4.5 pt). Small,
but it is why capture-based rates are reported as an upper bound.

**Lesson.** Quantify missingness on three axes — time, covariates, outcome — and always run the
outcome axis on a source independent of the failing instrument. Otherwise you measure your own
coverage.

## P12 — Shared infrastructure fabricates graph structure

**Symptom.** Building a co-occurrence graph over tokens (edge = at least 3 shared sniper wallets)
produced a **giant component covering 180 of 282 tokens (63.8 %)** — apparently one vast coordinated
network.

**Diagnosis.** Rank wallets by ubiquity. The most frequent address appears on **58.5 %** of all
tokens, the next four on 35.1 %, 32.3 %, 24.8 % and 15.6 %. These are shared bots and public
infrastructure, not members of any single operation: they connect every token to every other token by
construction. Removing the 14 addresses present on 14 or more tokens collapses the giant component to
**48 of 282 (17.0 %)**.

A second control matters as much: a degree-preserving (Chung-Lu) null confined within the day
reproduced **1 502 of the 6 024** pairs meeting the clustering criterion — a **24.9 % false-positive
rate** — and a giant component of 564 against the 668 observed. The criterion was barely above chance.

The same logic produced a false negative in the other direction: one address was classified as
"infrastructure" on ubiquity alone, when it was in fact a launch operator sniping its own 51 tokens.
Ubiquity is evidence of sharing, not proof of it.

**Lesson.** In any co-occurrence graph, hub nodes must be identified and handled before the structure
is interpreted, and the resulting structure must be compared against a degree-preserving null. A
giant component is the default outcome of a co-occurrence graph, not a discovery.

## P13 — A detection criterion with no null distribution of its own

**Symptom.** The funding-split detector declares a token positive when any one of three criteria
fires on its first forty buyers: **A**, two or more of them are funded inside the same transaction;
**B**, three or more receive amounts equal to within 1e-4 relative inside one hour; **C**, two or
more share a private funder. On the first target it examined it returned `DECOUPAGE DETECTE`, and
the matched control group returned 1 positive in 9. That reads like a clean separation.

**Diagnosis.** The three criteria were never given a null distribution. Supplying one is cheap,
because the control group already provides the right population: 136 early-buyer wallets from tokens
selected on creation slot alone, with their funding events measured by the identical code. Pool
those wallets, draw random groups of forty, and re-run the criteria unchanged. Resampling destroys
any within-token co-occurrence, so every hit in a drawn group is a coincidence by construction.

Over 5 000 draws (`code/a1_null_model.py`):

| criterion | fires on a random group of 10 | of 20 | of 40 |
|---|---|---|---|
| **A** same funding transaction | 0.0000 | 0.0000 | 0.0000 |
| **B** same amount within one hour | 0.0000 | 0.0000 | 0.0000 |
| **C** shared private funder | 0.151 | 0.461 | **0.889** |

Restricted to the 70 wallets whose genesis was actually reached — the subset on which a negative is
even admissible — criterion C fires on **99.5 %** of draws.

Criterion C is not weak evidence. It is the near-certain outcome of drawing forty wallets of that
era, and its rate rises with group size the way a birthday problem does: more wallets, more pairs,
and funders drawn from a finite pool. The one control that had been recorded as positive was
positive on C alone, and so was the first target. Both were the same artefact wearing opposite
labels.

One diagnosis had to be ruled out before the criterion could be retired rather than repaired. If a
handful of *unlabelled infrastructure* addresses funded much of the population, the fix would be to
extend the known-terminals list, not to abandon C. Ranking the funders settles it: the control
population has **114 distinct private funders, of which only 7 fund two wallets or more**, and the
most prolific covers **4.4 %** of it. There is no hub to exclude. Seven small overlaps are enough,
because forty wallets make 780 pairs.

Criteria A and B fired **0 times in 5 000 draws** at every group size. They are specific because
they require a coincidence in identity *and* in time, not merely a shared counterparty.

**Correction.** Every measured token was recounted under A and B only (`code/a2_recount.py`). The
verdict on the first target flips from positive to negative, and the control base rate drops from
1/9 to 0/9. The disjunctive verdict `A or B or C` is retired: a criterion that fires on nine random
groups out of ten cannot enter a disjunction, because it decides the verdict on its own.

**Lesson.** A detector's own criteria need a null distribution before any of their output is read,
and the control group usually already contains the population needed to build one. "Fires on the
targets, rarely on the controls" is not a result until you know how often it fires on nothing at
all. Note also which direction the error ran: the criterion that felt most intuitive — *these
wallets share a funder* — was the worthless one, and it would have carried the headline claim.

## P14 — A control group that answers a different question

**Symptom.** With criterion C retired (P13), the split signature still separated the target tokens
from their control group: **12/14 against 1/9, Fisher one-sided p = 0.0007** on the original
disjunctive verdict, and 5/14 against 0/9 on the corrected one. The controls had been chosen well by
every rule the project had written down — matched on creation slot to within ±200 slots, selection
depending on nothing but creation time and market outcome, the rule fixed in code before any funding
was measured, pagination carried to genesis for all 171 harvested mints.

**Diagnosis.** The controls were *dead tokens*. Every target had graduated; not one control had.
Two things therefore differed between the groups at once — the exposure under test (coordinated
funding) and the outcome (whether the token went anywhere) — and the design could not tell them
apart. Tokens that attract buyers attract *sophisticated* buyers, bots and desks whose wallets are
funded in ways that look coordinated whether or not anyone coordinated them.

A second control group settles it: twelve pump.fun tokens from the same window that **graduated**
and that the author never traded, drawn by systematic sampling across the capitalisation range of
the reachable pool, retention rule fixed before measurement. Holding the outcome fixed:

| comparison | targets | controls | p |
|---|---|---|---|
| original verdict (A or B or C) vs **dead** controls | 12/14 | 1/9 | **0.0007** |
| A or B only vs **dead** controls | 5/14 | 0/9 | 0.0595 |
| original verdict (A or B or C) vs **graduated** controls | 12/14 | 8/12 | 0.2478 |
| A or B only vs **graduated** controls | 5/14 | 3/12 | **0.4371** |

Two thirds of *untraded* graduated tokens carry the same signature. The effect was the outcome, not
the exposure.

Note the direction of the residual bias, because it does not rescue the result. The graduated
controls come from a capitalisation-ranked listing, so they are survivors: on average they did
*better* than the targets. That bias runs against the hypothesis, and the hypothesis still fails.

**Correction.** No claim of systematic coordination is made for the phase-1 window. The reference
case and one further instance stand as observations; the generalisation does not. Full write-up in
`docs/SPLIT_PHASE1.md`.

**Lesson.** Matching on everything measurable *before* the outcome is not the same as matching on
the outcome. When the targets were selected because they succeeded, a control group of failures
measures success, and it will do so with a small p-value and complete conviction. Ask of every
control group: *what single thing does this differ from my targets by?* If the answer is "two
things", the test has not been run yet.

This is P4 — confounding — recurring in a new domain, eleven cards after it was first documented.
That recurrence is the point of keeping this file: naming a pitfall does not immunise you against
it, and the only reliable defence is the mechanical habit of building the second control group
before reading the first result.

---

# What did not reproduce

Three figures appearing in internal notes could not be re-derived from the published dataset. They are
recorded here rather than repeated:

- **"peak 310 k for buyable versus 48 k for the rest, factor 6.4"** (P1). Recomputing on every
  population gives factors of 2.55 to 4.39; the largest, 4.39, comes from the unfiltered B population
  (272 071 vs 61 999). The pitfall is real and reproduces qualitatively on all three populations; the
  specific pair of numbers does not. The chapter uses the recomputed B-clean figures (200 314 vs
  65 232, factor 3.07).
- **"a 93 % success rate manufactured by the buyable filter"** (P1). The 93 % in the project's history
  belongs to a different episode — a second-wave concentration filter that survived permutation,
  Bonferroni and a holdout in-sample and then returned 53 % out-of-sample. Its underlying data is not
  in this repository, so no figure is claimed for it here. The `t_buyable` filter's actual inflation
  is 69.8 % against a 46.3 % base rate.
- **"67 % of tokens peaked before detection"** (P5). On the published populations the strictly-before
  share is 16.9 % to 33.3 %, and the share peaking within 60 s of detection — the operationally
  relevant one — is 35.5 % to 43.8 %. The chapter uses those.

Keeping this section is deliberate. A number that cannot be regenerated from the published data is not
a result, even when it points the right way.

---

# Cross-cutting lessons

1. **Audit definitions, never names.** P1, P5 and P6d were all fields whose name described the
   intent and whose formula described something else.
2. **Measure the artefact before arguing about it.** Elasticity (P2), lookahead in points of median
   (P9), the null of the maximum (P10) — each converts a methodological worry into a number you can
   subtract.
3. **Stratify on the dominant covariate.** In this corpus that is the entry market cap. Almost every
   apparent categorical effect (P4) was it.
4. **Every convention on missing values is a hypothesis.** State it, and publish the sensitivity
   (P8, P11).
5. **Instruments fail quietly.** Units, transport, provider limits and censored fields (P6) changed
   results by factors of 75, by 100 % of the data, and by 15 points — none of them raised an
   exception.
6. **Probes are code.** Two of two supervision probes were wrong on first use (P7), and both failed
   toward false confidence.
7. **A null result is a deliverable.** Nine of these twelve cards killed a positive finding. The
   corpus's honest answer — no exit policy is profitable in expectation, and nothing observable at
   purchase time locates the winners — only became defensible once those nine were dead.
