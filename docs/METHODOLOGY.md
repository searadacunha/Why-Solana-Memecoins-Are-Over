# Methodology

**What this chapter is.** The contract between the numbers in this repository and the reader: what
every term means as a formula, which population each rate is computed on, which validation procedure
a claim had to survive to be published, and where the whole thing stops being valid.

It is deliberately separate from the results. A result is only as good as the definition of its
denominator, and definitions are where this corpus hides its traps — nine of the fifteen episodes in
[PITFALLS.md](PITFALLS.md) were definition errors, not statistical ones. The three cards added since
that count (P13 a missing null distribution, P14 a confounded control group, P15 a transport failure)
are statistical or instrumentation errors, so the definition-error count stays nine while the total
moves to fifteen.

**Five-minute path.** Read [§0 Conventions at a glance](#0-conventions-at-a-glance), then
[§3.1 The unit of analysis is not the token](#31-the-unit-of-analysis-is-not-the-token), then
[§5 Limits](#5-limits). Everything else is reference material.

**Provenance marking.** Every figure below carries its source:

| tag | meaning |
|---|---|
| **[R]** | regenerated from `./code` + `./data` during this write-up; the command is given |
| **[P]** | published in [PITFALLS.md](PITFALLS.md), regenerable via `python3 code/p0_pitfalls_check.py` |
| **[N]** | from working notes whose underlying data is **not** in this repository; quoted as testimony, never as a verified figure |

The three evidence levels used inside the scripts' own output are `[MESURE]` (recomputed from
published data), `[INFERE]` (derived, flagged as such), `[NON ETABLI]` (hypothesis, never quoted as a
fact). They appear verbatim in every console output.

---

## 0. Conventions at a glance

| quantity | convention | value | where |
|---|---|---|---|
| price of an instant | median executed price of swaps >= 0.3 SOL in a 30 s bucket | — | `pumplib.robust_series` |
| decision grid | 30 s buckets; a decision taken on bucket *k* executes on bucket *k+1* | 30 s | `m5_roundtrip.py` X3, X10 |
| entry time | creation + 120 s (sensitivity: +300 s) | 120 s | X1 |
| position size | 0.5 SOL | 0.5 SOL | X11 |
| costs | 1 % fee + 2 % adverse slippage **per leg** | round-trip drag **5.8241 %** | X8 |
| unfilled exit | scored **-100 %** (hard convention); soft and strict-book variants printed alongside | — | X12 |
| last creditable exit | `t_safe` = last observed swap - 120 s | — | X9 |
| resampling unit | temporal cluster: launches less than 30 min apart | 1800 s | `pumplib.clusters` |
| units | capture prices are **SOL per token**; OHLCV prices are **USD per token** | factor ~75 | `common.py` header |
| launch market cap | pump.fun bonding-curve constant | **27.96 SOL** | `pumplib.LAUNCH_MC_SOL` |
| supply | constant | 1e9 | `pumplib.PUMP_SUPPLY` |
| primary target | absolute (`ATH >= X`) and residual (`log ATH` net of `log MC`) | — | `dataset_socle.json:meta.notes` |
| forbidden target | any multiple `ATH / entry MC` as a **primary** target | — | idem |

---

## 1. Definitions

Each definition states the formula, the file that implements it, and — where it matters — the naive
alternative that was rejected and why. A definition without a rejected alternative is usually a
definition nobody stress-tested.

### 1.1 Objects

**Launch / token.** One pump.fun mint. Time origin `t0` = `created`, the UNIX timestamp of the mint
creation transaction. Every relative time in this repository is measured from `t0`, never from the
first observation, so that tokens observed late are not silently re-based.

**Bonding curve.** The pump.fun primary market: a deterministic price ladder holding ~99 % of the
supply at creation. Buying on the curve moves the price up the ladder; there is no counterparty and
no order book. A curve purchase is identified **strictly**: a transaction in which the curve account
(the account that received ~99 % of the supply in the creation transaction) *loses* tokens and the
signer *gains* them (`v06_curve_ladder.py`). The loose alternative — "any transaction touching the
mint" — was rejected: it admits AMM swaps, arbitrage and multi-leg routes, which polluted an earlier
version of the measurement.

**Graduation.** The migration of liquidity from the bonding curve to an AMM pool, executed through
the pump.fun migration authority account. It is the moment the token becomes buyable by an ordinary
observer through a normal DEX route. Graduation events are enumerable exhaustively by walking the
signatures of that single account -- a survivorship-free sampling frame, because it is an on-chain
event that persists whatever the token later becomes, unlike any screener, leaderboard or frontend
API ranking. That exhaustive walk was performed in the unpublished collector, not by a script in
this repository; the frozen >= 500 k USD subset it produced is committed as
`data/v09_signature_gros_tokens.json` (see 1.2, "Full-curve buyback").

**Creation slot.** The Solana slot containing the mint creation transaction. Same-slot means same
block: transactions in one slot are ordered by index but are not separated by any interval an
external observer could act in. "Same slot" is therefore the strongest observable statement about
timing available on this chain — and notably **not** a statement about atomicity (see §5.7).

**AMM pool / observable market.** The post-graduation venue. The swap corpus in `./data` records this
venue only. Purchases made on the bonding curve before graduation are **not** in the swap stream;
they appear in the `snipers[]` field of each capture. That asymmetry is the subject of the project,
not an accident of collection.

### 1.2 Actors

**Sniper.** An address in the `snipers[]` list of a capture: an address that acquired the token
before the observable market opened. It is an *observation about an address*, never about a person.
Median 6 snipers per token, 282 of 293 tokens carry a non-empty list **[R]**.

**Purchase block of the creation slot.** In `v05_creation_block.py`, the set of buyers of >= 5 SOL
inside the creation slot, whoever they are. This definition is deliberately **identity-free**: the
fleet addresses are used only to *select* which launches to look at, never to decide who counts as a
member. That removes the circularity of "we found the fleet's wallets in the block we selected
because the fleet's wallets were in it", and it caught two launches where a stand-in wallet had
replaced a regular one.

**Full-curve buyback (the "bundle snipe").** The observable signature, measured on 42 launches
**[R]** (`data/v05_creation_block.json`):

| measurement | median | range |
|---|---|---|
| SOL committed in the creation slot | **85.2** | 79.5 - 87.5 |
| share of the 1e9 supply acquired | **79.0 %** | 76.8 - 79.3 % |
| buyers in the block | 4 | 4 (33 cases) or 5 (9 cases) |
| intra-block ticket dispersion (CV) | 0.027 | — |
| small buyers *before* the block | **0 in 42/42** | — |
| implied MC at the block's own price | ~8.3 k USD | — |
| implied MC at the last curve ticket | ~26.1 k USD | — |
| implied MC at AMM open | ~54.0 k USD | — |

On an independent, frozen sample of tokens that later reached >= 500 k USD, **58 of 70 = 82.9 %**,
Wilson 95 % CI **[72.4 ; 89.9]**, had their curve bought back for >= 60 SOL inside the creation slot
**[R]** (`data/v09_signature_gros_tokens.json`, frozen 2026-07-29). Two caveats travel with that
figure permanently and are repeated wherever it is quoted: the 70 tokens are an **outcome-selected
set** — conditioned on reaching >= 500 k USD, so this is P(signature | large), never
P(large | signature) — and the sample is **frozen at a fixed date**, so `n` is fixed at 70 and does
not grow with new launches. (An earlier draft quoted 48 of 60 = 80.0 %; that count was the first 60
rows of the file while it was still being written, and is superseded by the frozen 70.)

**Fleet.** A set of addresses that co-occur in creation-slot blocks across several launches.
Membership is asserted upstream and **tested** here, not assumed: `m3_operators.py` recomputes
counts, pairwise disjointness between fleets, and co-occurrence lift with its p-value, so a fleet
whose cohesion did not hold would show up as incoherent in its own output table.

**Shared-infrastructure address.** An address that snipes a large share of *all* launches
indiscriminately — a service used by many actors, not a participant in any one operation. Ubiquity of
the five most frequent addresses: **58.5 %, 35.1 %, 32.3 %, 24.8 %, 15.6 %** of the 282 tokens
carrying a sniper list **[R]**. These addresses are excluded from every link computation (§3.10).

In prose they are referred to as **W1 ... W9**, ordered by ubiquity. One editorial note, because a
reader will notice the inconsistency otherwise: base58 vanity prefixes are chosen by whoever
generates the keypair, and the most ubiquitous address in this corpus carries a prefix that is a
racial slur. It is replaced throughout the published documents and machine outputs by a stable
redaction token (`RDCT-<hash>`), consistent across files so that cross-referencing still works. Every
other address appears in clear: they are public on-chain identifiers and redacting them would only
make the results unverifiable.

**Operator cluster.** A group of launches sharing fleet addresses, computed **after** infrastructure
exclusion. The hypothesis actually tested is not "who is behind this" but a choice between two
mechanisms: `H_unique` (one entity) versus `H_methode` (several distinct entities applying the same
method). Strict disjointness of address sets combined with identical geometry supports `H_methode`,
which is what this corpus shows and therefore all that is claimed. No identity, no intent, no
attribution to any person is asserted anywhere.

### 1.3 Time

| term | definition | value |
|---|---|---|
| `t0` | mint creation timestamp | — |
| **detection** (`detect_ts`) | first external visibility: token seen `complete` at most 12 s after creation. A **lower bound** on any human buyer's latency, deliberately favourable to the buyer | <= t0 + 12 s |
| **entry** | `t0` + 120 s — the first moment a human who saw the token appear could plausibly have an order in | +120 s |
| **decision bucket** | 30 s; a rule that triggers on bucket *k* is filled on bucket *k+1*, never at the price that triggered it | 30 s |
| **fill horizon** | window in which counterparty for a 0.5 SOL order is looked for | 120 s |
| **`t_safe`** | last observed swap - 120 s; an exit scheduled later is pulled back to it | — |
| **capture window** | swap stream recorded from graduation to +20 min | 20 min |
| **long horizons** | +1 h, +2 h, +4 h, +24 h, from hourly OHLCV candles | — |
| **temporal cluster** | launches separated by <= 30 min | 1800 s |
| **day** | UTC calendar day, one single implementation (`pumplib.utc`) so that every table cuts days identically | — |

### 1.4 Measurements

**Executed price.** `sol / tokens` of a swap: what the buyer actually paid, router fees included in
`sol`. The pool's own `price` field is used only as a control; the two agree to the third decimal
(`m2_entry_price.py`).

**Robust price.** Median of the executed prices of swaps of **>= 0.3 SOL** within a 30 s bucket. No
interpolation: absence propagates as `None` rather than as a stale value.
Why not `max(price)`: dust swaps of ~0.002 SOL carry an implied price dominated by unit rounding and
produce values several orders of magnitude off — the raw max implies a market cap of 8.9e8 SOL, a
physically impossible number. The 0.3 SOL floor and the median remove the artefact without any
hand-picking. The same definition is used by the price series and by the round-trip engine, so the
two never disagree about what "the price" was.

**Exploitable swap.** `ts` present, `tokens > 0`, `sol > 0`, `side` in {buy, sell}. Applied to the
published corpus: **511 508 raw rows -> 476 847 exploitable**, i.e. 34 661 dropped, of which 34 659
are zero-SOL legs and 2 have non-positive token amounts **[R]**. The filter is stated here because a
corpus size quoted without its filter is not a corpus size.

**Market cap.** `price * 1e9`. The bonding-curve launch constant is **27.96 SOL**, verifiable outside
this repository. Useful scale: at the first observable instant the median market cap is already
**706 SOL**, i.e. **x25.2** the launch constant, and the median share of the launch-to-peak log-run
already consumed is **0.90** **[R]** (`docs/out/m2_entry_price.json`).

**Units — the single most expensive mistake in this project.** Capture prices are **SOL per token**;
the OHLCV provider returns **USD per token**. Mixing them multiplies every ratio by the SOL price
(~75 over the window) and once turned a −60 % result into a +2 900 % one **[P]**. Two defences are
now permanent: unit conventions are declared at the top of the shared library, and every cross-source
table prints a **dimensional sanity ratio** — `(USD price / SOL price) / (SOL in USD)` — whose
measured value is **0.850 on n = 277**, close to 1, published in the table's own footer.

**Depth and the book.** The data contains no order book. The "book" is reconstructed from the trades
that actually happened: the counterparties that really showed up. Bids are walked from the best price
down until 0.5 SOL is absorbed. This is strictly more conservative than a displayed book, which can
be cancelled. Minimum size to count as depth: 0.05 SOL (strict variant: 0.3 SOL, printed alongside).

**Round trip and drag.** `pnl = (p_out * (1-0.02) * (1-0.01)) / (p_in * (1+0.02) * (1+0.01)) - 1`,
i.e. a **5.8241 %** round-trip drag deducted from every figure. The 0.5 SOL position is deliberately
tiny: a larger buyer's impact goes in the same direction, never the opposite one, so the reported
loss is an optimistic bound on a real buyer's.

### 1.5 Targets

Three families, and the rule that governs them:

- **Absolute** — `ATH >= 200 k / 300 k / 500 k / 1 M`. Primary.
- **Residual** — `log10(ATH)` minus its within-day OLS fit on `log10(entry MC)`, binarised at the
  within-day upper tercile (`t_resid_logath_top33`). Primary. By construction, entry market cap
  carries no information about it.
- **Multiple** — `ATH / entry MC`. **Never primary.** The elasticity of `log ATH` to `log MC` is
  **0.884** on B (0.673 on A, 0.761 on C) **[P]**, so `log(multiple)` has a mechanical slope of
  `beta - 1 = -0.126` in the entry market cap — measured at −0.1263, exactly as predicted. Any
  variable correlated with entry MC becomes "predictive" of the multiple without carrying
  information. The dataset's own metadata carries the prohibition in writing.
  *Limitation, added on review*: the elasticity is published **without a standard error or CI**;
  measurement error in the entry MC (errors-in-variables) mechanically pulls the OLS slope below 1,
  and the near-flat ×2 rate across observed-MC bands (T2b, panel B) is in tension with a causal
  reading of b < 1. b is used here as a mechanical decomposition only; as an economic claim
  ("entering higher degrades the multiple") it is indicative, **NON ÉTABLI**.

Two fields are flagged in the dataset as **outcome-contaminated or censored** and are banned as
targets: `t_buyable` (defined as "peak occurs after detection" — it selects tokens that went up) and
`o_max_ath_logged` (a running maximum frozen when the row was written; below the true peak in 39.8 %
of rows) **[P]**.

---

## 2. Populations

Every rate in this repository is reported against one of four named populations, with `n`, cluster
count and day count. They are not interchangeable and are never pooled.

| id | definition | n | clusters | days | window |
|---|---|---|---|---|---|
| **A** | detector log, full-curve buyback (>= 60 SOL), after removing the 10 placeholder-poisoned rows | 93 | 34 | 3 | Jun-Jul 2026 |
| **B** | fast-graduation tokens with a verified peak, sane MC regime (5 k - 300 k) | 1 243 | 123 | 20 | 2026-06-27 -> 07-18 |
| **C** | subset carrying a swap-level capture (0-20 min) | 278 | — | 7 | 2026-06-27 -> 07-04 |
| **canonical** | tokens on which a 0.5 SOL round trip is actually executable at t0+120 s | 196 | 20 | 6 | 2026-06-27 -> 07-04 |

`A_all` = 103, `B_all` = 1 701, `C_all` = 293 before quality filters **[R]**
(`data/dataset_socle.json:meta.counts`).

**The attrition ledger.** Published in full, because the gap between "files collected" and "rows
analysed" is where sample sizes go to die **[R]**:

```
645  capture files produced by the collector
-352  empty (silent upstream RPC failures — an outage, not a market phenomenon)
= 293  non-empty captures            <- any headline quoting "645 captures" is wrong by 2.2x
 -  3  swap span < 120 s
 -  1  no buy at all
= 289  exploitable captures
 - 62  no robust price at the entry instant
 - 25  no offer able to absorb 0.5 SOL
 -  5  insufficient large-trade volume in the entry bucket
 -  1  entry falls after the end of the capture
= 196  tokens on which an entry is actually executable  (20 clusters, 6 days)
```

**Corpus window** (capture side): 2026-06-27 20:20 UTC to 2026-07-04 01:42 UTC — **6.2 days**,
7 calendar days, 293 tokens, 476 847 exploitable swaps, 90 979 distinct addresses seen swapping,
32 temporal clusters **[R]** (`python3 code/m1_corpus.py`).

---

## 3. Validation protocol

### 3.1 The unit of analysis is not the token

Tokens launched within 30 minutes of each other share a market regime. Treating them as independent
observations inflates precision. So:

- rates are reported with **n, cluster count and day count**, never with n alone;
- the headline mean is a **mean of cluster means**;
- confidence intervals for means come from a **cluster-level bootstrap** — the clusters are
  resampled, not the tokens — and the resampled estimator is the same mean-of-cluster-means as the
  point estimate, so the interval always contains its own point estimate (a mismatch here silently
  produces intervals that exclude the value they are supposed to bracket);
- proportions use Wilson intervals, which behave near 0 and 1 where the normal interval does not;
- median intervals use a percentile bootstrap with an **explicitly coded linear congruential
  generator**, so results are byte-identical across machines and Python versions —
  `random.seed()` does not guarantee that between versions.
- *Precision, added on review*: the LCG median bootstrap above is the engine of the
  m5/`pumplib` chain. The T1/T4/T5 **median** intervals use `common.boot_ci_median_tokens` —
  token-level resampling with `random.Random` — so they are narrower than a cluster-aware
  interval would be (effective n ≈ 5.5, below) and are indicative; the **mean** CIs, which carry
  the conclusions, are cluster-level. The engines are deliberately not merged (`code/statlib.py`,
  header): merging would silently change published numbers.

**And the honest consequence.** On the canonical corpus the 196 tokens fall into 20 clusters of sizes
**67, 34, 31, 12, 9, 8, 6, 6, 6, 5, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1**; one single day supplies **70 of
196** rows. Kish's effective sample size over clusters is **5.5** **[R]**. The correct reading of T1
is therefore "negative on ~6 effective observations", not "negative on 196". That number is stated in
the results rather than buried here, because a table that hides it is doing rhetoric.

### 3.2 Declared targets, forbidden targets

Primary targets are fixed before analysis (§1.5), the multiple is banned as primary, and every
categorical contrast is published **stratified on entry market cap** next to its crude version. Entry
MC is the dominant covariate of this corpus — a 7.9x spread on the absolute target across entry-MC
deciles **[P]** — and nearly every apparent categorical effect turned out to be it in disguise
(pitfall P4: a crude +30.0 points at p = 0.0032 became a Mantel-Haenszel odds ratio of 1.22 at
p = 0.97 once stratified).

### 3.3 Multiplicity: test the statistic you actually selected on

When k rules are swept, the quantity that was selected is the **maximum** over k, and its null is the
distribution of that maximum, not of a single test. Procedure: cluster-level sign-flip permutation,
5 000 draws, Westfall-Young max-T. On the 38-policy sweep **[P]**: best observed +7.26 %, raw
p = 0.279, max-T corrected p = 0.585, Bonferroni over 38 = 1.000, and the 5 % critical value of the
max-null is **+26.3 %** — the observed best is a quarter of the bar that noise clears routinely.

The corollary is a standing rule: **count the tests before running them.** In one related track,
115 370 tests were run against a permutation floor of 2.5e-4 (4 000 draws) and a Bonferroni threshold
of 5.6e-7 — no result could have passed, by construction, and the whole track was arithmetically dead
before it started **[N]**.

Note the asymmetry that makes T1 easy: its result is negative on every cell. Sweeping more policies
can only make a uniformly negative result *harder* to obtain by chance, so no multiplicity correction
is required there. Corrections are needed to defend a winner, not a null.

### 3.4 Base rates and matched comparisons

No rate is published without the base rate of the same population next to it. Two rules follow:

1. **Any filter is compared against the unfiltered population**, which is how the `t_buyable`
   inflation was caught: 69.8 % versus a 46.3 % base rate **[P]**.
2. **Availability is never compared across a variable that determines availability.** Testing whether
   lost captures differ in outcome must use an outcome measured by a source *independent* of the
   capture pipeline. Measured on the pipeline's own labels the gap looks like +29 points; measured on
   an independent source it is 49.1 % versus 50.7 %, permutation p = 0.77 **[P]**. The first number
   measures coverage, not signal.

### 3.5 Out-of-sample validation — where it exists, and where it does not

This is the section a reader should be most sceptical about, so it states the negative first.

**Available, and decisive.** One filter (second-wave concentration, "<= 10 buyers at rebuy") reached
**93 % in-sample on n = 60**, survived permutation, survived Bonferroni, survived a holdout — and
returned **53 % on n = 30 forward**, with AUC falling from 0.21 to 0.45 **[N]**. It is the single most
useful result in the project: in-sample robustness, including the standard battery, is not evidence
of out-of-sample validity on this data. Underlying data is not in this repository, so the figures are
quoted as testimony, not as a verified measurement.

**Not available.** T1, T4, T5 and the operator graph have **no out-of-sample validation**. They are
descriptive measurements of a single window. They are reported as such, and the failure of the one
strategy-like claim that *was* forward-tested is the reason no strategy-like claim is made from them.

**Structural substitutes** used where a true holdout was impossible: cluster-level and day-level
resampling (§3.1), leave-one-token-out on any positive mean (T4 publishes a "mean without the single
best token" column whose only function is to destroy its own positive result), and sign stability
across day splits.

### 3.6 Live-safe mirrors

Any rule with a retrospective anchor is reimplemented as an exact **zero-lookahead mirror** and the
difference is subtracted rather than argued about. The canonical case **[P]**: entering 120 s after
the price trough returned +14.7 % median; the mirror — enter when the current bucket is the running
minimum *so far* and the last closed bucket has recovered — returned **−2.8 %**. The lookahead is
**17.5 points of median**, measured in the unit of the result.

Two standing consequences: a decision taken on bucket *k* is always executed on bucket *k+1*, never
at the price that triggered it; and a rule whose mirror cannot be written is not published. The
decomposition is also informative — the mirror caught the true trough 78 times out of 162 (48 %), and
none of 27 flow features improved that capture rate (best AUC 0.596), which reframes the idea as a
timing problem rather than a filtering problem.

### 3.7 Every missing value is a hypothesis

Three rules:

1. **State the convention.** Unfilled exits are scored **−100 %** (hard). It is stated in the method,
   not chosen per table.
2. **Publish the sensitivity.** Every run prints hard / soft / strict-book side by side. It matters:
   switching to "drop the unfilled" moves `tp50` from **+3.3 % to +31.5 %** and flips three policies
   from clearly losing to apparently winning, on a one-word change **[R]**, because a token has no bid
   precisely when it is dead — dropping it excludes the worst outcomes and calls the remainder the
   average.
3. **Characterise missingness on three axes** — time, covariates, outcome. Here: 352/645 captures lost;
   a runs test gives 10 observed runs against 320.8 expected (p = 0.0002), so the losses are outages,
   not dropout; and they are outcome-neutral on an independent outcome source **[P]**. Conclusion:
   the loss costs power, not validity — a statement that had to be *measured*, not assumed.

### 3.8 Two implementations, and a port control

The round-trip result was computed twice, by two independently written engines. Raw agreement was
**9.7 % within one point on 1 887 pairs** — and every divergence was diagnosed rather than averaged
away **[N]**:

- differing cost assumptions (3.92 % vs 5.82 % drag) explained 100 % of the median divergence on the
  four time-based exits;
- a **lookahead** in one engine (15 s grid, decision evaluated over `[t, t+30)` while the robust price
  moves 6.2 % in median over 30 s) produced **+92.2 % versus −58.2 % on a single token — 150 points of
  difference on identical books**;
- a 600 s lookahead filter in the same engine dropped losers preferentially (−8.6 % vs −2.6 %).

The more conservative engine was adopted as canonical. The published port is then checked cell by
cell against the original engine's frozen output:

```
python3 code/m5_roundtrip.py --reference ../docs/reference_canonical.json
  cells compared            30
  maximum absolute deviation 0.000002 percentage point   OK        [R]
```

### 3.9 Instrument checks, run before analysis

- **Dimensional sanity.** Every cross-source ratio prints its measured value; expected ~1 (§1.4).
- **Placeholder scan.** Every field is scanned for suspicious constants and zero timestamps *before*
  any rate is computed, and the share of the **positive class** each anomaly supplies is reported —
  not the share of rows. Ten rows with `detect_mc = 15000` and `detect_ts = 0` supplied **24.3 % of
  the `>= 3x` positive class** while being 10 % of the rows **[P]**. They are kept in the published
  data behind a named `poison_default` flag rather than silently deleted, so the contamination stays
  auditable.
- **Censored fields.** Any incrementally written field is treated as censored until proven otherwise
  and is banned as an outcome.
- **Transport probes.** A collector is tested with a live probe that can actually fail. The provider
  rejects the default `urllib` User-Agent with HTTP 403; a retry wrapper that treats every non-429
  error as transient turns a **100 % failure rate into an empty dataset instead of an exception**
  **[P]**.
- **Provider limits recorded with the data.** The OHLCV endpoint retains ~1 000 candles at any
  granularity: 16.7 hours at minute resolution, 41.6 days hourly. Granularity is chosen from the span
  required, and `n_candles` plus the covered span are recorded on every row.
- **Liveness is a delta, not an existence check.** A PID proves nothing: a daemon froze for two days
  with its PID intact and the watchdog reporting healthy. Liveness = CPU time consumed since last
  check **and** bytes written since last check. Two of two supervision probes were wrong on first use,
  and both failed toward false confidence **[P]**.

### 3.10 Graph structure needs a null model and a hub policy

A co-occurrence graph produces a giant component by default; that is not a discovery. Two mandatory
controls, both published with their sensitivity:

**Hub removal.** Edge = at least 3 shared snipers, over 282 tokens:

| exclusion rule | giant component | share |
|---|---|---|
| none | 180 | 63.8 % **[R]** |
| declared shared-infrastructure list (9 addresses) | 57 | 20.2 % **[R]** |
| every address present on >= 14 tokens (14 addresses) | 48 | 17.0 % **[P]** |

Both rules are published because the answer depends on which one is used, and a reader is entitled to
see that dependence. Per-address contributions are printed too: removing W1 alone takes the component
from 180 to 128, W2 alone from 180 to 136 **[R]**.

**Degree-preserving null, confined within the day.** A Chung-Lu null reproduced **1 502 of the 6 024**
pairs meeting the clustering criterion — a **24.9 % false-positive rate** — and a giant component of
564 against 668 observed **[N]**. A day-blind null had previously certified "19 significant clusters";
preserving the day of each edge killed them. Time is a confounder in any co-launch graph, and a null
that ignores it certifies coincidences.

**And the symmetric error.** Ubiquity is evidence of sharing, not proof of it: one address classified
as infrastructure on ubiquity alone turned out to be a launch operator sniping its own 51 tokens
**[N]**. The exclusion list is therefore declared explicitly in the code and testable, not inferred
by threshold at runtime.

### 3.10b A detector's own criteria need a null before their output is read

§3.10 applies the rule to a graph. It applies to every detector, and the phase-1 split detector is
where the project learned that the hard way.

That detector fires on three criteria — same funding transaction, same amount inside one hour, or a
shared private funder — and each was given a null distribution built from the population the
detector actually faces: the control wallets, pooled, drawn in random groups of the target size, run
through the identical code. Resampling destroys within-token co-occurrence, so every hit in a drawn
group is a coincidence by construction.

| criterion | fires on a random group of 40 |
|---|---|
| same funding transaction | 0.0000 **[N]** |
| same amount within one hour | 0.0000 **[N]** |
| shared private funder | **0.889** **[N]** — 0.995 restricted to wallets whose genesis was reached |

The third criterion was retired on that basis, and every verdict recomputed without it. The rule the
project now applies:

- **No criterion enters a verdict before its own false-positive rate is measured.** A disjunctive
  verdict (`A or B or C`) is only as specific as its *loosest* term, so the loosest term must be
  measured first, not last.
- **The null is built from the control population, not from a parametric assumption.** The controls
  were assembled for the comparison; they double as the resampling pool at no extra cost.
- **The rate is reported at several group sizes.** A criterion whose false-positive rate climbs with
  group size — 0.151 at 10, 0.461 at 20, 0.889 at 40 — is a birthday problem, and its apparent
  strength on any single sample is an artefact of that sample's size.

### 3.11 Reproducibility

- **Standard library only** for every published measurement — no numpy, no pandas, no network, no
  API key. The scripts that *do* need the network are the two fetchers (`fetch_sol_usd.py`,
  `fetch_gt_ohlcv.py`) and the on-chain verifiers (`v0*.py`); their outputs
  are committed so every table regenerates offline.
- **Deterministic randomness**: explicit LCG, fixed seeds, stated in the function docstring.
- **One command per table**, printed in the table's own footer (`Regenerer : python3 code/...`).
- **Published reduction**: `make_public_data.py` publishes the reduction itself — what was dropped,
  rounded, truncated — and `data/MANIFEST.json` carries a sha256 per file plus the transformation
  list (empty captures dropped, `fees` removed, signatures kept only for `t <= created + 30 s`, SOL
  rounded to 6 significant digits, prices to 8, **no address anonymisation**: Solana addresses are
  public data).
- **Verified**: every committed result table regenerates bit-for-bit from `./code` + `./data`, and
  CI re-runs that byte-comparison on every push (`run_all.py --strict`). An earlier pass caught the
  committed T5 **stale** at n = 18; it has been regenerated since (currently n = 191, 27 clusters)
  and the byte-check now guards all of them.

---

## 4. What each claim had to survive

A compact audit trail: the tests each published claim actually passed, and the ones it did not.

| claim | population | cluster-level CI | multiplicity | stratified on entry MC | lookahead mirror | out-of-sample |
|---|---|---|---|---|---|---|
| no exit policy is profitable in expectation (T1) | canonical, 196 / 20 / 6 | yes (0/15 above zero) | not needed (uniformly negative) | n/a | n/a | **no** |
| no post-snipe entry rule reaches 1x (T4) | canonical | yes (all cross zero) | n/a | n/a | yes (bucket k -> k+1) | **no** |
| value decays over 1 h - 24 h (T5) | 191 / 27 clusters | yes | n/a | n/a | n/a | **no** |
| the peak is already past at first visibility (T3) | B clean, 1 243 / 123 / 20 | Wilson per band | n/a | yes (by MC band) | n/a | n/a (descriptive) |
| the multiple is a denominator artefact (T2) | A, B, C | — | n/a | yes | n/a | replicated on 3 populations |
| the creation-slot signature | 42 launches / 70 large tokens (frozen) | Wilson [72.4 ; 89.9] | n/a | n/a | n/a | **no** (outcome-selected 70) |
| fleets are distinct, method is shared | 282 tokens | co-occurrence p-values | n/a | n/a | n/a | attacked twice, survived, §5.7 |

---

## 5. Limits

Stated as measurements wherever possible, with the **direction** of each bias.

### 5.1 Window

The capture corpus covers **6.2 days** (2026-06-27 to 2026-07-04) and population B covers **20 days**
(to 2026-07-18). Nothing here says anything about any other market period, and no claim in this
repository is phrased as a general law. Memecoin microstructure changes on a scale of weeks.

### 5.2 Coverage

End-to-end coverage of the full launch flow is **6.8 %** (capture stage 0.377 x attribution stage
0.181) **[N]**. Within their own window the captures cover **278 of 805** eligible tokens
(**34.5 %**) **[P]**. This is a partially observed system, and it is described as one.

### 5.3 Selection, and the sign of the bias

The collector observes tokens it detected, not the population of launches — so the corpus
**over-samples tokens that moved**: P(peak >= 200 k) is 32.7 % in captured tokens versus 28.3 % in the
eligible population, **+4.5 points** **[P]**. This bias runs **against** the repository's own
conclusion: a sample enriched in winners should make buying look *less* unprofitable than it really
is. Where a bias helps the author's thesis it is treated as fatal; here it does not, and that is
stated rather than left for the reader to work out.

Separately, the 70-token sample behind the creation-slot signature is **outcome-selected** — frozen
tokens that later reached >= 500 k USD, not a random draw of launches (§1.2): the figure is
P(signature | large), never P(large | signature). (An earlier draft used the first 60 rows in file
order; it is superseded by the frozen 70.)

### 5.4 Effective sample size

The nominal n's are large; the effective ones are not. Canonical corpus: **20 clusters, 6 days,
Kish effective n = 5.5**, one day supplying 70 of 196 rows **[R]**. Population B is healthier (123
clusters, 20 days) but its outcomes come from a single provider's ATH field.

### 5.5 Missing data

**352 of 645 captures are empty** — silent provider failures. Measured: time-clustered (runs test
p = 0.0002; longest gaps 168 consecutive empties over 4.7 h and 140 over 36.5 h) and outcome-neutral
on an independent outcome source (p = 0.77) **[P]**. Cost: statistical power. Not measured, and not
claimable: whether the outage windows coincided with unusual market conditions.

### 5.6 Instrument and provider limits

- No order-book data exists for this venue; depth is reconstructed from executed trades (§1.4).
  Conservative, but it cannot represent liquidity that was offered and never hit.
- Peak timestamps come from the pump.fun API (one-second resolution) while `detect_ts` is a local
  clock. A few seconds of skew are possible, which is exactly why T3 publishes **three** thresholds
  (already past / < 60 s / < 120 s) and rests its conclusion on none of them alone.
- The OHLCV provider retains ~1 000 candles: any token older than 16.7 hours has its early trough and
  peak outside a minute-granularity window (§3.9).
- Costs (1 % + 2 % per leg) are a stated assumption, not a measurement of what a given router charges.

### 5.7 What is explicitly **not** established

- **Identity or intent.** Addresses are technical identifiers observed on a public ledger. No natural
  person is named, no attribution of intent is made, and no claim of coordination beyond measured
  address co-occurrence is asserted. The corpus contains no funding transfers, so a shared upstream
  financier — plausible — is not measurable here.
- **A single controlling entity.** The evidence supports "distinct fleets applying the same method"
  (strict disjointness of address sets, identical geometry, a shared software fingerprint: ALT usage,
  identical fee constant, hard-coded tip, strictly decreasing tickets). A shared *tool* is not a
  shared *owner*.
- **"Atomic" bundles.** Explicitly refuted: the dominant signer share is exactly 1/n on every
  measured launch and there is **0/42** transaction duplication — each buyer signs its own
  transaction **[N]**. The word is not used.
- **Any dating of a "sequential -> bundled" market transition.** The graduation walk has **no
  historical depth** (its oldest reached record is the run date), so no transition is dated, not even
  as a hypothesis. It is an open question, listed as one.
- **Operator skill.** Attacked twice and refuted twice: a "k >= 8" selection rule memorised 2
  addresses out of 822 (residual +0.042 without them, and a mid-window live rule would have ranked
  the eventual best operator **5th of 22**); operator identity explains the peak at **p = 1.000**,
  with the UNKNOWN group ranking best **[N]**.
- **Provenance parity between offline features and live features.** Declared leak: features were
  rebuilt offline with full pagination (median 408 signatures) while the live path reads one page of
  100 — **0/282 feature sets identical**, retention 0.964. Any model trained on the offline features
  would not see the same inputs live **[N]**.

### 5.8 Figures that did not reproduce

Three numbers circulating in the working notes could not be re-derived from the published data and
are **not** used: an ATH ratio of 6.4x for the "buyable" split (recomputed 2.55x to 4.39x depending
on population), "67 % of tokens peaked before detection" (recomputed 21.3 % on B; the 67 % came from
a subgroup of **n = 3**), and a "93 % manufactured by the buyable filter" (that 93 % belongs to a
different episode — the forward-test failure of §3.5 — and conflating them would be wrong in both
directions). They are listed in [PITFALLS.md](PITFALLS.md#what-did-not-reproduce) rather than quietly
dropped: a number that cannot be regenerated from the published data is not a result, even when it
points the right way.

---

## 6. Scope, data and ethics

- **Object of study.** The microstructure of a public market venue. Descriptive work: no
  recommendation, no investment advice, no execution tooling, and nothing in this repository is
  designed to be traded.
- **Addresses.** Solana addresses are public on-chain identifiers and appear as such. No
  third-party address is ever linked to a person, a name or an intent. Shared-infrastructure
  addresses are referenced by the neutral identifiers W1...W9 in prose (§1.2). The one deliberate
  exception is the author's own exchange deposit address, published and self-attributed on purpose
  (README.md, "Author"; `docs/EXPLOITATION.md` §5).
- **No secrets, no third-party personal data.** No API keys, tokens, `.env` files, session
  material, local filesystem paths. The one personal disclosure is the author's own: the KYC'd
  exchange deposit address and its reconstructed deposit ledger (`docs/out/expl_ledger.json`),
  published deliberately as self-attribution. Published data is the reduction described in
  `data/MANIFEST.json`, with a sha256 per file.
- **Reproduction.** Offline, standard library only:

```
python3 code/m1_corpus.py                                     # corpus census and its limits
python3 code/m5_roundtrip.py                                  # round trip, 10 exit policies
python3 code/m5_roundtrip.py --reference ../docs/reference_canonical.json   # port control
python3 code/m4_infra_ubiquity.py                             # hubs and giant-component collapse
python3 code/p0_pitfalls_check.py                             # recomputes every figure in PITFALLS.md
python3 code/t1_base_rate_sorties.py                          # -> docs/tables/T1_*.md
python3 code/t2_x2_par_prix_entree.py                         # -> docs/tables/T2*.md
python3 code/t3_ath_avant_detection.py                        # -> docs/tables/T3_*.md
python3 code/t4_entree_post_snipe_20min.py                    # -> docs/tables/T4_*.md
python3 code/fetch_sol_usd.py && python3 code/fetch_gt_ohlcv.py && \
python3 code/t5_horizon_1h_24h.py                             # -> docs/tables/T5_*.md  (needs network)
```
