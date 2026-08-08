# `code/` — how to re-run every measurement

Stdlib-only Python 3.9+. No install step. Relative paths only. No credential in
any file.

```bash
git clone <repo> && cd <repo>
python3 code/run_all.py --strict
```

That runs the 22 offline scripts — no API key, no network, ~20 s — and
then **byte-compares every regenerated table and JSON against the committed
one**. A green run means the numbers in `docs/` are what this code produces
from this data today, not what it produced on some earlier state of either.

```
  ok    p0_pitfalls_check.py               0.6 s
  ok    m1_corpus.py                       1.4 s
  ...
  ok    a9_g2y_prelaunch.py                0.0 s
  ok    p1_readme_check.py                 0.0 s

  22 ran, 20 skipped, 0 failed
  every committed table and JSON reproduced byte for byte
```

All 22 offline scripts pass, `p1_readme_check.py` included.

**`p1_readme_check.py` is the guard that keeps the prose honest, not just
another script that happens to pass.** It recomputes every figure quoted in the
root `README.md` from the committed artefacts and exits non-zero the moment the
prose and the measurement disagree — today it reproduces all 22 sourced claims
with 0 mismatch and lists the 15 figures that still have no artefact behind them
(counted, never fatal: *unsourced* is not the same defect as *wrong*). The two
lines are independent and both have to be read: *"reproduced byte for byte"*
says the code still produces the committed artefacts, *"0 failed"* says the
narrative has not drifted from them. When p1 does go red, fix the README or fix
the measurement; never adjust the expected value to make the runner green.

---

## The three headline measurements

| Question | Command | Output | Needs |
|---|---|---|---|
| **Is the curve bought back inside the creation slot?** | `python3 code/v05_creation_block.py` then `v06_curve_ladder.py` | `data/v05_creation_block.json`, `data/v06_curve_ladder.json` | RPC (cached) |
| **What does an exit policy return, without any entry filter?** | `python3 code/t1_base_rate_sorties.py` | `docs/tables/T1_base_rate_sorties.md` | nothing |
| **What happens past the 20-minute capture window?** | `python3 code/fetch_gt_ohlcv.py` then `t5_horizon_1h_24h.py` | `docs/tables/T5_horizon_1h_24h.md` | public HTTP, no key |

### 1. On-chain verification of the creation-slot signature

The claim is that the whole bonding curve is bought back within the token's
*creation slot*. `v05` deliberately **does not start from the operator wallets**
— that would be circular. It takes the 42 creation slots, pulls the full block,
enumerates *every* successful buy of the mint in that block whoever the signer
is, and calls "buy block" the set of buyers above 5 SOL. Identity is used only
to pick which tokens to look at, never to decide what counts.

```bash
export HELIUS_API_KEYS=...          # free tier is enough
python3 code/v05_creation_block.py  # 42 getBlock calls, cached under data/cache/
python3 code/v06_curve_ladder.py    # SOL spent, share of supply, price ladder
python3 code/v08_ages.py            # birth date of each wallet (paginated walk)
```

Once `data/cache/` is populated the scripts re-run offline. The 42 blocks and
859 transactions already fetched are ~437 MB, which is why the cache is
git-ignored while everything derived from it is committed.

### 2. Exit-policy backtest

`t1_base_rate_sorties.py` is the quantitative core, and it is written to be
attacked:

* the simulator is **re-implemented from scratch** in that one file — it reads
  the raw swap stream and nothing else — and is then reconciled **token by
  token** against a second, independently written implementation. The
  agreement block prints at the end of the run (it needs the unpublished
  working corpus; the archived result is in `docs/PITFALLS.md`, pitfall P2);
* **no lookahead**: a decision taken on the 30 s bucket *k* executes at
  `t_e + 30(k+1)`, because the price of bucket *k* is only known once it
  closes. On this data the price moves 6.2 % per 30 s step in the median, so
  this single detail is worth ~150 PnL points on one token;
