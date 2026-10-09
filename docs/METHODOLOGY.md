# Methodology

This chapter is the methodological contract of the repository.

The purpose is simple:

> **Every important claim should be traceable to a definition, a dataset, a measurement, and a validation procedure.**

The analysis is deliberately separated from the results. A result is only meaningful if its denominator, population, measurement and limitations are explicit.

This matters because many of the errors encountered during the investigation were not statistical errors. They were definition, sampling or instrumentation errors.

Of the fifteen issues documented in [`PITFALLS.md`](PITFALLS.md), nine were definition errors. The remaining issues involved null models, controls, transport failures and other parts of the measurement pipeline.

The methodology was therefore developed iteratively: when a measurement failed a test, the measurement was corrected, narrowed or removed.

---

# 0. At a glance

If you only have five minutes, read these sections:

1. **Definitions**
2. **Populations**
3. **Validation protocol**
4. **Limits**

Everything else documents the implementation in detail.

Every figure in the repository carries an evidence tag:

| Tag     | Meaning                                                                                                                |
| ------- | ---------------------------------------------------------------------------------------------------------------------- |
| **[R]** | Regenerated from `./code` + `./data`                                                                                   |
| **[P]** | Published in [`PITFALLS.md`](PITFALLS.md), regenerable with `python3 code/p0_pitfalls_check.py`                        |
| **[N]** | Taken from working notes whose underlying data is not published; treated as testimony, never as a verified measurement |

The scripts themselves use three evidence levels:

* `[MESURE]` — recomputed from published data
* `[INFERE]` — derived from measured data and explicitly flagged
* `[NON ETABLI]` — hypothesis or interpretation that is not established by the data

---

# 1. Core principles

The investigation follows six rules.

### 1. Define before measuring

Every important quantity has:

* a formula;
* a population;
* an implementation;
* and, where relevant, a rejected alternative.

A definition that has never been challenged is not considered sufficiently tested.

### 2. Separate observation from attribution

A blockchain address is an address.

It is not automatically a person, company or controlling entity.

The repository therefore distinguishes:

**Observed**

> Wallet A transferred X SOL to Wallet B.

from:

**Inferred**

> Wallet A and Wallet B may belong to the same operational cluster.

from:

**Not established**

> Wallet A and Wallet B belong to the same person.

The last claim requires evidence that this repository does not have.

### 3. Never hide the denominator

Every rate is reported with its population.

Where clustering matters, cluster count and day count are reported alongside `n`.

### 4. Attack the hypothesis

Competing explanations are actively tested.

A result is not considered strong merely because it is statistically significant.

### 5. Make missing data visible

Dropped observations are not silently removed.

The repository records:

* why an observation disappeared;
* whether the missingness is related to time;
* whether it appears related to the outcome;
* and how the missingness affects statistical power.

### 6. Reproduce before publishing

Published tables are expected to regenerate from the committed code and data.

When they do not, the result is not treated as a result.

---

# 2. Definitions

## 2.1 Launch / token

A launch is one pump.fun mint.

The time origin `t0` is the UNIX timestamp of the mint creation transaction.

All relative times are measured from `t0`, never from the first observation.

This prevents late-observed tokens from silently receiving a different time origin.

---

## 2.2 Bonding curve

The bonding curve is the pump.fun primary market.

At creation it holds approximately 99% of the supply.

A curve purchase is identified strictly in `v06_curve_ladder.py`:

* the curve account loses tokens;
* the signer gains those tokens.

The loose definition — "any transaction touching the mint" — was rejected because it includes AMM swaps, arbitrage and multi-leg routes.

---

## 2.3 Graduation

Graduation is the migration of liquidity from the bonding curve to an AMM pool.

It is identified through the pump.fun migration authority account.

This creates an on-chain sampling frame that does not depend on:

* a leaderboard;
* a screener;
* a frontend ranking;
* or later token performance.

The exhaustive graduation walk was performed by the collector; the frozen ≥$500k subset used for the analysis is committed as:

`data/v09_signature_gros_tokens.json`

---

## 2.4 Creation slot

The creation slot is the Solana slot containing the mint creation transaction.

Transactions inside the same slot have an ordering, but there is no external-observer time interval between them.

