# Methodological Pitfalls

## Fifteen ways this investigation could have been wrong

This document is not a collection of caveats added after the analysis.

It is the record of the investigation attempting to **break its own conclusions**.

Fifteen claims emerged during the analysis. For each one, the same question was asked:

> **What would have to be true for this result to be an artefact?**

A dedicated test was then built.

The outcome was deliberately uncomfortable:

* **11 of 15 claims failed under their own validation tests.**
* One additional negative finding was invalidated in the opposite direction: what initially looked like a negative result was ultimately traced to a broken data connection.

That is the purpose of this document.

A pipeline that only confirms its author is not an investigation.

Everything reported elsewhere in this repository is what remained **after these failure modes were actively tested**.

Every figure below is reproducible from the published dataset with:

```bash
python3 code/p0_pitfalls_check.py
```

Three figures from internal notes could not be reproduced from the published dataset. They are documented explicitly at the end rather than silently removed.

---

# 1. Reference Populations

| ID            | Definition                                                     |     n | Clusters | Days |
| ------------- | -------------------------------------------------------------- | ----: | -------: | ---: |
| **A**         | Detector log, full-curve buyback ≥60 SOL                       |    93 |       34 |    3 |
| **B**         | Fast-graduation tokens with verified peak and sane MC regime   | 1,243 |      123 |   20 |
| **C**         | Subset of B with swap-level capture                            |   278 |        — |    7 |
| **Canonical** | Tokens where a 0.5 SOL round trip is executable at entry +120s |   196 |       20 |    6 |

Clusters are launches separated by ≤30 minutes.

The nominal row count is therefore not the effective number of independent observations. Rates are always reported together with their population context.

---

# 2. The Investigation in One Table

| #       | Failure mode                  | What initially appeared true          | What survived                                             |
| ------- | ----------------------------- | ------------------------------------- | --------------------------------------------------------- |
| **P1**  | Selection on the outcome      | 69.8% of tokens double                | **46.3% base rate**                                       |
| **P2**  | Denominator artefact          | Low-MC variables predict the multiple | Elasticity **0.88**; residual target removes the artefact |
| **P3**  | Silent default value          | 35.9% reach 3x                        | **30.1%**                                                 |
| **P4**  | Confounding variable          | +30.0 points, p=0.0032                | Adjusted OR **1.22**, p=0.97                              |
| **P5**  | Peak ≠ executable price       | Median peak = 1.87x entry             | **0/10 exit policies profitable**                         |
| **P6**  | Instrumentation errors        | +1h = 29.97x, 91.5% profitable        | **0.394x, 14.9% profitable**                              |
| **P7**  | Broken monitoring             | “Process alive” = healthy             | CPU/IO deltas exposed failures                            |
| **P8**  | Missing-exit convention       | +31.5% median                         | **+3.3%** under hard convention                           |
| **P9**  | Lookahead                     | Trough entry = +14.7%                 | **−2.8% live-safe mirror**                                |
| **P10** | Multiple-testing winner       | Best of 38 = +7.26%                   | Max-null critical value **+26.3%**                        |
| **P11** | Missingness                   | 54.6% of captures lost                | Time-clustered, outcome-neutral                           |
| **P12** | Shared infrastructure         | Giant component = 63.8%               | **17.0%** after hub control                               |
| **P13** | Detector without its own null | Shared funder separates targets       | Fires on **88.9% of random groups**                       |
| **P14** | Wrong control group           | p=0.0007                              | Graduated controls: **p=0.4371**                          |
| **P15** | Transport failure             | 0/14 carry the pattern                | **3/9 measured; 5 impossible to measure**                 |

---

# 3. P1 — Selection on the Outcome

## A variable that secretly knew the answer

A boolean named `t_buyable` looked like an executability filter.

It was not.

### The symptom

Tokens satisfying the filter appeared dramatically better:

* **69.8%** reached 2x;
* **50.3%** reached 200k market cap.

The rest reached 2x only **16.3%** of the time.

The effect reproduced across populations.

That made it look compelling.

It was also wrong.

### The diagnosis

Read the formula instead of the variable name.

`t_buyable` was defined as:

```text
peak_ts >= detect_ts + 60s
```