* **unfilled exits count as −100 %** (primary column). The `_excl` column,
  which throws them away, is published *only* to show how much return that
  optimistic convention manufactures;
* **censoring**: no exit is scheduled past `last_swap − 120 s`, so every fill
  has 120 s of future flow available to verify it. A −100 % can therefore never
  be an artefact of the recorder stopping;
* **n is counted in clusters and in UTC days**, not only in tokens: two tokens
  from the same launch are not independent observations. The confidence
  intervals bootstrap at the *cluster* level.

```bash
python3 code/t1_base_rate_sorties.py      # 15 policies, ~7 s
python3 code/t4_entree_post_snipe_20min.py
```

### 3. Price-horizon extension

Captures stop at 20 minutes, so "what if I had waited?" cannot be answered from
them. `t5` re-anchors on hourly GeckoTerminal candles.

```bash
python3 code/fetch_sol_usd.py     # SOL/USDC hourly series
python3 code/fetch_gt_ohlcv.py    # per-token OHLCV (289 tokens, no key)
python3 code/t5_horizon_1h_24h.py
```

Swap prices are **SOL per token**; GeckoTerminal returns **USD per token**.
Dividing one by the other without converting inflates every multiple by the
price of SOL (~73× over this window). `t5` converts through the hourly series
**and then verifies the conversion against the data itself**: for each token it
compares the open of its first candle (USD) to the robust price of its first
seconds of swaps (SOL); the ratio must reproduce the SOL price. That check
prints on every run.

---

## What needs a key, what does not

| Class | Scripts | Requirement |
|---|---|---|
| **Offline** | `p0`, `m1`–`m6`, `t1`–`t5`, `a1`–`a7`, `a9`, `exit_ladder`, `p1` | nothing. `data/` only. |
| **Public HTTP, no key** | `fetch_sol_usd`, `fetch_gt_ohlcv` | GeckoTerminal, ~300 requests, rate-limited client |
| **Solana RPC** | `v05`–`v08`, `v1_*`, `v2_*`, `r1_*`, `a8_wallet_horde`, `09_bundle_snipe` | `HELIUS_API_KEYS` (free tier) |
| **Unpublished raw corpus** | `v01`–`v04`, `make_public_data` | `PUMP_PRIVATE_ROOT` |
| **Unpublished deposit address** | `expl_ledger` | `EXPL_LEDGER_ADDR` **and** `HELIUS_API_KEYS` (a populated `data/cache/` replaces the key, never the address) |
| **Figures** | `f_*` | `matplotlib`, the only third-party package anywhere |

```bash
cp .env.example .env      # git-ignored; or just export the variables
```

`.env.example` documents the format and contains no value. Keys are read by
`settings.helius_keys()` and by nothing else; no script writes a key to disk,
and `settings.redact_key()` strips them from anything printed. Several keys can
be given comma-separated: the clients rotate round-robin and fail over on
429/5xx, which is what lets the deep history walks finish.

**Call budget.** `v05` 42 `getBlock`; `v06`/`v07` ~860 `getTransaction`;
`v08` a backward `getSignaturesForAddress` walk capped at 40 pages per address
(a wallet past the cap is flagged `censure=true`, so its birth date is reported
as an *upper bound* rather than silently truncated); `r1_*` paginate the
enhanced-transactions endpoint. Everything is cached on first fetch.

---

## The deposit-wallet ledger (`expl_ledger.py`)

The one measurement in this repository whose subject is the author's own money
rather than someone else's chain. It answers a single question — *what actually
landed on the exchange deposit address between 2024-10-01 and 2025-02-02?* — and
it exists because five figures in the root `README.md` were asserted rather than
measured. They are now measured, and the prose moved onto the measurement rather
than the measurement onto the prose.

```bash
export EXPL_LEDGER_ADDR=<base58 address>   # never committed, see below
export HELIUS_API_KEYS=...                 # first run only
python3 code/expl_ledger.py                # -> docs/out/expl_ledger.json
```

