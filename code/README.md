# `code/`: Reproducing the Measurements

This directory contains the executable measurement pipeline behind the repository.

The objective is simple:

> **Every published number should be reproducible from code and committed data, and every important narrative claim should be traceable to a measurement.**

The code is designed to make silent methodological drift difficult: reproducibility checks, independent implementations, null models, chronology checks, explicit censoring, cluster-level bootstrap, deterministic outputs, and publication gates are part of the measurement pipeline rather than post-hoc documentation.

---

## 0. Quick Start

Requirements:

* Python **3.9+**
* standard library only for the core offline pipeline
* no installation step
* relative paths only
* no credentials committed to the repository

From a clean clone:

```bash
git clone <repo>
cd <repo>

python3 code/run_all.py --strict
```

The strict runner executes the **22 offline scripts**, then compares every regenerated committed table and JSON artefact byte-for-byte with the repository version.

A successful run means:

> The numbers published in `docs/` are the numbers produced by the current code from the current committed data.

It is not a claim that the measurements are universally correct; it is a reproducibility check on the repository's declared measurement pipeline.

Typical output:

```text
ok    p0_pitfalls_check.py
ok    m1_corpus.py
...
ok    a9_g2y_prelaunch.py
ok    p1_readme_check.py

22 ran, 20 skipped, 0 failed
every committed table and JSON reproduced byte for byte
```

All 22 offline scripts currently pass, including `p1_readme_check.py`.

---

# 1. Reproducibility Has Two Separate Checks

The runner deliberately checks two different things.

### Artefact reproduction

The code regenerates the committed tables and JSON files byte-for-byte.

This answers:

> **Does the current code still produce the committed measurement artefacts?**

### Narrative consistency

`p1_readme_check.py` independently recomputes every figure quoted in the root `README.md`.

It currently reports:

* **22/22 sourced claims reproduced**
* **0 mismatches**
* 15 narrative figures that still have no underlying artefact

Those 15 unsourced figures are reported but are not treated as measurement failures.

This distinction matters:

> **Unsourced is not the same defect as wrong.**

If `p1_readme_check.py` fails, the correct response is to fix either the prose or the measurement.

The expected value must never be modified simply to make the test pass.

---

# 2. The Three Headline Measurements

| Question                                                 | Command                                         | Primary output                                               | Requirement         |
| -------------------------------------------------------- | ----------------------------------------------- | ------------------------------------------------------------ | ------------------- |
| Is the curve bought back inside the creation slot?       | `v05_creation_block.py` → `v06_curve_ladder.py` | `data/v05_creation_block.json`, `data/v06_curve_ladder.json` | Solana RPC, cached  |
| What does an exit policy return without an entry filter? | `t1_base_rate_sorties.py`                       | `docs/tables/T1_base_rate_sorties.md`                        | None                |
| What happens after the 20-minute capture window?         | `fetch_gt_ohlcv.py` → `t5_horizon_1h_24h.py`    | `docs/tables/T5_horizon_1h_24h.md`                           | Public HTTP, no key |

---

# 3. On-Chain Verification of the Creation-Slot Signature

The creation-slot claim is:

> **The bonding curve is bought back within the token's creation slot.**

The verification deliberately does **not** start from known operator wallets.

Doing so would make the measurement circular.

Instead, `v05_creation_block.py`:

1. takes the 42 previously identified creation slots;
2. retrieves the complete block;
3. enumerates every successful purchase of the target mint in that block;
4. identifies the set of buyers above 5 SOL;
5. measures the resulting creation-block structure.

Wallet identity is used to select the verification population, **not to define what counts as a purchase**.

Run:

```bash
export HELIUS_API_KEYS=...
python3 code/v05_creation_block.py
python3 code/v06_curve_ladder.py
python3 code/v08_ages.py
```

The first pass makes the required RPC calls and populates:

```text
data/cache/
```

After the cache is populated, the scripts can be rerun offline.

The cached material currently contains:

* 42 blocks
* 859 transactions
* approximately 437 MB

The cache is therefore git-ignored while the derived artefacts are committed.

---

# 4. Exit-Policy Backtest

`t1_base_rate_sorties.py` is the quantitative core of the buyer-economics analysis.

It is intentionally designed to be attacked.

## 4.1 Independent implementation

The simulator is implemented from scratch in the file itself.

It reads the raw swap stream and is reconciled **token by token** against a second independently written implementation.