A token whose peak occurred immediately after detection was included.

A token whose peak occurred before detection was excluded.

The filter therefore used future outcome information to decide which observations belonged in the sample.

It was not identifying “buyable” tokens.

It was identifying tokens that **went up after detection**.

### The correction

`t_buyable` was demoted from feature to diagnostic.

It cannot be used as:

* an entry criterion;
* a model input;
* a headline selection filter.

### What survived

Population B:

**46.3%** reached 2x.

For the 200k target:

**30.9%**, not 50.3%.

### Transferable lesson

> **Audit the formula, not the name.**

Any variable containing information from after the decision point is an outcome, regardless of what its name says.

---

# 4. P2 — The Denominator Artefact

## When the denominator manufactures the signal

The natural performance metric was:

```text
peak MC / entry MC
```

It looked reasonable.

It also created misleading signals.

### The symptom

Variables associated with low entry market cap appeared predictive of large multiples.

An operator whose launches happened to be detected early could therefore appear to have better-performing launches when the effect was partly created by the denominator.

### The diagnosis

Regress:

```text
log10(peak MC)
```

against:

```text
log10(entry MC)
```

within day.

Measured elasticity:

* **0.884** on B;
* **0.673** on A;
* **0.761** on C.

Because:

```text
log10(multiple)
=
log10(peak)
-
log10(entry MC)
```

the expected slope of the multiple against entry MC is:

```text
beta - 1 = -0.126
```

Measured:

**−0.1263**

Exactly what the denominator predicts.

The rank correlations tell the same story:

* entry MC vs peak: **+0.561**
* entry MC vs multiple: **−0.057**

Both can be true simultaneously.

Large entries reach larger absolute peaks.

Small entries generate larger multiples.

The ratio creates the apparent relationship.

### The correction

A residual target was introduced:

```text
log10(peak)
-
within-day OLS fit of log10(peak) on log10(entry MC)
```

It was then binarised at the within-day upper tercile.

### What survived

Correlation between entry MC and the residual:

**+0.048**

The denominator artefact is effectively removed.

### Transferable lesson

> **Before trusting a ratio, measure the elasticity of the numerator against the denominator.**

If the elasticity is not 1, the ratio contains information about the denominator.

---

# 5. P3 — Silent Default Values

## Ten rows were capable of writing the story

Population A initially showed:

* **35.9%** reaching 3x;
* **22.3%** reaching 5x.

The top outcomes looked spectacular:

**8.4x, 9.1x, 9.3x, 9.5x, 12.6x, 12.9x.**

### The diagnosis

The extreme observations shared:

```text
detected_at = 0
detect_mc = 15000
```

Those were not measurements.

They were placeholders written when the real market-cap fetch failed.

Across the raw detector log:

**31 / 211 rows**

carried the pair.

Ten entered population A.

The true median entry MC was:

**60,432**

while the placeholder was frozen at:

**15,000**

An ordinary token could therefore acquire an artificially large multiple.

### The correction

Every contaminated row receives:

```text
poison_default = true
```

The rows remain in the published data so the contamination is auditable.

They are excluded from rates.

### Before vs after

| Target | Before |     After |
| ------ | -----: | --------: |
| ≥2x    |  54.4% | **49.5%** |
| ≥3x    |  35.9% | **30.1%** |
| ≥5x    |  22.3% | **17.2%** |

### Transferable lesson

> **Test suspicious constants and zero timestamps before computing the statistic.**

More importantly, measure how much of the **positive class** they supply.

---

# 6. P4 — The Confounder Wearing a Technical Label

A bot-family label initially looked like the strongest discriminator in the project.

### The symptom

The labelled tokens reached 100k:

**83.3% vs 53.3%**

Difference:

**+30.0 points**

Fisher exact:

**p = 0.0032**

Crude OR:

**4.38**

### The diagnosis

The label was strongly associated with entry market cap.

Median entry MC:

* labelled: **113,296**
* rest: **44,305**

Once stratified by entry MC:

| Entry MC     | Labelled |  Rest | Difference |
| ------------ | -------: | ----: | ---------: |
| Below median |    42.9% | 37.5% |    +5.4 pt |
| Above median |   100.0% | 92.3% |    +7.7 pt |