Therefore:

> **Same-slot is the strongest observable timing statement used in this investigation.**

It is **not** interpreted as proof of atomic execution.

---

# 3. Actors and behavioural signatures

## 3.1 Sniper

A sniper is an address appearing in the `snipers[]` list of a capture.

It means:

> **This address acquired the token before the observable market opened.**

It does not mean:

> This address belongs to a particular person.

Across the published corpus:

* median: **6 snipers per token**
* **282 / 293** tokens have a non-empty sniper list **[R]**

---

## 3.2 Creation-slot buyers

`v05_creation_block.py` identifies buyers committing at least **5 SOL** inside the creation slot.

The definition is deliberately identity-free.

The addresses are used to identify the behaviour of the block, not to decide beforehand which addresses "belong to the fleet".

This avoids circular reasoning.

---

## 3.3 Full-curve buyback / bundle snipe

The creation-slot signature was measured across **42 launches [R]**.

| Measurement                    |     Median |      Range |
| ------------------------------ | ---------: | ---------: |
| SOL committed in creation slot |   **85.2** |  79.5–87.5 |
| Supply acquired                |  **79.0%** | 76.8–79.3% |
| Buyers in block                |      **4** |        4–5 |
| Ticket dispersion (CV)         |  **0.027** |          — |
| Small buyers before block      | **0 / 42** |          — |

The independent frozen sample contains tokens that later reached ≥$500k:

**58 / 70 = 82.9%**

had their curve bought back for ≥60 SOL inside the creation slot.

Wilson 95% CI:

**[72.4%, 89.9%]**

This number has an important limitation:

the 70-token sample was selected because those tokens later reached ≥$500k.

Therefore it estimates:

> **P(signature | large)**

not:

> **P(large | signature)**

The sample was frozen on **2026-07-29**.

---

# 4. Wallet clusters and attribution

## 4.1 Fleet

A fleet is a group of addresses repeatedly co-occurring in creation-slot blocks across launches.

`m3_operators.py` tests:

* address counts;
* pairwise disjointness;
* co-occurrence;
* lift;
* statistical significance.

Fleet membership is therefore tested rather than assumed.

---

## 4.2 Shared infrastructure

Some addresses appear across a large fraction of launches and are treated as shared infrastructure rather than participants in a specific operation.

The five most ubiquitous addresses appear across:

**58.5%, 35.1%, 32.3%, 24.8%, 15.6%**

of the 282 tokens carrying sniper lists.

They are excluded from operator-link calculations.

For reproducibility, the addresses are referred to in prose as **W1–W9**.

One address contained a racial-slur vanity prefix and is therefore redacted consistently as `RDCT-<hash>`. Other public Solana addresses remain visible so that the measurements can be independently verified.

---

## 4.3 Operator cluster

An operator cluster means:

> **A group of launches sharing non-infrastructure fleet addresses.**

The analysis explicitly tests two competing explanations:

* `H_unique`: one entity
* `H_methode`: several entities using the same method

The evidence may support the second interpretation, but the repository does **not** claim:

* a common identity;
* a common owner;
* a common financier;
* or a specific intent.

A shared method is not the same thing as a shared owner.

---

# 5. Time model

| Variable         | Definition                                     |
| ---------------- | ---------------------------------------------- |
| `t0`             | Mint creation timestamp                        |
| `detect_ts`      | First external visibility, ≤12s after creation |
| Entry            | `t0 + 120s`                                    |
| Decision bucket  | 30s                                            |
| Fill horizon     | 120s                                           |
| `t_safe`         | Last observed swap − 120s                      |
| Capture window   | Graduation through +20 minutes                 |
| Long horizons    | +1h, +2h, +4h, +24h                            |
| Temporal cluster | Launches ≤30 minutes apart                     |
| Day              | UTC calendar day                               |

A rule triggered during bucket `k` is executed on bucket `k+1`.

It is never executed at the price that triggered it.

This prevents accidental lookahead.

---

# 6. Price and transaction measurements

## 6.1 Executed price

The executed price is:

`SOL / tokens`

using the actual swap execution.

Router fees are included in the SOL amount.

The pool's own price field is retained as a control.

---

## 6.2 Robust price