The agreement block runs at the end of the analysis and is documented in `docs/PITFALLS.md`, P2.

The archived result is retained even though the working corpus used for the full reconciliation is not published.

---

## 4.2 No lookahead

A decision observed in 30-second bucket `k` cannot execute at the price of that same bucket.

The execution occurs at:

```text
t_e + 30(k + 1)
```

because the closing price of bucket `k` is only known after that bucket has ended.

The median price movement between adjacent 30-second buckets is approximately **6.2%** in this dataset.

The execution convention therefore materially affects measured PnL and is not treated as an implementation detail.

---

## 4.3 Unfilled exits

The primary result treats an unfilled exit as:

**−100%**

An `_excl` column is also published, but only as a sensitivity analysis showing how much the optimistic convention of dropping unfilled exits changes the result.

Unfilled exits are therefore not silently discarded.

---

## 4.4 Censoring

No exit is scheduled after:

```text
last_swap − 120 seconds
```

This guarantees that every scheduled exit has at least 120 seconds of subsequent recorded flow available for verification.

Consequently, a −100% result cannot be produced merely because the recorder stopped before the position could be evaluated.

---

## 4.5 Statistical Unit

The analysis does not treat every token as an independent observation.

Counts are tracked by:

* cluster;
* UTC day;
* token.

Confidence intervals use **cluster-level bootstrap** because multiple tokens associated with the same launch structure are not necessarily independent.

Run:

```bash
python3 code/t1_base_rate_sorties.py
python3 code/t4_entree_post_snipe_20min.py
```

The main 15-policy analysis takes approximately seven seconds on the reference environment.

---

# 5. Extending the Horizon Beyond the Capture Window

The capture system ends at approximately 20 minutes.

It therefore cannot answer:

> “What happens if the position is held longer?”

`t5_horizon_1h_24h.py` extends the measurement using hourly GeckoTerminal candles.

Run:

```bash
python3 code/fetch_sol_usd.py
python3 code/fetch_gt_ohlcv.py
python3 code/t5_horizon_1h_24h.py
```

The OHLCV collection covers the required tokens without an API key.

---

## 5.1 Unit Conversion Check

The two price sources use different units:

* swaps: **SOL per token**
* GeckoTerminal: **USD per token**

Dividing the two directly would therefore introduce the SOL/USD exchange rate as a multiplicative error.

`t5` converts through the hourly SOL/USD series and then validates the conversion independently.

For each token it compares:

1. the USD price of its first hourly candle;
2. the robust SOL-denominated swap price from the corresponding initial period.

The resulting ratio must reproduce the contemporaneous SOL price.

This check runs every time the analysis is executed.

---

# 6. Dependencies and Data Access

The pipeline is deliberately divided by data requirement.

| Class                      | Scripts                                                                   | Requirement                              |
| -------------------------- | ------------------------------------------------------------------------- | ---------------------------------------- |
| **Offline**                | `p0`, `m1`–`m6`, `t1`–`t5`, `a1`–`a7`, `a9`, `exit_ladder`, `p1`          | `data/` only                             |
| **Public HTTP**            | `fetch_sol_usd`, `fetch_gt_ohlcv`                                         | GeckoTerminal; rate-limited client       |
| **Solana RPC**             | `v05`–`v08`, `v1_*`, `v2_*`, `r1_*`, `a8_wallet_horde`, `09_bundle_snipe` | `HELIUS_API_KEYS`                        |
| **Unpublished raw corpus** | `v01`–`v04`, `make_public_data`                                           | `PUMP_PRIVATE_ROOT`                      |
| **Deposit ledger**         | `expl_ledger`                                                             | `EXPL_LEDGER_ADDR` + Helius on first run |
| **Figures**                | `f_*`                                                                     | `matplotlib`                             |

Environment configuration:

```bash
cp .env.example .env
```

`.env` is git-ignored.

`.env.example` contains the expected variable format but no credentials.

The credential loader is centralized:

```text
settings.helius_keys()
```

Keys are not written to disk.

`settings.redact_key()` removes them from printed output.

Multiple Helius keys can be supplied as a comma-separated list. The client rotates them round-robin and fails over on 429/5xx responses.

---

# 7. RPC Budget and Caching

The main RPC workloads are bounded and cached.