Mantel-Haenszel:

**OR = 1.22**

**p = 0.974**

The apparent effect disappeared.

### The correction

Categorical effects are now reported stratified by entry MC.

### Transferable lesson

> **A variable that predicts the outcome may simply be predicting the dominant covariate.**

---

# 7. P5 — Touched Is Not Cashed

## A peak is not an executable trade

Population B has:

**median peak = 1.87x detection MC**

and:

**46.3% reaching 2x**

That sounds interesting until a more basic question is asked:

> **Could the buyer actually have captured that price?**

### The diagnosis

On B:

* **43.8%** peak within 60 seconds of detection;
* **21.3%** peak before detection;
* median detection-to-peak delay = **2 minutes**.

The ATH is therefore a historical property of the token.

It is not a realised trading opportunity.

### The correction

Peak multiples are replaced by an executable round-trip model:

* entry = creation +120s;
* 0.5 SOL position;
* actual trade depth;
* 1% fee;
* 2% adverse slippage per leg;
* 5.8241% round-trip drag;
* unfilled exits = −100%.

### What survived

Across:

**196 executable tokens**

and:

**20 clusters / 6 days**

the result was:

* **0 / 10** policies positive in both mean and median;
* 38-policy sweep: **0 positive mean**;
* best mean: **−6.1%**.

The perfect-foresight oracle still produces:

**+27% median / +52.9% mean**

on the same corpus.

The value existed.

The question was whether anything observable at purchase time could locate it.

### Transferable lesson

> **Never substitute an extremum for an executable price.**

---

# 8. P6 — Instrumentation Can Silently Rewrite the Answer

Four independent instrumentation failures were found.

The important property they shared:

> **None initially looked like a software error.**

---

## P6a — Mixed Units

### The false result

At +1h:

**29.97x median**

**91.5% profitable**

At +24h:

**6.86x**

**88.4% profitable**

### The bug

Swap captures were expressed as:

**SOL / token**

while OHLCV data was:

**USD / token**

Every ratio was therefore multiplied by the SOL/USD exchange rate.

### The correction

Convert the entry price using SOL/USD at its own timestamp before calculating the return.

### Result

| Horizon | Incorrect |    Correct |
| ------- | --------: | ---------: |
| +1h     |    29.97x | **0.394x** |
| +2h     |    23.58x | **0.325x** |
| +4h     |    19.44x | **0.269x** |
| +24h    |     6.86x | **0.092x** |

The error factor had a median of:

**75.2**

The conclusion reversed completely.

---

## P6b — HTTP 403 Became “No Data”

The provider rejected the default Python User-Agent.

The fetch wrapper interpreted the failure as retryable and eventually returned `None`.

A transport failure therefore became an empty dataset.

### Correction

Transport errors now remain errors.

The fetch layer distinguishes:

* no data;
* forbidden;
* rate-limited;
* failed request.

---

## P6c — Provider History Was Mistaken for Full History

The provider caps results at approximately:

**1,000 candles**

Therefore:

* hourly = **41.6 days**
* minute = **16.7 hours**

A minute-level backtest over 20 days could therefore silently analyse only the final 16.7 hours.

### Correction

Every row records:

* candle count;
* actual time span;
* requested granularity.

---

## P6d — Running Maximum Was a Censored Outcome

A detector field stored a running maximum at the moment the row was written.

It was later compared with the true peak.

**41 / 103 rows = 39.8%**

were below the eventual true peak.

The field was therefore censored.

### Correction

The field is explicitly marked:

> **censored — never use as an outcome**

Mature outcomes are fetched independently.

### Transferable lesson

> **Instrumentation fails silently more often than it fails loudly.**

Assert units at boundaries.

Test transport with deliberate failures.

Record provider limits.

Treat incrementally written outcomes as censored until proven otherwise.

---

# 9. P7 — The Watchdog Was Watching the Wrong Thing

Two monitoring probes were wrong within one hour.

Neither raised an error.

### Failure 1 — Process detection

`pgrep -f` matched the monitoring shell itself.

The monitor was therefore watching an inert wrapper rather than the actual process.