The robust price is the median executed price of swaps ≥0.3 SOL within a 30-second bucket.

There is no interpolation.

If no valid observation exists:

`None`

is propagated.

The definition was chosen because tiny swaps can generate absurd implied prices through unit rounding.

---

## 6.3 Exploitable swap

A swap is exploitable when:

```text
ts is present
tokens > 0
sol > 0
side ∈ {buy, sell}
```

The published corpus contains:

**511,508 raw rows**

→ **476,847 exploitable swaps**

→ **34,661 removed**

Of the removed rows:

* 34,659 had zero SOL;
* 2 had non-positive token amounts.

---

## 6.4 Market cap

Market cap is:

`price × 1e9`

The pump.fun launch constant is:

**27.96 SOL**

In the first observable instant:

* median market cap = **706 SOL**
* approximately **25.2×** the launch constant

---

## 6.5 Units

Unit consistency is treated as a major control.

Capture prices are:

**SOL per token**

while OHLCV prices are:

**USD per token**

Mixing the two can multiply ratios by approximately the SOL/USD price.

That error previously turned a −60% result into +2,900%.

The defence is permanent:

* units are declared in the shared library;
* every cross-source table prints a dimensional sanity ratio.

Measured sanity ratio:

**0.850 on n=277**

which is close to the expected value of 1.

---

# 7. Depth and execution assumptions

No order-book dataset exists for this venue.

Therefore depth is reconstructed from **executed trades**, not displayed liquidity.

The reconstructed book walks actual counterparties from the best price downward until a 0.5 SOL order is absorbed.

Minimum depth:

**0.05 SOL**

Strict variant:

**0.3 SOL**

This is conservative because displayed liquidity can be cancelled without executing.

---

# 8. Round-trip model

The round-trip calculation is:

```text
pnl =
(p_out × (1 - 0.02) × (1 - 0.01))
/
(p_in × (1 + 0.02) × (1 + 0.01))
- 1
```

This applies a total round-trip drag of:

**5.8241%**

The model uses a deliberately small:

**0.5 SOL position**

A larger position would generally increase market impact, so the reported result should not be interpreted as an optimistic claim about scalable execution.

Unfilled exits are scored:

**−100%**

Hard, soft and strict-book variants are all printed.

---

# 9. Targets

The repository uses three target families.

### Absolute targets

Primary:

* ATH ≥ 200k
* ATH ≥ 300k
* ATH ≥ 500k
* ATH ≥ 1M

### Residual target

`log10(ATH)` is residualised against `log10(entry MC)` within day.

The upper within-day tercile is then used as the binary target.

This deliberately removes entry market cap information from the target.

### Multiple

`ATH / entry MC`

is **never used as a primary target**.

The reason is mechanical:

the relationship between `log ATH` and `log entry MC` means that the multiple can appear predictive even when the underlying variable carries no additional information.

The repository therefore treats the multiple as a diagnostic, not as a primary prediction target.

---

# 10. Populations

Rates are never pooled across populations.

| Population    | Definition                                                   |     n | Clusters | Days |
| ------------- | ------------------------------------------------------------ | ----: | -------: | ---: |
| **A**         | Detector log, full-curve buyback ≥60 SOL                     |    93 |       34 |    3 |
| **B**         | Fast-graduation tokens with verified peak and sane MC regime | 1,243 |      123 |   20 |
| **C**         | Tokens with swap-level capture                               |   278 |        — |    7 |
| **Canonical** | Tokens where a 0.5 SOL round trip is executable at t0+120s   |   196 |       20 |    6 |

Before quality filters:

* `A_all` = 103
* `B_all` = 1,701
* `C_all` = 293

---

# 11. Attrition is part of the result

The gap between collected files and analysed observations is published.

```text
645 capture files
-352 empty captures
=293 non-empty captures

-3  swap span <120s
-1  no buy
=289 exploitable captures

-62 no robust entry price
-25 insufficient executable depth
-5 insufficient large-trade volume
-1 entry after capture end
=196 executable observations
```

The empty captures are not interpreted as market behaviour.

They were caused by silent upstream RPC failures.

The final capture corpus contains:

* **293 tokens**
* **476,847 exploitable swaps**
* **90,979 distinct addresses**
* **32 temporal clusters**
* **6.2 days**

---

# 12. Validation protocol

## 12.1 The token is not always the independent observation

Tokens launched within 30 minutes can share the same market regime.

Treating every token as independent can therefore inflate precision.

The repository consequently reports:

* `n`
* cluster count
* day count

and calculates headline means as:

> **mean of cluster means**

Confidence intervals for means are generated through cluster-level bootstrap.

Proportions use Wilson intervals.

Median intervals use the explicitly coded bootstrap engines documented in the repository.

---

# 13. Base rates and matched comparisons

Every rate is shown alongside the base rate of the same population.

Two rules are enforced.

### Rule 1

Any filter is compared against the unfiltered population.

This caught the `t_buyable` inflation:

**69.8% vs 46.3%**

### Rule 2

Availability is not compared across a variable that determines availability.

A capture pipeline can create an apparent signal simply by failing more often in one category.

Using an independent outcome source:

**49.1% vs 50.7%, permutation p=0.77**

The earlier apparent difference therefore measured coverage rather than market behaviour.

---

# 14. Multiple testing

When many rules are tested, the statistic selected is the maximum of those tests.

Its null distribution must therefore be the distribution of that maximum.

The repository uses:

* cluster-level sign-flip permutation;
* 5,000 draws;
* Westfall–Young max-T.

For the 38-policy sweep:

* best observed = **+7.26%**
* raw p = **0.279**
* max-T corrected p = **0.585**
* Bonferroni = **1.000**
* 5% max-null critical value = **+26.3%**

The conclusion is straightforward:

> The best observed rule was well inside the range that noise could routinely produce.

---

# 15. Out-of-sample validation

Most of the repository does **not** have a true holdout.

This limitation is explicit.

One strategy-like filter did receive a forward test.

It reached:

**93% in-sample on n=60**

then:

**53% forward on n=30**

with AUC falling:

**0.21 → 0.45**

That collapse is one of the most important results in the project.

It demonstrates why in-sample robustness is not treated as evidence of future validity.

The underlying data for those figures is not published, so they remain `[N]` testimony rather than verified repository measurements.

---

# 16. Live-safe mirrors

Any rule using a retrospective anchor is rebuilt as a zero-lookahead mirror.

Example:

A retrospective rule entering after the price trough produced:

**+14.7% median**

The live-safe mirror produced:

**−2.8%**

The measured lookahead contribution was:

**17.5 percentage points**

This is why:

> A decision made on bucket `k` is executed on bucket `k+1`.

A rule that cannot be expressed without future information is not published as a live rule.

---

# 17. Missing data

Missing data is treated as a hypothesis, not as an inconvenience.

Three rules apply:

1. State the convention.
2. Publish sensitivity.
3. Characterise missingness across time, covariates and outcome.

For example:

**352 / 645 captures were empty.**

A runs test produced:

**10 observed runs vs 320.8 expected**

with:

**p = 0.0002**

The losses were therefore strongly time-clustered and consistent with outages.

An independent outcome source gave:

**p = 0.77**

for an outcome difference.

The measured consequence is primarily:

> **loss of statistical power**

not demonstrated outcome bias.

---

# 18. Independent implementations and port control

The round-trip calculation was implemented in two independent engines.

Where they disagreed, the difference was diagnosed rather than averaged away.

One identified source of divergence was lookahead:

**+92.2% vs −58.2% on a single token**

from identical books when one engine contained a lookahead.

The more conservative engine became canonical.

The published implementation is then compared cell-by-cell against the frozen reference:

```text
python3 code/m5_roundtrip.py --reference ../docs/reference_canonical.json

cells compared:              30
maximum absolute deviation:  0.000002 percentage point
status:                      OK
```

---

# 19. Instrumentation checks

Checks are executed before interpreting the analysis.

### Dimensional sanity

Cross-source ratios must be approximately 1.

### Placeholder scan

Suspicious constants and zero timestamps are detected before rates are computed.

Ten contaminated rows supplied **24.3% of the positive ≥3x class** despite representing only 10% of rows.

They remain in the published dataset behind a named `poison_default` flag rather than being silently deleted.

### Censored fields