| Measurement   | Approximate workload                    |
| ------------- | --------------------------------------- |
| `v05`         | 42 `getBlock` calls                     |
| `v06` / `v07` | ~860 `getTransaction` calls             |
| `v08`         | Backward `getSignaturesForAddress` walk |
| `r1_*`        | Paginated enhanced-transaction endpoint |

`v08` caps the history walk at 40 pages per address.

When the cap is reached, the wallet is explicitly marked:

```text
censure=true
```

Its birth date is then reported as an **upper bound**, rather than silently pretending the history is complete.

All fetched responses are cached on first retrieval.

---

# 8. The Deposit-Wallet Ledger

`expl_ledger.py` measures the author's own exchange deposit wallet rather than a third-party on-chain subject.

Its question is deliberately narrow:

> **What actually landed on the exchange deposit address between 2024-10-01 and 2025-02-02?**

Several figures in the root `README.md` were previously asserted rather than measured.

They are now generated from the ledger artefact.

Run:

```bash
export EXPL_LEDGER_ADDR=6tmiM84AxMzmXzRByq7m1dgNkHtn9wp671e1GMe2ZmWU
export HELIUS_API_KEYS=...

python3 code/expl_ledger.py
```

Output:

```text
docs/out/expl_ledger.json
```

---

## 8.1 Ledger Definitions

### Incoming

The deposit wallet's positive balance delta on a successful transaction.

Current measurement:

* **259 transfers**
* **1,226.4663 SOL**
* **$244,315.58**

over the declared window.

### Outgoing

The exchange's sweep transactions:

* **190 sweeps**
* **1,226.4566 SOL**

These are reported separately and excluded from proceeds.

### Pass-through check

Incoming:

**1,226.4663 SOL**

Outgoing:

**1,226.4566 SOL**

Residual:

**0.0098 SOL**

The near-complete pass-through is the consistency check for the deposit-wallet model.

---

## 8.2 Price Method

Each incoming transfer is valued using the:

**Binance `SOLUSDT` daily close on that transfer's own UTC day**

There is no single average SOL price applied to the entire period.

`missing_price_days` must be empty.

A missing price day raises an error rather than silently defaulting.

---

## 8.3 What the Total Means

The total is the net value of **all incoming transfers**, including losing and winning activity.

There is intentionally no “best trades” table.

The aggregate already includes losing trades.

The artefact publishes:

* monthly SOL/USD/count data;
* window totals;
* sweep totals;
* aggregate counts.

It does not publish transaction signatures or sender addresses.

---

## 8.4 Attribution Limits

Sender attribution is heuristic.

The method identifies the counterparty associated with the most negative balance delta in the same transaction.

Therefore:

> **Sender counts are weaker than the money totals.**

The ledger also cannot prove that every incoming transfer is trading proceeds.

For example, capital sent back from the exchange and later redeposited would technically appear as another positive incoming transfer.

The measurement therefore counts every positive delta and separately measures whether an incoming transfer's heuristic sender also appears as a sweep recipient.

That return-of-capital signature is currently:

**0**.

---

# 9. Publication of the Deposit Address

The deposit address is intentionally published.

The repository treats this as a deliberate trade-off:

> **Public verifiability over pseudonymity for this particular artefact.**

The address is a KYC-linked exchange deposit address, so publishing it permanently connects the ledger to the author's legal identity.

Before this decision, it was represented using a salted-HMAC label:

```text
RDCT-838bf381fe
```

That mechanism was retired when the address was published.

The script still reads the address from:

```text
$EXPL_LEDGER_ADDR
```

and fails clearly if it is absent.

The artefact records which address was measured.

`run_all.py` therefore skips the ledger cleanly when the address or required RPC access is unavailable, reporting the exact missing condition rather than turning the absence into a failed test.

---

# 10. Reproducibility Guarantees

## 10.1 Public and private corpora

The published corpus is:

```text
data/floor_capture_public.jsonl.gz
```

It contains:

* **293 captures**
* **511,508 swaps**

The same measurement code can alternatively read the complete private capture corpus when:

```text
PUMP_PRIVATE_ROOT
```

is available.

The published representation rounds:

* `sol` to 6 significant digits;
* `tokens` / `price` to 8 significant digits.

The T1 output remains bit-identical across the two corpus representations, including all 15 policies.

The 352 empty captures removed at publication are represented explicitly in `data/MANIFEST.json` rather than disappearing silently.

---

## 10.2 Deterministic Ordering

Python's `Counter.most_common()` can preserve insertion order when counts tie.