### Failure 2 — Unsupported timestamp syntax

The local `find` implementation rejected the timestamp expression.

The command still returned exit status 0.

The monitor interpreted an error as:

> no recent files.

### Failure 3 — Existence ≠ Liveness

A process can retain its PID while being completely frozen.

That happened for two days.

### Correction

Liveness is now measured through deltas:

* CPU time;
* bytes written.

Both must stop before the watchdog raises an alarm.

### Failure 4 — Decorative health endpoints

A provider health endpoint could return “OK” even with an exhausted quota.

A health check that cannot return “unhealthy” is not a useful health check.

### Transferable lesson

> **Probes are production code.**

Test them with deliberate failures.

---

# 10. P8 — One Line of Missing-Data Policy Created Three Fake Winners

When an exit has no bid, several conventions are possible.

The simulator initially compared:

* hard: −100%;
* soft: remove the observation;
* unfilled: track separately.

### What happened

| Policy        |      Hard |       Soft |
| ------------- | --------: | ---------: |
| tp50 median   | **+3.3%** | **+31.5%** |
| time_10m mean |    −10.3% |  **+8.5%** |
| tp2x mean     |    −10.9% | **+10.5%** |
| tp2x median   |    −17.4% |  **+5.4%** |

Three policies switched from losing to apparently winning.

### Why

The missing exits were not random.

A token with no bid is likely to be dead.

Dropping it therefore removes exactly the worst outcomes.

### Correction

The canonical convention is:

**unfilled = −100%**

Sensitivity results remain published alongside the hard result.

### Transferable lesson

> **Dropping missing outcomes is a selection filter, not cleaning.**

---

# 11. P9 — Pricing the Lookahead

## The +14.7% strategy that disappeared when time became real

Entering 120 seconds after the price trough looked promising:

**+14.7% median**

**60.9% winners**

### The problem

You only know that a price was the trough after subsequent prices have already occurred.

That is future information.

### The correction

Build the exact live-safe mirror:

> Enter when the current bucket is the running minimum so far and the last closed bucket has recovered.

Same costs.

Same policies.

Same corpus.

| Rule                 |     Median |   Mean |
| -------------------- | ---------: | -----: |
| Retrospective trough | **+14.7%** |  +3.3% |
| Live-safe mirror     |  **−2.8%** | −12.9% |

The lookahead accounts for:

**17.5 percentage points of median performance.**

### Transferable lesson

> **Do not debate whether a strategy leaks. Build its zero-lookahead mirror.**

The performance difference is the measurable cost of the leak.

---

# 12. P10 — The Winner of 38 Tests Is Not a Normal Test

A sweep of 38 exit policies produced:

**best = +7.26%**

A plausible winner.

But the statistic selected was not:

> one policy

It was:

> **the best of 38 policies.**

### The correct null

Use:

* cluster-level sign-flip permutation;
* 5,000 draws;
* Westfall–Young max-T.

Results:

* raw p = **0.279**
* corrected p = **0.585**
* Bonferroni = **1.000**
* 5% max-null critical value = **+26.3%**

The observed +7.26% is below the level routinely generated by the maximum of noisy alternatives under the null.

### Transferable lesson

> **Test the statistic you actually selected.**

If you searched 38 times, your null must search 38 times too.

---

# 13. P11 — Missingness: What Disappeared?

## 352 captures did not fail randomly

The corpus contains:

**352 / 645 empty captures**

or:

**54.6%**

### Axis 1 — Time

Runs test:

**10 observed runs**

versus:

**320.8 expected**

**p = 0.0002**

Longest gaps:

* 168 consecutive empty captures / 4.7h
* 140 / 36.5h

These were outages.

### Axis 2 — Outcome

Using an independent outcome source:

|                | Empty | Non-empty |
| -------------- | ----: | --------: |
| P(multiple ≥2) | 49.1% |     50.7% |

Permutation:

**p = 0.77**

Median entry MC:

**47,897 vs 50,120**

**p = 0.21**

Missingness is therefore strongly time-clustered but not measurably outcome-dependent on the independent source.

### Axis 3 — The Trap

Using labels generated by the failing pipeline produced a large apparent difference.