Incrementally written fields are treated as censored until proven otherwise.

### Transport probes

Collectors are tested against real failure conditions.

A provider returning HTTP 403 must not become an apparently valid empty dataset.

### Provider limits

OHLCV limits are recorded with each dataset.

### Liveness

A process ID is not considered proof that a collector is alive.

Liveness requires:

* CPU progress;
* and bytes written since the previous check.

---

# 20. Graph analysis

Wallet co-occurrence graphs naturally create giant components.

Therefore a giant component is **not** considered evidence by itself.

Two controls are mandatory.

## Hub removal

For edges requiring ≥3 shared snipers:

| Exclusion                       | Giant component | Share |
| ------------------------------- | --------------: | ----: |
| None                            |             180 | 63.8% |
| Declared infrastructure         |              57 | 20.2% |
| All addresses present ≥14 times |              48 | 17.0% |

The sensitivity is published because the result depends on the hub policy.

---

## Degree-preserving null

A Chung–Lu null model was also used while preserving day structure.

The null reproduced:

**1,502 / 6,024 qualifying pairs**

or:

**24.9% false positives**

The giant component under the null was:

**564**

versus:

**668 observed**

A day-blind null previously produced apparently significant clusters.

Preserving the day structure removed them.

This established an important control:

> **Time is a confounder in co-launch graphs.**

---

# 21. Detector-specific null models

The same principle applies to individual detectors.

The phase-1 funding detector used three criteria:

* same funding transaction;
* same amount within one hour;
* shared private funder.

Each criterion received its own null distribution using control wallets exposed to the exact same detector.

| Criterion                   | False-positive rate on random group of 40 |
| --------------------------- | ----------------------------------------: |
| Same funding transaction    |                                **0.0000** |
| Same amount within one hour |                                **0.0000** |
| Shared private funder       |                                 **0.889** |

The third criterion was therefore retired.

The rule is now permanent:

> **No criterion enters a verdict before its own false-positive rate has been measured.**

---

# 22. Reproducibility

Published measurements are designed to run offline.

The published analysis uses the Python standard library for the measurement layer.

Network-dependent components are limited to:

* SOL/USD fetching;
* OHLCV fetching;
* on-chain verification.

Their outputs are committed so that published tables remain reproducible offline.

Additional controls:

* deterministic randomness;
* fixed seeds;
* one command per table;
* published data reduction;
* SHA-256 manifest;
* byte-level result comparison;
* CI regeneration on every push.

The repository therefore aims for:

> **same data + same code = same result**

An earlier CI check caught a stale T5 result at `n=18`. It was regenerated, and the current result is protected by the byte-comparison check.

---

# 23. What each major claim had to survive

| Claim                                    | Population        | Cluster CI          | Multiplicity | MC stratification | Lookahead | Out-of-sample  |
| ---------------------------------------- | ----------------- | ------------------- | ------------ | ----------------- | --------- | -------------- |
| No exit policy profitable in expectation | Canonical         | Yes                 | —            | —                 | —         | No             |
| No post-snipe entry rule reaches 1x      | Canonical         | Yes                 | —            | —                 | Yes       | No             |
| Value decays over 1–24h                  | 191 / 27 clusters | Yes                 | —            | —                 | —         | No             |
| Peak already past at first visibility    | B                 | Wilson              | —            | Yes               | —         | Descriptive    |
| Multiple is a denominator artefact       | A/B/C             | —                   | —            | Yes               | —         | Replicated     |
| Creation-slot signature                  | 42 / 70 frozen    | Wilson              | —            | —                 | —         | No             |
| Fleets are distinct, method is shared    | 282 tokens        | Co-occurrence tests | —            | —                 | —         | Attacked twice |

This table is deliberately less impressive than a table showing only positive findings.

That is the point.

---

# 24. Limits

## 24.1 Time window

The main capture corpus covers:

**2026-06-27 → 2026-07-04**

Population B extends through:

**2026-07-18**

The repository does not claim that the observed behaviour is a permanent law of Solana.

Memecoin microstructure can change over weeks.

---

## 24.2 Coverage

End-to-end coverage is approximately:

**6.8%**

within the measured pipeline.

Within the capture window:

**278 / 805 eligible tokens = 34.5%**

The system is therefore partially observed.

It is described as such.

---

## 24.3 Selection bias

The collector observes detected tokens rather than every launch.

Captured tokens therefore over-sample tokens that moved.

Measured:

**32.7% vs 28.3%**

for the ≥200k peak outcome.

This is a **+4.5 percentage-point selection difference**.

The direction of this bias would make buying appear less unprofitable than it actually is.

The repository therefore does not hide the bias.

---

## 24.4 Effective sample size

Nominal sample sizes can be misleading.

The canonical corpus contains:

* **196 tokens**
* **20 clusters**
* **6 days**
* Kish effective n = **5.5**

One day supplies 70 of the 196 observations.

The correct interpretation is therefore closer to:

> "approximately six effective independent observations"

than:

> "196 independent observations."

---

## 24.5 Missing data

**352 / 645 captures are empty.**

The missingness is strongly time-clustered.

The repository therefore treats it primarily as a power problem.

It does not claim that outage windows were unrelated to unusual market conditions because that question was not directly measured.

---

# 25. What is explicitly NOT established

This section is intentionally blunt.

The repository does **not** establish:

### Identity or intent

No person is identified from a wallet address.

No intent is inferred from transaction behaviour.

### A single controlling entity

The evidence is compatible with several operators using the same method.

A shared software fingerprint does not establish a shared owner.

### A shared upstream financier

The corpus does not contain sufficient upstream funding information to establish this.

### Atomic execution

Same-slot transactions are not described as atomic.

Each buyer signs its own transaction.

There is:

**0 / 42 transaction duplication**

in the measured launches.

### A historical date for the market transition

The graduation walk does not contain sufficient historical depth to date a "sequential → bundled" transition.

### Operator skill

The analysis does not establish that one identified operator is more skilled than another.

### Live parity of all features

Offline and live feature provenance is not identical.

The repository explicitly records this limitation rather than pretending otherwise.

---

# 26. Figures that did not reproduce

Three figures from working notes could not be reproduced from the published data.

They are therefore **not used as results**:

* an ATH ratio of 6.4x;
* "67% of tokens peaked before detection";
* "93% manufactured by the buyable filter".

The recomputed values differ materially.

They remain documented in [`PITFALLS.md`](PITFALLS.md#what-did-not-reproduce) because deleting an inconvenient number without documenting why it disappeared would make the research less auditable.

The rule is simple:

> **If another analyst cannot reproduce it from the published evidence, it is not a measured result.**

---

# 27. Scope, data and ethics

This repository studies the microstructure of a public blockchain market.

It is descriptive research.

It is **not**:

* investment advice;
* execution tooling;
* a trading recommendation;
* a system designed to trade automatically.

Solana addresses are public on-chain identifiers.

Third-party addresses are not linked to people, names or intent.

No private keys, API keys, tokens, `.env` files or session material are published.

The author's own KYC'd exchange deposit address is deliberately self-attributed in the repository to make the financial reconstruction independently verifiable.

Published datasets are reduced according to:

`data/MANIFEST.json`

with SHA-256 hashes and documented transformations.

---

# 28. Reproduction

The main measurements can be regenerated with:

```bash
python3 code/m1_corpus.py
```

```bash
python3 code/m5_roundtrip.py
```

```bash
python3 code/m5_roundtrip.py \
  --reference ../docs/reference_canonical.json
```

```bash
python3 code/m4_infra_ubiquity.py
```

```bash
python3 code/p0_pitfalls_check.py
```

```bash
python3 code/t1_base_rate_sorties.py
```

```bash
python3 code/t2_x2_par_prix_entree.py
```

```bash
python3 code/t3_ath_avant_detection.py
```

```bash
python3 code/t4_entree_post_snipe_20min.py
```

Network-dependent measurements:

```bash
python3 code/fetch_sol_usd.py
python3 code/fetch_gt_ohlcv.py
python3 code/t5_horizon_1h_24h.py
```

The generated tables identify their own reproduction command.

---

# Final principle

The methodology can be reduced to one sentence:

> **Observe the chain, define the measurement, try to break the explanation, publish the limitation, and only then state what the data supports.**

That is the standard this repository is built around.