That can make output dependent on hash randomisation.

The repository therefore sorts explicitly by:

```python
(-count, address)
```

The same treatment is applied to rejection dictionaries printed in table footers.

This makes the generated outputs stable across `PYTHONHASHSEED` values.

---

## 10.3 Sample Mode Cannot Overwrite Published Results

`m1` and `m5` support a small sample corpus:

```bash
--data data/sample/floor_capture_sample.jsonl
```

The sample contains:

* 20 tokens;
* data truncated at +300s;
* approximately 2 MB.

When `--data` is provided, output is redirected to:

```text
data/sample/
```

This prevents a small-format test run from silently overwriting a published table generated from the full corpus.

---

# 10.4 Python Version Scope

The random resampling is deliberately implemented using an explicit LCG rather than Python's `random` module.

The resampling counts are therefore interpreter-independent.

Two floating-point aggregates are not completely byte-stable across all Python/libm combinations:

* the log-log ATH/MC elasticity in `t2`;
* the mean-based cluster-bootstrap CI in `m5`.

The committed JSON is byte-identical on:

**CPython 3.12 and 3.13**

but may differ in the final approximately `1e-15` digits on 3.9–3.11.

The rounded published figures remain unchanged.

Accordingly, the strict CI byte-comparison is pinned to **Python 3.12/3.13**.

Python 3.9+ remains supported for execution; “byte-for-byte” reproducibility is specifically scoped to 3.12/3.13.

---

# 11. Pre-Publication Security Check

Before publishing changes:

```bash
python3 code/check_no_secrets.py [--identity personal_strings.txt]
```

The scanner fails on:

* 32-hex / UUID-like credentials;
* `sk-` literals;
* Telegram tokens and bot handles;
* `api-key=` URL parameters;
* absolute home paths;
* `.env`, `.pem`, session dumps and similar credential files;
* credentials currently present in the environment;
* configured personal strings;
* oversized files;
* unapplied redactions.

---

## 11.1 Scanner False Positives

The scanner itself has been hardened against two known false-positive classes.

### Solana System Program

```text
11111111111111111111111111111111
```

is a legitimate Solana System Program identifier.

32-character values consisting of two or fewer distinct characters are therefore not treated as keys.

### Scanner self-matching

The scanner's own pattern table naturally contains the patterns it searches for.

Only lines explicitly marked:

```text
# noqa: leakscan
```

are exempted.

The exemption is line-level rather than file-level.

---

# 12. Redaction Policy

Solana addresses and mint addresses are public technical data.

They are generally published in clear text because masking them would make the measurements difficult or impossible to independently verify.

There is one narrow exception:

> vanity addresses whose prefixes deliberately contain a racial slur.

For those identifiers:

```text
SHA-256(identifier)
        ↓
RDCT-<10 hex>
```

is stored in:

```text
code/redactions.json
```

The repository contains hashes rather than the original offending strings or the external word list.

The transformation is injective and the labels cannot be interpreted as base58 addresses.

Therefore:

* counts remain unchanged;
* clusters remain unchanged;
* graph measurements remain unchanged;
* independent researchers who already possess the original address can verify the mapping.

Current scope:

**43 identifiers / 212,201 scanned = 0.02%**

None belongs to the operator clusters analysed in the dossier.

The former HMAC-based privacy redaction for the author's exchange deposit address was removed when that address was deliberately published in 2026-08.

---

## 12.1 Redaction Is Applied at Write Time

Redaction occurs during data emission rather than as a post-processing pass.

Relevant write paths include:

```text
common.dump_json
pumplib.emit
lib_verif.save
r1lib.save
```

This means a rerun from the raw network cache cannot accidentally reintroduce a redacted identifier into a published artefact.

`sanitize_data.py --check` verifies this invariant.

The repository previously had a more dangerous implementation.

A naive `{32,44}` pattern could match a 44-character substring inside a valid 87–88 character Solana transaction signature and corrupt it.

The current implementation anchors the pattern and fails hard if a redaction label is attached directly to base58 characters.

---

# 13. Script Index

## Shared Infrastructure