That comparison was invalid.

The variable existed only when the pipeline succeeded.

It therefore measured coverage.

Not signal.

### Transferable lesson

> **When an instrument fails, test missingness against time, covariates and outcome — and measure the outcome independently of the failing instrument.**

---

# 14. P12 — Shared Infrastructure Fabricates Graph Structure

## The giant component that was mostly infrastructure

A co-occurrence graph produced:

**180 / 282 tokens**

inside one giant component.

That is:

**63.8%**

It looked like a vast coordinated network.

### The diagnosis

The most frequent addresses appeared on:

* 58.5%
* 35.1%
* 32.3%
* 24.8%
* 15.6%

of tokens.

Shared infrastructure can therefore connect otherwise unrelated launches.

### Correction

Remove high-ubiquity infrastructure.

The giant component falls to:

**48 / 282 = 17.0%**

A degree-preserving Chung–Lu null restricted within day also reproduced:

**1,502 / 6,024 qualifying pairs**

or:

**24.9% false positives**

### Important symmetry

The opposite error also occurred.

One address was classified as infrastructure because of ubiquity, although it was actually an operator sniping its own 51 launches.

Therefore:

> **Ubiquity is evidence of sharing, not proof of infrastructure.**

### Transferable lesson

> **A giant component is the default output of a co-occurrence graph.**

Remove hubs.

Preserve degree.

Preserve time.

Then interpret the remaining structure.

---

# 15. P13 — A Detector Needs Its Own Null

The funding detector used three criteria:

**A** — same funding transaction

**B** — same amount within one hour

**C** — shared private funder

The original detector treated:

```text
A OR B OR C
```

as the verdict.

### The problem

None of the three criteria had its own null distribution.

A “hit” therefore had no measured false-positive rate.

### The test

Using the control-wallet population:

**5,000 random groups** were generated.

| Criterion                    |   n=10 |   n=20 |      n=40 |
| ---------------------------- | -----: | -----: | --------: |
| A — same funding transaction | 0.0000 | 0.0000 |    0.0000 |
| B — same amount              | 0.0000 | 0.0000 |    0.0000 |
| C — shared private funder    |  0.151 |  0.461 | **0.889** |

Criterion C fires on:

**88.9%**

of random groups of 40.

Restricted to the subset where the test is admissible:

**99.5%**

### Why

Forty wallets create:

**780 possible pairs.**

With enough wallets drawn from a finite funding pool, shared funders become common even without coordination.

### Correction

Criterion C was retired.

The detector verdict is now based on A/B only.

### Transferable lesson

> **A detector cannot be stronger than the null distribution of its weakest criterion.**

“Rare on controls” is meaningless until you know how often the detector fires on random groups.

---

# 16. P14 — The Control Group Answered a Different Question

Even after removing criterion C, the detector appeared to separate targets from controls.

Original comparison:

**12/14 vs 1/9**

**p = 0.0007**

It looked strong.

It was not answering the intended question.

### The problem

All targets had graduated.

None of the original controls had.

The groups therefore differed in two dimensions:

1. the exposure being tested;
2. the outcome.

The control group was effectively:

> tokens that failed

while the targets were:

> tokens that succeeded.

### The correction

A second control group was constructed from pump.fun tokens that also graduated.

| Comparison                             | Targets | Controls |          p |
| -------------------------------------- | ------: | -------: | ---------: |
| Original verdict vs dead controls      |   12/14 |      1/9 | **0.0007** |
| A/B vs dead controls                   |    5/14 |      0/9 |     0.0595 |
| Original verdict vs graduated controls |   12/14 |     8/12 | **0.2478** |
| A/B vs graduated controls              |    5/14 |     3/12 | **0.4371** |

Two-thirds of the graduated controls carried the same signature.

The apparent effect was therefore associated with the outcome.

Not demonstrably with the exposure.

### Correction

No general claim of systematic coordination is made from this phase.

The individual observations remain observations.

The generalisation does not.

### Transferable lesson

> **A control group must differ from the target on the variable you are testing — not on the outcome itself.**

If targets succeeded and controls failed, a low p-value may simply be detecting success.

---

# 17. P15 — A Network Failure Can Look Like a Scientific Result

