# Blockchain Investigation Framework

This document describes the investigation framework used throughout this repository.

It is not a theoretical AML checklist and it is not a description of a particular case. It is the working method used to move from raw on-chain observations to a documented, reproducible conclusion.

The central principle is simple:

> **Observe first. Trace second. Test alternatives third. Attribute only what the evidence supports.**

The investigation is designed to distinguish four different things that are often incorrectly collapsed into one:

1. **What happened on-chain.**
2. **What mechanism can explain the observation.**
3. **What pattern is statistically or operationally unusual.**
4. **What, if anything, can be attributed to a specific actor, identity, intent, or strategy.**

The fourth does not follow automatically from the first three.

---

# 1. Investigation Question

Every investigation starts with a concrete question.

Examples from this repository include:

* How was a token's bonding curve acquired?
* Did the observed buyers receive funding before the launch?
* Were several fresh wallets funded through the same mechanism?
* Does the same execution structure recur across launches?
* Could the observed clustering arise from shared infrastructure or random co-occurrence?
* Does an apparent trading advantage survive execution costs, lookahead controls, and out-of-sample testing?

The question determines the population and the evidence required.

A detector should not define its own outcome.

For example, filtering tokens to those that eventually reached a target multiple and then asking whether they were profitable introduces selection on the outcome. The repository therefore separates:

**detection → measurement → outcome evaluation**

rather than defining the population from the result.

---

# 2. Define the Population Before Measuring It

A result is only meaningful relative to its population.

For each analysis, the investigation records:

* observation window;
* timezone;
* token population;
* inclusion criteria;
* exclusion criteria;
* capture mechanism;
* measurement availability;
* cluster definition;
* missing-data treatment.

Where relevant, populations are explicitly separated.

Examples include:

* the full detector log;
* fast-graduation launches;
* tokens with verified peak data;
* tokens with swap-level capture;
* creation-slot reconstructed launches;
* tokens for which an executable round trip can actually be simulated.

This prevents a convenient subset from becoming an implicit definition of the market.

---

# 3. Preserve the Raw Observation

The first step is to preserve what the chain actually shows.

The investigation does not begin with an interpretation such as:

> "These wallets are controlled by the same operator."

It begins with observations such as:

* wallet A received X SOL;
* wallet B received X SOL;
* both transactions occurred within Y seconds;
* both wallets were created shortly before funding;
* both wallets subsequently bought the same token;
* the transactions occurred before token creation.

These observations can then be tested.

The distinction is important because:

> **A transaction relationship is evidence of a transaction relationship, not automatically evidence of common ownership.**

---

# 4. Entity and Wallet Resolution

Wallets are treated as technical entities first.

For each address, the investigation may examine:

* first observed activity;
* account creation or activation;
* transaction history;
* funding sources;
* downstream transfers;
* token purchases;
* token sales;
* recurrence across launches;
* shared infrastructure;
* temporal relationships.

Wallet age is measured from observable chain activity rather than assumed identity.

The repository uses terms such as:

* `fresh wallet`;
* `disposable wallet`;
* `fleet wallet`;
* `cluster member`;
* `infrastructure address`.

These are analytical categories, not claims about legal or human identity.

For example, a wallet that was first active shortly before receiving launch capital can be classified as *fresh* without claiming who created it.

---

# 5. Trace the Funds

When the question concerns funding, the investigation follows the money rather than stopping at the first transfer.

A typical trace is:

```text
source
   ↓
gateway / distributor
   ↓
fresh wallet
   ↓
token purchase
   ↓
secondary wallet / liquidation
```

Each edge is treated as a separate observation.

The investigation attempts to establish:

* chronology;
* transaction relationship;
* amount;
* recurrence;
* destination;
* upstream origin where measurable;
* downstream behaviour where measurable.

A funding relationship is only considered pre-launch funding when the chronology actually supports it.

A wallet receiving funds after the relevant token launch cannot be used as evidence that those funds financed the launch.

This chronological constraint eliminated several superficially plausible relationships in the historical investigation.

---

# 6. Reach the Genesis of the Flow

A funding source should not be treated as an unexplained origin merely because the first implementation of the scanner stopped there.

Historical traces therefore use paginated transaction history where available.

The repository explicitly distinguishes:

* **genesis reached**;
* **history read but genesis not reached**;
* **history censored by a provider or configured limit**;
* **measurement impossible because of transport failure**.

These states are not interchangeable.

A bounded history can support:

> "No earlier funding was observed within the measured range."