| | |
|---|---|
| **Incoming** | the deposit wallet's own *positive* balance delta on a successful transaction. 259 transfers, 1 226.4663 SOL, 244 315.58 USD over the window |
| **Outgoing** | the exchange's sweeps, 190 of them, 1 226.4566 SOL — reported **separately and excluded** from proceeds |
| **Pass-through check** | 1 226.4663 in vs 1 226.4566 out, residual 0.0098 SOL. A deposit address holds no balance, and that is what validates the model |
| **Price** | Binance `SOLUSDT` **daily close, per transfer, on that transfer's own UTC day** — never one average price over the window. `missing_price_days` is `[]`, and a missing day would raise rather than default |
| **Cache** | every RPC response and the kline series land in `data/cache/` (git-ignored, 455 files). After the first run the script needs the address but no key and no network, and reproduces the artefact byte for byte |

**The total is the net of every incoming transfer, winners and losers alike.**
There is no best-trades table anywhere and there will not be one: the number is
strong *because* it already absorbs the losing trades.

**What the artefact publishes, and what it refuses to.** Per-month SOL/USD/n,
window totals, sweep totals, counts — and nothing else. No transaction
signature (one is enough to identify the wallet), no sender address. For the 80
distinct senders, the **count** is published, never the list. Most are the
author's own trading wallets, but the same heuristic resolves four of them to
third-party exchange hot wallets this repository labels elsewhere, so ownership
is not claimed: the artefact files any identity behind a sender under
`NON_ETABLI`.

Two limits are stated in the artefact itself rather than left for a reader to
discover. Sender attribution is a **heuristic** — the counterparty with the most
negative delta in the same transaction — so it bounds the distinct-sender count
but is not an exact transfer-level decomposition; this is why the *counts* are
weaker than the *money*. And an incoming transfer is not provably proceeds: SOL
sent back from the exchange and re-deposited would be capital returning. Every
positive delta is counted (that is the measurement), and the number of incoming
transfers whose heuristic sender is also a sweep recipient — the only
return-of-capital signature visible from this wallet — is measured and published
so a reader can subtract it. It is 0.

**Privacy: the address is never committed.** It is a KYC'd exchange deposit
address, so publishing it in the clear would attach a legal identity to this
dossier permanently. It is read from `$EXPL_LEDGER_ADDR` exactly like
`PUMP_PRIVATE_ROOT` (`settings.expl_ledger_addr()`, clear
error when unset), and everything committed names it **only by its redaction
label**, `RDCT-0a350b2ba8` — the artefact, and the cache filenames too. The
script refuses to run at all if that label is missing from
`code/redactions.json`, so the scrubbing cannot be forgotten; redaction happens
at write time inside `pumplib.emit`, not as a post-hoc pass. Anyone already
holding the address can hash it and confirm the label. That is the whole point:
verifiable on demand, without publishing the address. `check_no_secrets.py`
passes on the result. It stops the address being read off this repository; it
does not make the wallet unfindable, since the published aggregates are
themselves a fingerprint that can be matched against the chain.

`run_all.py` lists it as `[addr+net]` and skips it with the missing condition
named — `needs $EXPL_LEDGER_ADDR` or `needs $HELIUS_API_KEYS or a populated
data/cache/` — so a clean clone reports a reason instead of a failure. Its
artefact lives in `docs/out/`, so `--strict` byte-compares it like every other.

---

## Reproducibility

**Two corpora, same numbers.** Measurements read
`data/floor_capture_public.jsonl.gz` (293 captures, 511 508 swaps, committed).
Set `PUMP_PRIVATE_ROOT` and the exact same code reads the 645 raw capture files
instead. The published corpus is rounded to 6 significant digits on `sol` and 8
on `tokens`/`price` — **T1 comes out bit-identical either way**, all 15 policies,
which is the empirical answer to "does your rounding matter". Rejection counts
are reported identically too: the 352 empty captures dropped at publication time
are read back from `data/MANIFEST.json` rather than silently disappearing.