The scan of bonding-curve buyers returned:

**0 buyers across 14 tokens**

The output even looked internally consistent.

Curve transaction counts were correct:

**538, 391, 587...**

Only the buyer field was zero.

### The diagnosis

Three transport failures were found:

| Failure | Actual problem                                            | Apparent result                 |
| ------- | --------------------------------------------------------- | ------------------------------- |
| 1       | Batch decode endpoint returned HTTP 403                   | “No curve buyers”               |
| 2       | `rpc()` returned `None`; caller converted it with `or []` | “No transactions”               |
| 3       | Signature pagination hit HTTP 429                         | “Genesis reached, 0 signatures” |

The common failure pattern was:

```text
error
↓
falsy return value
↓
empty list
↓
"negative result"
```

### The contradiction

A graduated token has hundreds of curve transactions by definition.

A token reporting:

**587 curve transactions**

cannot simultaneously provide:

**0 curve buyers**

without an explanation.

A result that contradicts the definition of its own population is a bug until proven otherwise.

### Correction

Errors now raise.

Failed measurements are reported as:

```text
MEASUREMENT IMPOSSIBLE
```

with the HTTP status.

They are not counted as negative observations.

The final result became:

**3 / 9 measured**

**5 not measurable**

Less tidy.

Much more honest.

### Transferable lesson

> **Empty and failed are different measurements.**

A client that turns an error into `[]` can eventually turn an outage into a scientific conclusion.

---

# 18. What Did Not Reproduce

Three figures from internal notes could not be regenerated from the published dataset.

They are recorded here rather than silently removed.

## 18.1 “Peak 310k vs 48k, factor 6.4”

Recomputation gives factors between:

**2.55x and 4.39x**

depending on population.

The qualitative P1 failure reproduces.

The original pair of numbers does not.

---

## 18.2 “93% success manufactured by the buyable filter”

The 93% figure belongs to a different episode involving a second-wave concentration filter.

Its underlying data is not published here.

The reproducible `t_buyable` inflation is:

**69.8% vs 46.3%**

---

## 18.3 “67% peaked before detection”

The published populations give:

**16.9%–33.3%**

strictly before detection.

The operationally relevant within-60-second measure is:

**35.5%–43.8%**

The 67% figure is therefore not used.

---

# 19. What These Failures Taught Me

## 19.1 Audit definitions, not names

P1, P5 and P6d all involved variables whose names described their intended meaning while their formulas described something else.

The implementation wins over the label.

---

## 19.2 Turn methodological concerns into measurements

Instead of saying:

> “There may be lookahead.”

Measure:

> **17.5 points of median performance.**

Instead of saying:

> “The denominator may matter.”

Measure:

> **elasticity = 0.884.**

Instead of saying:

> “Multiple testing may be a problem.”

Measure:

> **max-null critical value = +26.3%.**

A methodological objection becomes substantially more useful once it has a measurable consequence.

---

## 19.3 Stratify on the dominant covariate

Here, entry market cap dominated many apparent categorical effects.

The crude effect can look enormous.

The adjusted effect can disappear completely.

---

## 19.4 Missing-data policy is part of the model

“Drop N/A” is not neutral.

Every missing value has a mechanism.

That mechanism needs to be measured.

---

## 19.5 Infrastructure is part of the measurement system

Units, APIs, provider limits, transport errors and censored fields changed results by:

* factors of approximately 75;
* effectively 100% of an apparent dataset in one failure mode;
* or 15 percentage points.

None initially produced an obvious error.

---

## 19.6 Monitoring deserves the same scepticism as analysis

Two monitoring probes were wrong on first use.

Both failed toward **false confidence**.

A monitoring system that reports “healthy” while its underlying process is frozen is itself a source of measurement error.

---

## 19.7 Null results are deliverables

Eleven of fifteen findings died under their own tests.

That is not a failure of the investigation.

**That is the investigation.**

The final conclusions became more defensible precisely because attractive explanations were repeatedly given opportunities to fail.

---

# Final Principle

> **Do not ask whether the data supports your hypothesis.**
>
> **Ask what could make the data appear to support it — and then try to prove that explanation wrong.**