| File                       | Role                                                                                    |
| -------------------------- | --------------------------------------------------------------------------------------- |
| `settings.py`              | Path resolution and credential loading                                                  |
| `pumplib.py`               | Corpus loading, conventions and evidence labels: `[MESURE]`, `[INFERE]`, `[NON ETABLI]` |
| `common.py`                | Capture filtering, robust price, cluster bootstrap, Wilson interval, table generation   |
| `lib_verif.py` / `hlib.py` | Helius client, disk cache, backwards signature walking                                  |
| `r1lib.py`                 | Strict Helius client distinguishing empty responses from quota errors                   |
| `redact.py`                | Redaction logic                                                                         |
| `build_redactions.py`      | Builds redaction mappings                                                               |
| `sanitize_data.py`         | Validates redaction invariants                                                          |
| `check_no_secrets.py`      | Publication security gate                                                               |
| `run_all.py`               | Reproduction runner                                                                     |

---

## Measurement Scripts

| File                              | What it establishes                                              |
| --------------------------------- | ---------------------------------------------------------------- |
| `p0_pitfalls_check.py`            | Recomputes figures quoted in `docs/PITFALLS.md` from `data/`     |
| `m1_corpus.py`                    | Corpus perimeter: included data, exclusions and reasons          |
| `m2_entry_price.py`               | Price actually paid versus pool price                            |
| `m3_operators.py`                 | Operator clusters and the attacks against those clusters         |
| `m4_infra_ubiquity.py`            | Shared infrastructure and its effect on graph connectivity       |
| `m5_roundtrip.py`                 | Round-trip economics under exit policies                         |
| `m6_horizon.py`                   | +1h/+2h/+4h/+24h horizon measurements                            |
| `t1`–`t5`                         | Five published measurement tables                                |
| `v01`–`v08`                       | On-chain verification: creation slot → curve → exit → wallet age |
| `v1_probe_addresses.py`           | Infrastructure-address existence and activity                    |
| `v2_dispatcher_burst.py` / `r1_*` | Funding-burst geometry and dust/funding separation               |
| `a1_null_model.py`                | Null firing rate of split-detector criteria                      |
| `a2_recount.py`                   | Recount of phase-1 tokens under surviving criteria               |
| `a3_hub_origin.py`                | Distribution-hub genesis and fan-out                             |
| `a4_selection_bias.py`            | Selection bias and the claims it invalidates                     |
| `a5_author_pattern.py`            | Token-by-token funding-dispatch presence test                    |
| `a6_gateway_chains.py`            | Dated gateway → distributor → wallet chains                      |
| `a7_cross_token_links.py`         | Cross-token linkage tests                                        |
| `exit_ladder.py`                  | Executable mechanical exit policy                                |
| `a9_g2y_prelaunch.py`             | Pre-launch funding burst and conflicting token collections       |
| `expl_ledger.py`                  | Exchange deposit-wallet inflows and pass-through reconciliation  |
| `p1_readme_check.py`              | Root `README.md` claim verification                              |
| `make_public_data.py`             | Construction of the committed public corpus                      |
| `f_*`                             | Figure generation                                                |

---

# 14. Known Limits

The code is reproducible, but reproducibility does not remove the limitations of the underlying data.

### One capture window

The main capture window is:

**2026-06-27 → 2026-07-04**

with **645 capture files**.

The results are conditional on that window.

No claim is made that the same measurements hold in other periods.

### Twenty-minute capture horizon

Primary captures stop at approximately 20 minutes.

Longer-horizon results therefore rely on hourly candles, which have:

* coarser temporal resolution;
* their own coverage gaps.

`t5` reports missing-candle observations rather than silently dropping them.

### Private upstream corpus

`v01`–`v04` require the unpublished raw corpus.

Their derived outputs are nevertheless committed, allowing downstream measurements to remain auditable without distributing the private source corpus.

### Address interpretation

Addresses are technical identifiers observed on a public ledger.

The repository does not infer intent or identity from them.

No address in the analysis should therefore be read as an attribution to a person or organization.

---

# Final Principle

The purpose of `code/` is not merely to make the analysis executable.

It is to make the analysis **attackable**.

A result is stronger when:

* another implementation reproduces it;
* a null model challenges it;
* a failed API call cannot become a false zero;
* lookahead is explicitly prohibited;
* censored observations are visible;
* statistical dependence is respected;
* unit conversions are checked;
* deterministic output is enforced;
* published prose is tested against the underlying artefacts;
* and previous mistakes remain documented rather than erased.

The repository therefore treats reproducibility as part of the evidence itself:

> **The code is not just how the result was generated. It is part of the argument for why the result should be trusted.**