**Determinism was a bug, then a fix.** `Counter.most_common` leaves ties in
insertion order, which depends on hash randomisation — two runs of `m4` could
swap two addresses tied at 14 tokens. Sorting explicitly on `(-count, address)`
made the output stable across `PYTHONHASHSEED`. The rejection dictionary printed
in the table footers was sorted for the same reason.

**Sample mode cannot overwrite a published artefact.** `m1` and `m5` accept
`--data data/sample/floor_capture_sample.jsonl` (20 tokens, truncated at
+300 s, ~2 MB) to check the format on a small input. When `--data` is given the
default output is redirected to `data/sample/`, so a 20-token run can never
silently replace a 289-token table.

**Interpreter pin for byte-exactness.** The random resampling is
version-independent by construction (an explicit LCG, not `random`), so every
count reproduces on any CPython. Two *floating-point aggregates* do not: the
log-log ATH/MC elasticity in `t2` and the mean-based cluster-bootstrap CI in
`m5` differ in their last ~1e-15 across libm builds, so their committed JSON is
byte-identical on **CPython 3.12 and 3.13** but not on 3.9-3.11 (where the code
still runs and every rounded figure is unchanged). CI therefore pins the
`--strict` byte comparison to 3.12/3.13; that is the honest scope of "byte for
byte", and the fix if you want the full 3.9+ matrix green is to round those two
15-digit values to a meaningful precision.

---

## Before publishing

```bash
python3 code/check_no_secrets.py [--identity personal_strings.txt]
```

Exits non-zero on: 32-hex/UUID/`sk-` literals, Telegram tokens and bot handles,
`api-key=` in a URL query string, absolute home paths (`/Users/...`, `/home/...`), credential files
(`.env`, `*.pem`, session dumps), any key currently live in the environment,
personal strings from an out-of-band list, oversized files, and unapplied
redactions. `"I checked"` becomes a command with an exit code.

Two deliberate refinements, each from a false result it produced:

* `11111111111111111111111111111111` is the Solana System Program id and matches
  "32 hex" in every account dump — matches made of ≤ 2 distinct characters are
  not keys;
* the scanner's own pattern table matches its own patterns — lines carrying
  `# noqa: leakscan` are exempt, rather than exempting the whole file.

### Redaction — one narrow exception to publishing addresses in the clear

Addresses and mints are public chain data and are published unmasked on
purpose: masking them would make every claim unverifiable. The exception is that
a *vanity* address is chosen by whoever ground it, and a few identifiers here
were ground to carry a racial slur in their leading characters.

`code/redactions.json` maps `sha256(identifier) → RDCT-<10 hex>`. **It contains
hashes only**: the repository holds neither the offending strings nor the word
list used to find them (that list is passed to `build_redactions.py --wordlist`
from outside the repo). Anyone already holding an address can confirm what it
became by hashing it. Labels contain a hyphen, so they can never be read as
base58, and the substitution is injective — every count, cluster and graph
measure is unchanged. 43 identifiers out of 212 201 scanned (0.02 %), none of
them in the operator clusters the dossier analyses.

A 44th entry is there for **privacy rather than decency**: the exchange deposit
address measured by `expl_ledger.py`. Same machinery, different reason — see
*The deposit-wallet ledger* above.

Redaction is applied **at write time**, inside `common.dump_json`,
`pumplib.emit`, `lib_verif.save` and `r1lib.save` — not as a post-hoc pass. A
re-run from the raw network cache, which still holds the original strings,
therefore cannot undo it. `sanitize_data.py --check` verifies the invariant.

> The first version of this got it wrong in an instructive way. A Solana
> *signature* is 87–88 base58 characters, so a plain `{32,44}` pattern matched a
> 44-character **window inside** a signature — and a slur can occur by chance
> inside an 88-character random string. The scrubber duly rewrote that window
> and silently corrupted the signature, leaving it unverifiable on any explorer.
> The pattern is now anchored on both ends, and `sanitize_data.py` fails hard if
> it ever finds a label welded to base58 characters, because that failure is
> invisible otherwise.