It cannot support:

> "This wallet had no earlier funding."

That distinction is especially important in forensic work.

---

# 7. Detect Repeated Structures

Once individual transactions are reconstructed, repeated structures can be searched for.

The investigation uses several types of signal.

### Funding transaction

Several recipients receive funds from the same transaction.

### Amount similarity

Several wallets receive the same or near-identical amount.

### Temporal proximity

Funding events occur within a defined time window.

### Wallet freshness

Recipients were created or first became active shortly before funding.

### Launch proximity

Funding precedes the relevant token creation or purchase.

### Cross-token recurrence

The same mechanism appears around more than one token.

A candidate pattern becomes substantially stronger when several independent properties coincide.

For example:

```text
fresh wallet
+
same funding transaction
+
same amount
+
short time interval
+
pre-launch chronology
+
subsequent purchase
```

is materially different from:

```text
two wallets share a funder
```

The latter was tested as a null model in this repository and produced high false-positive rates in random groups. It was therefore retired as a standalone coordination criterion.

---

# 8. Separate Detection From Attribution

A detected structure does not automatically identify an operator.

The repository deliberately distinguishes:

### Direct observation

> Four wallets received 3.000000000 SOL each from the same transaction.

### Mechanistic inference

> The transaction is consistent with a coordinated funding distribution.

### Stronger repeated evidence

> The same funding mechanism and amount structure recur across launches.

### Attribution

> The wallets belong to the same person or organization.

The first three can be supported by on-chain evidence.

The fourth requires additional evidence.

The investigation therefore does **not** treat:

* shared funding;
* shared gateway;
* identical ticket sizes;
* common software characteristics;
* graph connectivity;
* repeated wallet reuse;

as sufficient proof of human identity.

The strongest conclusion may be that a **shared execution mechanism or infrastructure pattern is observable**, while the operator remains unidentified.

---

# 9. Build Null Models

An unusual-looking structure is not necessarily unusual.

Before treating a detector as meaningful, the investigation asks:

> **How often would this criterion fire if the wallets were unrelated under the relevant null?**

This is implemented through randomization and control populations.

The Phase 1 investigation provides a concrete example.

Three criteria were tested:

* **A:** wallets funded in the same transaction;
* **B:** several wallets receiving approximately equal amounts within a defined time window;
* **C:** wallets sharing a private funder.

Across 5,000 random groups:

| Criterion |   n=10 |   n=20 |   n=40 |
| --------- | -----: | -----: | -----: |
| A         | 0.0000 | 0.0000 | 0.0000 |
| B         | 0.0000 | 0.0000 | 0.0000 |
| C         |  0.151 |  0.461 |  0.889 |

Criterion C was therefore retired.

The important lesson is:

> **A detector is not validated because it finds the target. It is validated by measuring how often it finds non-targets.**

---

# 10. Use Appropriate Controls

Controls should resemble the target population in the dimensions that can confound the result.

A control consisting entirely of failed launches cannot establish that a target pattern predicts success if every target launch succeeded.

This occurred in the historical Phase 1 analysis.

The original comparison produced:

* target: 12/14;
* dead controls: 1/9;
* Fisher p = 0.0007.

But the targets were systematically selected from successful launches while the dead controls were not.

When graduated controls were used instead:

* target: 12/14;
* graduated controls: 8/12;
* p = 0.2478.

Using only the retained A/B criteria:

* target: 5/14;
* graduated controls: 3/12;
* p = 0.4371.

The mechanism remained observable in individual cases.

The generalized claim did not survive the appropriate control.

That distinction is a core part of the investigation.

---

# 11. Attack the Hypothesis

Every important conclusion should have an attempted failure mode.

The repository therefore maintains explicit methodological attacks in `docs/PITFALLS.md`.

Examples include:

* selection on outcome;
* denominator artefacts;
* silent default values;
* confounding;
* touched-versus-cashed outcomes;
* instrumentation errors;
* watchdog failures;
* missing exits;
* lookahead;
* multiple testing;
* missingness;
* shared infrastructure;
* detector nulls;
* inappropriate controls;
* transport failures.

The objective is not to protect the original hypothesis.

It is to discover which parts of it remain after the obvious alternative explanations have been removed.

---

# 12. Treat Missing Data as Evidence About Measurement, Not the Outcome

A failed measurement is not automatically a negative observation.

The investigation distinguishes:

```text
positive
negative
empty
unmeasurable
transport failure
censored
```

For example:

```text
HTTP 403
→ not "zero buyers"

HTTP 429
→ not "no funding"

provider history cap
→ not "wallet had no earlier activity"
```

This rule became necessary after transport failures were converted into empty arrays and subsequently interpreted as negative findings.

One reconstructed investigation originally appeared to show:

> 0 buyers across 14 tokens.

After correcting the data path, the result became:

> **3 / 9 measured**
> **5 not measurable**

The latter is less convenient.

It is also the defensible measurement.

---

# 13. Control for Shared Infrastructure

Graph connectivity is particularly vulnerable to infrastructure effects.

A group of wallets may appear highly connected because they all interact with:

* a common service;
* a common funding source;
* a common execution tool;
* a shared infrastructure address.

The repository therefore tests graph structure after removing or controlling for high-ubiquity addresses and temporal co-occurrence.

In the main corpus:

* the initial giant component contained 180/282 tokens, or 63.8%;
* after removing nine infrastructure addresses it fell to 57/282, or 20.2%.

A time-preserving null also generated substantial false-positive connectivity.

The lesson is:

> **Graph connectivity is an observation. It is not, by itself, an operator map.**

---

# 14. Validate Chronology

Chronology is a hard constraint in forensic reconstruction.

The investigation checks relationships in temporal order:

```text
funding
    ↓
wallet creation / activation
    ↓
token creation
    ↓
purchase
    ↓
subsequent activity
```

A relationship that occurs in the wrong order is not treated as causal funding evidence.

This eliminated examples where a wallet bought two tokens but the gateway funding occurred after both launches.

The wallets were linked as buyers.

They were not linked by that funding event as a pre-launch mechanism.

---

# 15. Reconstruct the Launch Mechanism

For launch analysis, the investigation goes below the level of token-level statistics.

Selected launches are reconstructed transaction by transaction.

The creation-slot analysis examined 42 launches and measured:

* median 85.21 SOL committed;
* median 78.95% of supply acquired;
* 0 curve purchases before the creation block;
* 0-second / 0-slot intra-core gap in all 42 launches;
* median transfer delay of approximately 17.5 seconds;
* launch market cap of approximately $2,158;
* AMM-open market cap of approximately $53,985.

The purpose is not simply to show a large number.

It is to reconstruct **how the number happened**.

That distinction turns an aggregate observation into a mechanism-level investigation.

---

# 16. Separate Mechanism From Economic Outcome

A mechanism can be real without being exploitable.

The repository therefore treats these as separate questions:

### Mechanism

Did the observable execution structure occur?

### Timing

Could an external observer have detected it before the relevant market move?

### Execution

Could an observer have executed after detection?

### Economics

Did the resulting position have positive expected or realized performance after realistic costs?

The 2026 testing found:

* 15 tested exit policies;
* 15/15 negative mean;
* 12/15 negative median;
* 0/15 bootstrap confidence intervals above zero;
* +1h median multiple of 0.48×;
* +24h median multiple of 0.20×.

This does not establish that every possible trading strategy fails.

It establishes that the tested policies did not demonstrate a positive result under the declared methodology.

---

# 17. Correct for Lookahead

Historical data can make an investigation appear dramatically better than it would have been live.

For example:

> detect the launch → identify the eventual trough → enter at the trough

is not a live strategy.

The repository therefore distinguishes retrospective measurements from live-safe measurements.

Where a future event is used to define an entry or exit, it is treated as lookahead unless the information would have been available at that timestamp.

This principle applies to:

* entry price;
* exit price;
* peak;
* trough;
* token classification;
* control selection;
* operator ranking.

---

# 18. Control the Denominator

Ratios can manufacture apparent signals.

The repository found:

```text
log10(peak MC) ~ log10(entry MC)
slope = 0.884
```

Therefore:

```text
log10(multiple)
=
log10(peak)
-
log10(entry)
```

has an expected slope of approximately:

```text
0.884 - 1 = -0.116
```

The measured value was:

```text
-0.1263
```

The resulting apparent relationship between entry market cap and multiple was therefore substantially driven by the denominator.

After constructing a residual target that removes the within-day entry-market-cap relationship:

```text
Spearman(entry MC, residual) = +0.048
```

The investigation consequently reports both absolute outcomes and denominator-controlled outcomes where relevant.

---

# 19. Record Corrections Instead of Hiding Them

A forensic repository should preserve failed measurements.

This repository explicitly records figures that did not reproduce.

Examples include:

* the earlier ×6.4 selection-bias factor, replaced by population-dependent values of approximately ×2.55–×4.39;
* the unreproduced 93% success figure, replaced by the reproducible 69.8% versus 46.3% selection inflation;
* the earlier 67% "peaked before detection" claim, replaced by the published population-specific measurements;
* the earlier 476,847 swap count alongside the raw recount of 511,508;
* the earlier AMM-open estimate of $46,147, replaced by the authoritative $53,985 measurement.

A correction is not a weakness in the investigation.

It is part of the audit trail.

---

# 20. Confidence and Evidence Boundaries

Every conclusion should be classified according to what the evidence actually establishes.

A useful hierarchy is:

### Directly observed

The transaction, timestamp, amount, wallet relationship, or market measurement is directly present in the data.

### Reconstructed

The event is derived deterministically from multiple on-chain observations.

### Supported inference

Several independent observations support a mechanistic interpretation.

### Not established

The available evidence is insufficient to support the stronger claim.

For example:

**Established**

> Several fresh wallets received repeated near-identical funding amounts before selected launches.

**Supported**

> The pattern is consistent with a repeatable funding/execution mechanism.

**Not established**

> All such wallets belong to one operator.

**Not established**

> The gateway service was aware of or responsible for the downstream activity.

**Not established**

> The pattern identifies a specific person or organization.

The distinction should remain explicit in the final report.

---

# 21. Reproducibility

A finding is not considered complete until another analyst can understand how it was produced.

Each major measurement should expose:

```text
Input
↓
Transformation
↓
Output
↓
Validation
```

Where possible, scripts are deterministic and run without network access once the required data has been cached.

Examples include:

```bash
python3 code/a1_null_model.py
python3 code/a2_recount.py
python3 code/a3_hub_origin.py
python3 code/a4_selection_bias.py

python3 code/f_figures_resultats.py
python3 code/t1_base_rate_sorties.py
python3 code/t3_ath_avant_detection.py
python3 code/t4_entree_post_snipe_20min.py
python3 code/t5_horizon_1h_24h.py
```

The repository's broader runner can also execute the offline analysis suite and verify regenerated tables and JSON outputs against committed artefacts.

Reproducibility is treated as part of the evidence, not as documentation added afterward.

---

# 22. Investigation Output

A finished investigation should answer five questions.

## What happened?

A concise description of the directly observed behaviour.

## How do we know?

The transactions, measurements, population and methodology supporting the observation.

## What alternative explanations were tested?

Controls, null models, infrastructure effects, missingness, lookahead and other relevant failure modes.

## What survives?

Only the claims that remain after those tests.

## What remains unknown?

Identity, intent, causality, prevalence, generalization, or profitability where the evidence does not establish them.

---

# 23. The Investigation Template

For a new case, the working structure is:

```text
# Investigation

## 1. Question

What are we trying to establish?

## 2. Scope

Time window:
Population:
Data sources:

## 3. Direct Observations

What does the chain actually show?

## 4. Entity Resolution

Which wallets, transactions, contracts or addresses are involved?

## 5. Fund Flow

Where did the assets come from and where did they go?

## 6. Chronology

What happened before, during and after the event?

## 7. Pattern Detection

What repeated structure is observable?

## 8. Alternative Explanations

What else could produce the same observation?

## 9. Controls / Null Model

How often does the detector fire outside the target?

## 10. Validation

Which findings survive?

## 11. Attribution Boundary

What can and cannot be attributed?

## 12. Confidence

Direct observation:
Reconstructed:
Supported inference:
Not established:

## 13. Reproduction

Which scripts and artefacts reproduce the result?

## 14. Conclusion

What is the narrowest defensible conclusion?
```

---

# 24. Operating Principle

The purpose of this framework is not to produce the most dramatic interpretation of an on-chain pattern.

It is to produce the **strongest conclusion that survives attempts to invalidate it**.

The workflow is therefore:

```text
Question
   ↓
Define population
   ↓
Collect raw evidence
   ↓
Reconstruct transactions
   ↓
Trace funds
   ↓
Validate chronology
   ↓
Detect repeated structures
   ↓
Build controls / null models
   ↓
Attack alternative explanations
   ↓
Correct measurement failures
   ↓
Separate observation from attribution
   ↓
Reproduce
   ↓
State the narrowest defensible conclusion
```

The final rule is:

> **Do not ask only whether the data supports the hypothesis.**
>
> **Ask what else could have produced the same observation — and try to make the hypothesis fail.**

That is the standard used throughout this repository.