---

## Script index

**Shared**
| File | Role |
|---|---|
| `settings.py` | the only path resolution and the only credential read in the package |
| `pumplib.py` | corpus loading, conventions, proof levels (`[MESURE]` / `[INFERE]` / `[NON ETABLI]`) |
| `common.py` | capture filter, robust price, cluster bootstrap, Wilson interval, table writer |
| `lib_verif.py` / `hlib.py` | Helius client, disk cache, backward signature walk |
| `r1lib.py` | stricter Helius client: distinguishes *empty page* from *quota error* and raises, so a paginated history can never be silently truncated |
| `redact.py`, `build_redactions.py`, `sanitize_data.py` | pseudonymisation |
| `check_no_secrets.py`, `run_all.py` | publication gate, runner |

**Measurements**
| File | What it establishes |
|---|---|
| `p0_pitfalls_check.py` | recomputes every figure quoted in `docs/PITFALLS.md` from `data/` alone |
| `m1_corpus.py` | corpus perimeter: what is in, what was dropped, why |
| `m2_entry_price.py` | price actually paid vs pool price |
| `m3_operators.py` | operator clusters by shared wallets — **and the three attacks on that result** |
| `m4_infra_ubiquity.py` | shared infrastructure, and how much of the graph it fabricates on its own |
| `m5_roundtrip.py` | round trip under 10 exit policies |
| `m6_horizon.py` | +1 h/+2 h/+4 h/+24 h, matched subset vs cross-section stated separately |
| `t1`–`t5` | the five published tables |
| `v01`–`v08` | on-chain verification chain, creation slot → curve → exit → wallet age |
| `v1_probe_addresses.py` | existence and activity of every infrastructure address the dossier quotes |
| `v2_dispatcher_burst.py`, `r1_*` | funding-burst geometry, and the dust/funding separation that kills "N wallets funded in T seconds" |
| `a1_null_model.py` | how often the split detector's own criteria fire on random wallet groups — **the measurement that retired criterion C** |
| `a2_recount.py` | every phase-1 token recounted under the criteria that survive `a1`, plus Fisher's exact test against both control groups |
| `a3_hub_origin.py` | phase-1 distribution hub: genesis, fan-out shape, and the upstream addresses that stay out of reach |
| `a4_selection_bias.py` | how far the phase-1 cohort is from a random sample, and which claims that forbids |
| `a5_author_pattern.py` | presence test of the funding-dispatch pattern, token by token |
| `a6_gateway_chains.py` | dated chains swap gateway -> distributor -> fresh wallets |
| `a7_cross_token_links.py` | are the per-token operations linked to each other? |
| `exit_ladder.py` | a mechanical exit policy stated as executable code and measured |
| `a9_g2y_prelaunch.py` | act I: the pre-launch funding burst — nine wallets, one amount to nine decimals, 343 s — and the two collections of that token that disagree |
| `expl_ledger.py` | what actually landed on the exchange deposit address, 2024-10-01 → 2025-02-02: every incoming SOL transfer, valued at its own UTC day's close, plus the pass-through check against the exchange's sweeps |
| `p1_readme_check.py` | recomputes every figure quoted in the root `README.md` from the committed artefacts; **exits non-zero on disagreement** |
| `make_public_data.py` | builds `data/` from the raw corpus; published so the reduction is auditable |
| `f_*` | figures |

---

## Limits

* **One window**, 2026-06-27 → 2026-07-04, 645 capture files. Everything here is
  conditional on it. No claim is made about other periods.
* **Captures stop at 20 minutes.** Beyond that the source is hourly candles,
  with a coarser granularity and its own coverage gaps (`t5` reports the
  no-candle share with a Wilson interval instead of dropping those tokens).
* `v01`–`v04` need the unpublished corpus. Their **outputs** are committed, so
  the downstream chain stays checkable without it.
* Addresses are technical identifiers observed on a public ledger. No intent and
  no identity is attributed to any of them.
