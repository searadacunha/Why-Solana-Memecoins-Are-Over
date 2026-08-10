# Technical results — microstructure of pump.fun launches

> **Summary.** Three measured results on a 7-day capture of Solana memecoin launches
> (645 capture files, 293 with swap flow, 282 with identified early buyers, 511 508 swaps).
> **(1) Launch mechanics.** On 42 launches verified transaction-by-transaction, the entire bonding
> curve is bought inside the *creation slot itself* — median 85.2 SOL for 79.0 % of supply, with
> **zero** curve purchase preceding it in 42/42 cases. The position is transferred out at a median
> **t+17.5 s**. Median market cap goes from ~$2,158 at launch to ~$53,985 when the first external
> buyer can transact: **×25 before the market opens**. On a separate frozen sample of 70 tokens that
> reached ≥ $500k, **58/70 = 82.9 %** [95 % CI 72.4–89.9] carry this creation-slot signature.
> **(2) Operator clusters.** A token–token graph is dominated by 9 shared-infrastructure addresses:
> removing them collapses the giant component from **180/282 to 57/282 tokens**. Once cleaned,
> 6 disjoint clusters cover 76/282 tokens, with intra-cluster wallet reuse of 0.90–1.00 against a
> **0.019 base rate**. Two clusters sharing *no wallet and no token* nonetheless share a byte-level
> execution fingerprint — a shared tool, not a shared identity.
> **(3) Cost to a buyer.** Across **15 exit policies** on 196 tokens / 20 clusters, the mean is
> negative **15/15** and no policy has a 95 % CI (cluster bootstrap) above zero. 21.3 % of tokens
> (n=1243) have already peaked at first external visibility, 50 % within 120 s.
> **What is deliberately not claimed:** operator identity does not predict how high a token goes
> (p = 1.000), the clusters' tokens perform *below* baseline, and the ≥$500k sample is not random.
> Every figure regenerates from `code/` + `data/` with no network access.

**Window**: 2026-06-27 → 2026-07-04 (7 UTC days). **Scope**: pump.fun launches known as
*fast-grad* (fast graduation to the AMM). All addresses and signatures quoted are public technical
identifiers, verifiable on a Solana explorer. No intent, no identity and no person is attributed
to them: this document describes a market microstructure.

---

## 0. The corpus, and what it does not cover

| quantity | value | source |
|---|---|---|
| capture files | 645 | `data/v01_corpus.json` |
| captures with swap flow | 293 | idem |
| captures with identified early buyers | 282 | idem |
| swaps (raw recount) | **511,508** | idem |
| distinct addresses | 91,353 (raw) | idem |
| distinct sniper wallets | 1,616 (2,894 occurrences) | idem |
| launches verified transaction by transaction | **42** | `data/v05`, `v06`, `v07` |
| tokens ≥ $500k re-audited on-chain | **70** (frozen 2026-07-29) | `data/v09_signature_gros_tokens.json` |

⚠️ **A counting gap, acknowledged.** `docs/out/m1_corpus.json` publishes 476,847 swaps and 90,979
addresses, about 7 % less than the raw recount above. `m1` applies an additional filter that is not
documented in its header. Both figures are published; **no result in this document depends on this
total**, which serves only to describe the size of the corpus.

⚠️ **Real sensor coverage: 6.8 %.** `floor_capture` sees only **282 / 749** fast-grad tokens of its
own window (0.377), and over-samples winners (share with ATH ≥ $200k: 0.337 among captured tokens
versus 0.255 among non-captured ones). Combined with the cluster-attribution rate (0.181), the real
end-to-end coverage is **6.8 %**. The corpus is therefore **not** a representative sample of the
flow: it is a sample biased toward the launches that worked, and every result below must be read
that way.

---

## 1. The reconstructed operating method

### 1.1 The move, measured on 42 launches

The pump.fun bonding curve graduates to the AMM at around 85 SOL. On the 42 launches reconstructed
transaction by transaction, that curve is bought back **in full, inside the token's creation slot**,
before anyone else can transact.

**Table A — The common move (n = 42 launches, 4 clusters)**

| measurement | median | Q1–Q3 | min–max | source |
|---|---|---|---|---|
| SOL committed in the creation block | **85.21** | 83.12 – 85.72 | 79.49 – 87.46 | `v05` |
| share of total supply grabbed | **78.95 %** | 78.31 – 79.09 % | 76.78 – 79.25 % | `v05` |
| share of the curve captured | 79.09 % | — | 77.60 – 79.29 % | `v06` |
| share of the curve's SOL captured | **98.72 %** | — | — | `v06` |
| curve purchases **before** the block | **0** | — | max = 0 SOL (**42/42**) | `v06` |
| intra-core time gap | **0 s / 0 slots** | — | 42/42 | `v02` |
| CV of the tickets inside the block | 0.0265 | — | — | `v05` |
| creator's dev-buy | 0.068 SOL | — | — | `v06` |
| block size | 4 wallets (33 cases) / 5 wallets (9 cases) | — | — | `v05` |

Two rows carry most of it:

- **`curve purchases before the block = 0, on 42/42`.** This is not "the operator is fast": it is
  that there is **no window at all** between the token's creation and the curve buyback. The first
  possible external buyer arrives after.
- **`intra-core time gap = 0 s and 0 slots, on 42/42`.** The 4 (or 5) purchases are in the same
  Solana slot. No external observer, however fast, can slip in between.

### 1.2 The price staircase

![F1 — market-cap staircase](../figures/f1_escalier_capitalisation.png)

**Table B — Median market cap at each step (n = 42)**

| step | median MC | ×  vs launch |
|---|---|---|
| launch (untouched curve, 27.96 SOL constant) | **$2,158** | ×1 |
| execution of the creation block | $8,321 | ×3.9 |
| after the block's last ticket | $26,093 | ×12.1 |
| **AMM open = first possible external buyer** | **$53,985** | **×25.0** |

Ratio AMM open / block execution: **median ×6.54** (n = 42, range 0.22 – 14.57;
**40/42 ≥ ×3**).

**Independent convergence.** This ×25 is found again on **another population with another method**:
`docs/out/m2_entry_price.json` measures, on the **293** captures, a median market cap of
**706 SOL at the first externally observable instant** against the launch constant of
27.96 SOL, i.e. **×25.2** [95 % CI 672 – 724 SOL]. The share of the launch → peak log-run already
consumed at that instant is **0.90 in median**. Two measurements with no shared code, 0.2 points
apart.

### 1.3 Five verifiable launches

Each row is a public mint. The slot, the number of block wallets, the SOL committed and the transfer
delay are verifiable on a Solana explorer from the mint alone.

**Table C — Five launches, end to end**

| mint | cluster (lead) | creation slot | block wallets | block SOL | supply grabbed | purchases before | block MC → AMM open | bag transfer (median) | collectors |
|---|---|---|---|---|---|---|---|---|---|
| `87QChghgFr2XBNumi2Tg1MJCWHLqoTTT5KThtnDspump` | C1 `22vL22Pc…` | 429,307,208 | 4 | 84.94 | 78.05 % | **0** | $8,401 → $122,404 | t+23.5 s (19–35) | 3 |
| `DuiJLBQbnW7q5DibZNUckqtQbPMpMrXyc81iSNmzpump` | C1 `22vL22Pc…` | 429,722,432 | 4 | 85.23 | 79.10 % | **0** | $8,317 → $60,423 | t+14.0 s (9–18) | 4 |
| `9hrV5rTGN7s2noUZwo84kpFZKmhsnRuMS6AVMs1upump` | C2 `339QJtzB…` | 429,338,545 | 4 | 82.08 | 77.99 % | **0** | $8,125 → $52,951 | t+16.5 s (6–27) | 4 |
| `hCVRw8Qq9e8ZTeGYzWBoY8G5GvhDdkoMDmy4MWypump` | C3 `2GMhqu3c…` | 429,414,857 | 4 | 84.81 | 78.84 % | **0** | $8,304 → $51,938 | t+22.0 s (14–35) | 4 |
| `ALbvXciC8k4P3G57b4hMRPypvvsc2Rr9K4WucSwLpump` | C4 `2LLHCtDp…` | 430,477,517 | 4 | 79.49 | 77.45 % | **0** | $7,923 → $59,736 | t+13.0 s (13–13) | 4 |

The 5 tokens have **5 different creators** (`78wF7WAi…`, `Gcdpw19Y…`, `9vivFUKu…`, `E7B2ojFo…`,
`EaopWCEj…`). None is reused. See §2.3: this point disqualifies the reading "these clusters
launch the tokens".

### 1.4 The template is deterministic — and it can be proven

While verifying table C, five launches of cluster C2 turned out to carry values **identical to the
fourth decimal**: same 4 tickets `[21.1299 / 20.8140 / 20.4678 / 19.6699]`, same
`tokens_bloc = 779,852,771.1`, same supply share `0.77985`, on five different tokens.

A perfect repetition is first of all a signal of a **data bug** (a duplicated record). The check was
done before any publication:

| check | result | conclusion |
|---|---|---|
| creators of the 5 tokens | **5 distinct creators** | not a duplicate |
| execution order of the 4 wallets | **different** on 3 of the 5 | not a duplicate |
| slots | 5 distinct slots, spread over ~23,000 slots | not a duplicate |
| dev-buy in **tokens** | `3,564,784.69` — identical | *explains* the repetition |
| distinct `tokens_bloc` values across the 42 | **35 / 42** | the repetition is local, not global |

**Diagnosis**: the dev-buy purchases a **fixed quantity of tokens**, so the state of the curve at
the block's entry is identical from one launch to the next; a buy ladder itself expressed in token
quantities then costs an amount of SOL identical to the fourth decimal. This is not a data
artefact: it is a **hard-coded execution template**, and the constancy of the figures is its most
legible signature. Cluster C2's inter-launch CV is **0.0075** (`v02`).

### 1.5 The exit

**Table D — Position exit (n = 42 launches, 177 block wallets)**

| measurement | value |
|---|---|
| wallets transferring their bag | **162 / 177** |
| wallets selling directly | 46 / 177 |
| share of the supply transferred (median) | **99.99 %** |
| delay to the first transfer | **median 17.5 s**, Q1–Q3 13.0 – 26.2 s, range 0 – 80 s |
| distinct collectors (2nd tier) | 41 |

The bag is almost never sold by the wallet that bought it: it is transferred as SPL, at
**t+17.5 s in median**, to a second tier of addresses that then liquidate in series. The forensic
report measures these liquidations at **119 to 194 tranches** of about 4 SOL spaced ~1.5 s apart
depending on the cluster (n = 42; counted per cluster, not per launch — to be read as an order of
magnitude).

**Wallet-age asymmetry** (n = 476 exactly dated wallets):

| population | n | median age at first snipe |
|---|---|---|
| token creator | 151 | **0.03 d (~45 min)** — 75.5 % are less than a day old |
| disposable sniper (1–2 tokens) | 267 | 0.22 d |
| cluster member | 58 | **32.5 d** (q75 = 118 d); the 4 "quad" clusters: 118 / 228 / 419 d |

The **creator** wallet is **disposable and fresh**; the **buying** wallets are **pre-provisioned in
batches and aged** for months before use, then reused across 6 to 14 launches. The 4 wallets of
cluster C3 were created **within 50 seconds** (2025-11-12) and used **228 days** later.

### 1.6 The signature on large tokens — and its three limits

A question asked separately: when a token reaches a high market cap, does it carry this opening
signature? An on-chain test **independent of the detector**, on a **frozen** sample of
70 tokens with ATH ≥ $500k (`code/f_signature_gros_tokens.py`).

| measurement | value |
|---|---|
| median ATH of the sample | $1,205,423 |
| curve bought back (≥ 60 SOL) **inside the creation slot** | **58 / 70 = 82.9 %** — Wilson 95 % CI **[72.4, 89.9]** |
| agreement "buyback within 30 s" vs "buyback inside the creation slot" | **70 / 70** |
| SOL committed in that slot | median **85.01** (81.79 – 85.01) |
| buyers in that slot | median 4 (1 – 13) |

The **70/70** agreement is the sharpest fact in the file: there is no intermediate case where the
curve would be bought back within a few seconds *without* being bought back in the creation slot.
There is no window — there is a closed door.

⚠️ **Three limits, to be read with the figure:**

1. **The sample is not random.** These are the first 70 tokens ≥ $500k in the order of the source
   file. The 95 % CI quantifies sampling error, not selection bias.
2. **The signature does not make tokens go up.** Within these same 70: median ATH **with** the
   signature (n=58) = **$1.13M**; median ATH **without** the signature (n=12) = **$2.33M**. The
   tokens *without* the signature go **higher**. It describes a start, it does not predict a
   trajectory.
3. **It is P(signature | large), not P(large | signature).** This measurement is conditioned on
   success. It says nothing about the share of sniped launches in the general flow, nor about the
   probability that a sniped launch succeeds. Confusing the two would be exactly the
   outcome-selection bias documented in `PITFALLS.md`.

### 1.7 A reconciliation found while writing this section

The two scripts `v05_creation_block.py` and `v06_curve_ladder.py` both compute the market cap at
AMM open. Their published medians diverge: **$46,147 versus $53,985**, and the disagreement covers
**42 launches out of 42**, with per-launch gaps up to a factor of 100 (one launch at $78 versus
$11,435).

Diagnosis: `v05` kept the **first swap that came along** and was driven by dust trades of
~0.002 SOL, whose implied price is aberrant. `v06` takes the **median of the PUMP_AMM swaps
≥ 0.1 SOL over the first 60 seconds** — its docstring explicitly declares that it corrects `v05`.

**`v06` is authoritative; the figures in this document come from it.** The episode is kept here
because it illustrates the project's central mechanism: two implementations of the same quantity, a
gap, and a robust estimation convention that settles it. Without the cross-check, the wrong value
would have been published — it already was, in `v05`.

---

## 2. Operator clusters by graph analysis

### 2.1 The trap first: clean before interpreting

![F4 — graph and infrastructure](../figures/f4_graphe_infra.png)

Building a token–token graph (edge if two tokens share ≥ 3 early buyers) over the
282 captures yields a **giant component of 180 tokens out of 282 (63.8 %)**. Read naively, it
describes "a single network covering two thirds of the market". That is wrong.

A small number of addresses buys an enormous fraction of **all** launches. They are not operators:
they are **services** used by everyone, which artificially link any pair of tokens.

**Table E — Ubiquity of the top 5 infrastructure addresses (n = 282 tokens)**

| id | tokens sniped | share of the corpus |
|---|---|---|
| **W1** | 165 | **58.5 %** |
| W2 | 99 | 35.1 % |
| W3 | 91 | 32.3 % |
| W4 | 70 | 24.8 % |
| W5 | 44 | 15.6 % |

**Removing 9 addresses of this type drops the giant component from 180 to 57 tokens (63.8 % →
20.2 %).** The "giant network" was a bridging artefact. It is the easiest trap to fall into on this
data, and the repository publishes the test that demonstrates it (`code/m4_infra_ubiquity.py`), not
just the conclusion.

Two classification corrections, kept because they cut both ways:

- **W1 had been labelled a "single-mint volume bot".** Wrong: over its last 500 transactions,
  45 distinct mints, dominant mint at 4.0 %. The test "≥ 90 % of txs on a single mint" passes on
  **0 wallets / 57**. W1 is excluded for **ubiquity**, not for being single-mint — the right reason
  matters.
- **`GeBJSHK4…` had been classified as infrastructure** by the clustering. Wrong: it is a creator of
  51 tokens buying its own. Classing it as infra would have caused it to be **missed**. An
  infrastructure filter that is too broad costs true positives.

### 2.2 What the graph yields once cleaned

**Table F — The 6 clusters (n = 282 captured tokens)**

| cluster | core addresses | tokens | wallets / launch | intra-cluster reuse | inter-launch CV | median SOL |
|---|---|---|---|---|---|---|
| C1 `22vL22Pc…` | 7 (**a stand-in replaces one regular mid-series**) | 14 | 4 | 0.904 | 0.146 | 84.97 |
| C2 `339QJtzB…` | 4 | 12 | 4 | 1.000 | **0.0075** | 80.90 |
| C3 `2GMhqu3c…` | 4 (**0 rotation over 10 launches**) | 10 | 4 | 1.000 | 0.0118 | 85.10 |
| C4 `2LLHCtDp…` | 4 | 6 | 4 | 1.000 | 0.0345 | 79.62 |
| C5 `yHCxHBEa…` | 1 + 12 sub-wallets | 24 | 1 | 1.000 | 0.316 | 84.9 |
| C6 `GeBJSHK4…` | 1 | 10 | 1 | 1.000 | **0.000** | **exactly 84.0, 10/10** |
| **comparison base** | — | — | — | **0.0191** | — | — |

**What makes these clusters solid:**

- **Reuse of 0.904 – 1.000 against a base of 0.0191**, a factor of ~47 to 52.
- **Co-occurrence**: on the C1 core pairs, lift **×20 to ×22**, p from 2×10⁻¹⁹ to 6×10⁻²⁴.
- **Total disjointness**: the 6 clusters share **no token** (0 pairs) and **no address**
  (0 pairs). They are not arbitrary pieces of a single blob.
- **Persistence beyond the window**: the 4 "quad" clusters are found still active **25 days after**
  the capture window, same wallets, same ticket, while their entire funding layer had been renewed
  in the meantime.

Coverage: **76 / 282 tokens = 27.0 %**. The rest of the corpus is atomised — **1,062 creators out of
1,183 (90 %) launched only one token** (n = 1,701 mapped tokens). The observed market is mostly
individual, not industrial.

### 2.3 What these clusters are not

**42 tokens, 42 different creators, zero repetition.** Clusters C1–C4 have no link to the wallets
that create the tokens they buy. The initial hypothesis — "these are launchers sniping their own
tokens" — is **refuted**: they are **demand-side** actors, buying the curve of tokens created by
others.

**And "bundle" is a misnomer here.** The dominant signer is worth exactly **1/n** on all tokens
(n = 42 for the quads, n = 187 outside clusters): **each wallet signs its own transaction**, 0/42
duplication. There is **no** atomic bundle with a shared fee-payer. The only atomicity mechanism
observed is a single-tip Jito bundle, on 2 clusters. The term is kept in the code for historical
reasons; it does not describe a technical fact.

> **Dismissed for lack of evidence.** The hypothesis of a historical transition "sequential and
> therefore observable purchases → atomic and therefore invisible bundle" is **not testable on this
> data**: walking back through the history has no depth (the oldest record reached is the same
> day). No dating is proposed. The word "atomic" is moreover refuted above.

### 2.4 Two software families, not six operators

Three independent technical axes give **the same partition** of the 4 quad clusters:

| | **{C1, C3}** | **{C2, C4}** |
|---|---|---|
| Address Lookup Tables | 100 % | partial |
| fees per transaction | 11,500 lamports | 6,500 lamports |
| Jito tip | none | **hard-coded recipient** (a standard client picks at random among 8) |
| ticket order | strictly decreasing **16/16** | non-monotonic |

Two clusters that share **neither wallet nor token** run the same binary, to the lamport. The
defensible inference is **"shared or sold tool"**, not **"same actor"** — and that distinction is
the result, not a rhetorical precaution.

### 2.5 The three attacks — what the graph does NOT allow one to conclude

A co-occurrence graph produces clusters even on noise. Three attacks were mounted against the
conclusions above; **they destroy their predictive part**.

**Attack A — the graph's null was blind to time.**
The initial null model (Chung-Lu, degree-preserving) gave "19 significant clusters". It ignores
that two tokens from the same day share buyers by mere temporal co-presence. With a null that
**preserves the day of each edge**: **1,502 false-positive pairs out of 6,024 (25 %)**, and the
null giant component reaches 564 wallets against 668 observed. Only the **perfect quads** survive
(1 observed, **0 in 30 replays**). The 6 clusters of table F are the survivors of this test; the
13 other "candidate fleets" are not.

**Attack B — operator identity predicts nothing.**

| test | result |
|---|---|
| permutation ANOVA, 4 operators, n = 46 tokens | identity explains `ATH ≥ $200k` at **p = 1.000** |
| out-of-sample test of the exact claim | **×1.162** on the selected tokens, **×1.167** on those that would have been discarded → identity is worth **−0.5 % relative** |
| best group | the **UNKNOWN** group (non-attributable cores): `ATH ≥ $300k` = **0.286** against 0.083 – 0.100 for the named clusters |
| tokens with a core signature (n = 54) | `ATH ≥ $300k` = **0.130** [0.064, 0.244] against **0.213** for the base (n = 268) |

**The identified clusters' tokens do worse than the market.** Their profit comes entirely from the
entry → AMM-open gap (§1.2), **not** from any ability to push the price up.

**Attack C — selecting the "best operator" is survivorship.**
A "k ≥ 8 tokens" rule applied walk-forward gives an apparent rate of 0.512 (n = 125). Without the
**2 addresses** that supply 55–64 % of the selected tokens, it falls back to **0.326** against a
base of 0.309: the rule had **memorised 2 addresses out of 822 creators**. A live rule applied
mid-window would not have picked the best operator — it was **5th of 22**. Equal-weighting by
creator (the real unit), 6 creators out of 13 have a positive residual: a coin flip.

**Conclusion of the section.** The graph **identifies** real, reproducible and persistent
structures. It **provides no predictive power** over a token's price trajectory. These two
sentences are the result; publishing the first without the second would betray it.

---

## 3. Quantifying the cost to the buyer

### 3.1 The move precedes the signal

**Table G — Where the price already is when an external observer sees the token (n = 1,243, 123 clusters, 20 days)**

| MC band at detection | n | ATH already past | ATH < +60 s | ATH < +120 s | median delay to ATH |
|---|---|---|---|---|---|
| 5k – 20k | 16 | 43.8 % | 62.5 % | 62.5 % | 0.1 min |
| 20k – 30k | 108 | 23.1 % | 55.6 % | 60.2 % | 0.5 min |
| 30k – 40k | 137 | 27.7 % | 60.6 % | 65.7 % | 0.3 min |
| 40k – 50k | 296 | 18.9 % | 44.6 % | 54.4 % | 1.7 min |
| 50k – 65k | 277 | 26.4 % | 46.6 % | 51.6 % | 1.6 min |
| 65k – 85k | 121 | 26.4 % | 52.1 % | 58.7 % | 0.9 min |
| 85k – 120k | 123 | 14.6 % | 31.7 % | 35.8 % | 6.7 min |
| 120k – 300k | 165 | 9.7 % | 17.6 % | 23.0 % | 36.1 min |
| **whole population** | **1,243** | **21.3 %** | **43.8 %** [41.1, 46.6] | **50.0 %** | **2.0 min** |

**21.3 % of tokens have already reached their maximum at the moment of their first external
visibility. 50 % reach it within 120 seconds.** This result depends on no model: it turns a market
question into a question of **latency**.

> **Corrected figure.** An earlier working note put forward "67 % of tokens had already reached
> their maximum". That 67 % is only found on the < $20k band of population A, where **n = 3**.
> The value on a clean population is **21.3 %** (n = 1,243). That is the one published.

### 3.2 Fifteen exit policies, all negative

![F2 — exit policies](../figures/f2_politiques_sortie.png)

Protocol: **systematic** entry at t0+120 s, **with no entry filter whatsoever**, on the 196
exploitable tokens (20 clusters, 6 days). Costs of **5.8241 % round-trip** (1 % fee + 2 % adverse
slippage per leg) already deducted. Live-safe decisions: a decision taken on a 30 s bucket executes
on the next bucket, never at the price that triggered it.

| result | value |
|---|---|
| policies with a **negative mean** | **15 / 15** |
| policies with a negative median | 12 / 15 |
| policies positive **both** in median and in mean | **0 / 15** |
| policies whose mean's 95 % CI (**cluster-level** bootstrap) is above zero | **0 / 15** |
| mean of the means | **−11.3 %** per round trip |

**The trap this table makes visible.** The only positive medians are tight take-profits, and their
expectation is **the worst in the table**: `tp30` shows a median of **+22.4 %** for a mean of
**−16.4 %**. Winning often a little, losing rarely a lot. Reading the median alone on a fat-tailed
distribution inverts the conclusion.

**No multiplicity correction is needed** here, and that is a property of the result:
it is negative everywhere, and sweeping more policies can only make a uniformly negative result
*harder* to obtain by chance.

### 3.3 Post-snipe entries, and the column that destroys its own result

Seven entry rules tested after the curve buyback, with a common exit at the end of the capture
(≤ 20 min).

| entry rule | n | median multiple | 95 % CI | % multiple > 1 | net mean | **mean without the best token** |
|---|---|---|---|---|---|---|
| graduation (+120 s) | 196 | **0.81** | [0.61, 0.93] | 40.3 % | −10.2 % | −13.8 % |
| retrace −20 % | 181 | 0.70 | [0.56, 0.91] | 38.1 % | −15.6 % | −19.5 % |
| retrace −30 % | 160 | 0.64 | [0.53, 0.84] | 35.0 % | −14.0 % | −24.2 % |
| retrace −40 % | 135 | 0.63 | [0.51, 0.84] | 33.3 % | **+16.6 %** | **−15.2 %** |
| retrace −50 % | 118 | 0.67 | [0.46, 0.80] | 28.0 % | **+22.3 %** | **−14.1 %** |
| retrace −60 % | 86 | 0.46 | [0.09, 0.73] | 23.3 % | **+23.9 %** | **−26.3 %** |
| retrace −70 % | 61 | 0.16 | [0.00, 0.51] | 16.4 % | **+13.1 %** | **−58.0 %** |

**No rule reaches a median multiple of 1.** The best is `graduation (+120 s)` at
**0.81×** [0.61, 0.93].

The mean turns positive on the deep retracements (−40 % to −70 %). **This is not an edge**, and the
table publishes the two controls that show it: (a) the **cluster-level** bootstrapped 95 % CI of the
mean crosses zero on each of those rows; (b) removing **the single best token** flips **all** of
those means back to negative, down to −58 %. A fat right tail carried by a handful of tokens is not
positive expectation.

### 3.4 What is left after a few hours

![F3 — decay by horizon](../figures/f3_horizon_decroissance.png)

Buy at the robust price of the last 120 seconds of the capture (~t0+20 min), sell at the `close` of
the hourly candle at the horizon. n = 191 tokens, 27 clusters.

| horizon | n with candle | no candle | median multiple | 95 % CI | % > 1 | whole population |
|---|---|---|---|---|---|---|
| +1 h | 189 | 2 (1 %) | **0.48** | [0.38, 0.61] | 18.5 % | 0.47 |
| +2 h | 185 | 6 (3 %) | 0.43 | [0.29, 0.54] | 18.4 % | 0.41 |
| +4 h | 179 | 12 (6 %) | 0.38 | [0.26, 0.49] | 15.6 % | 0.30 |
| +24 h | 144 | **47 (25 %)** | **0.20** | [0.05, 0.29] | 12.5 % | **0.03** |

The "whole population" column scores at **0.00×** the tokens that no longer have **any candle** at
the horizon, that is, no trading at all: it is the honest convention for an asset that can no
longer be sold. At +24 h, **25 % of tokens are in that case**, and the median multiple of the whole
population falls to **0.03×**.

**A units control published with the result.** The ratio (external price in USD / swap price in
SOL) divided by (SOL in USD) is **0.850 in median on n = 277**. Close to 1 ⇒ the conversion is
correct. Without that conversion, every multiple in this table would be **multiplied by ~76** —
a unit error would have turned a 78 % loss into a ×34 gain.

> **Corrected figures.** Earlier notes put forward "0.35× at +1 h and 0.08× at +24 h", and
> "50 % of tokens without volume". The values regenerated on the current corpus are **0.48×** and
> **0.20×** (0.03× on the whole population), and **25 %** without candle **at +24 h**. An earlier
> prose version of this section was itself stale (n = 128, 18 clusters); the figures of record are
> the committed table `docs/tables/T5_horizon_1h_24h.md`, regenerated at n = 191, 27 clusters.

### 3.5 Why one must not reason in multiples of the ATH

A natural reflex is to measure "how many times its entry price" a token reaches. **That target
manufactures results.**

- **Denominator artefact.** Measuring ATH / entry MC *mechanically* makes any variable correlated
  with the entry MC predictive, without it predicting anything. The measured elasticity
  log₁₀(ATH) ~ log₁₀(MC), demeaned by day, is **b = 0.884** (n = 1,243) — recomputed
  independently, **identical to the third decimal**. Corrective adopted: a **residual** target
  (residual of log(ATH) after regressing on log(MC)), and an explicit ban on `t_mult*` targets as
  a primary target.
- **b < 1 is real information, not a tautology.** Entering higher genuinely degrades the
  multiple; the relationship is not perfectly mechanical. The nuance is published with the figure.
- **Limitation (added on review): the economic reading of b is indicative, NON ÉTABLI (not
  established).** b = 0.884 is published **without a standard error or a confidence interval**; the
  measurement error on the entry MC (*errors-in-variables*) mechanically pulls the OLS slope
  **below 1**, so part of "b < 1" may be measurement noise rather than economics; and panel B (a
  near-flat ×2 rate per band, next point) is in tension with a causal reading of "entering higher
  degrades the multiple". The use of b as a **mechanical decomposition** (slope of the multiple
  = b − 1, denominator artefact) remains measured and reproduced; it is the causal reading that is
  not established.
- **The ×2 rate is nearly flat across observed-MC bands**: **42–48 % on every band above $30k**
  (n = 1,119 of 1,243). The two low bands are higher (55.6 % on $20–30k, n = 108; 75.0 % below
  $20k, n = 16), but they are also the ones where the ATH is most often already past
  (§3.1: 43.8 % and 23.1 %). Tokens that show up low also have a low ATH.
  There is no "good entry band".
- **With no free parameter at all**: the entry price that would give a 90 % chance of ×2 is
  **$24,385**, while the median MC at detection is ~$52k. The required price is already gone.
- **And "reaching the ATH" is not "selling at the ATH".** All the ×2 columns of this repository are
  **upper bounds**. §3.1 gives the collectable measure.

**Selection bias, quantified.** Filtering on a `buyable` field defined as "the ATH occurs after
detection" moves the ×2 rate from **38.3 % to 63.0 %** (B, n = 1,701 → 1,034):
**+24.7 points of success entirely manufactured**, since the filter mechanically selects the
tokens that went up. The details of this episode and of the six other traps are in
[`PITFALLS.md`](PITFALLS.md).

> **Corrected figure.** An earlier note put this median-ATH gap at "310 k versus 48 k,
> a factor of 6.4". The recomputation gives **272 k versus 62 k = a factor of 4.39** (B, n = 1,701;
> 2.55 on A, 3.09 on C). The mechanism is confirmed; the announced magnitude was not.

---

## 4. What this work establishes, and what it does not

**Established (measured, with n and CI):**

1. On 42 launches verified transaction by transaction, the bonding curve is bought back in full
   inside the creation slot, with **0 prior purchases on 42/42**, and the position is transferred at
   **t+17.5 s** in median.
2. The median market cap goes from ~$2,158 to ~$53,985 (**×25**) before an external buyer can
   transact — a value confirmed independently at ×25.2 on the 293 captures.
3. On a frozen sample of 70 tokens ≥ $500k, **82.9 %** [72.4, 89.9] carry this signature,
   with perfect agreement (70/70) between the two definitions of the window.
4. Six buyer clusters, disjoint in tokens and in addresses, with a wallet reuse of
   0.90–1.00 against a base of 0.019, persistent 25 days beyond the capture window.
5. For a buyer entering after this move: **negative mean on 15/15 exit policies**,
   **0/15** 95 % CIs above zero, and **0.20×** at 24 h (0.03× counting the tokens that became
   untradeable).

**Not established — and explicitly refused:**

- **No dating** of a historical evolution of the market: the data does not have the required
  depth (§2.3).
- **No predictive power** of a cluster's identity over a token's trajectory: p = 1.000,
  and the identified clusters' tokens do **worse** than the base (§2.5).
- **No strategy** is proposed. The main result of that section is negative.
- **No intent** is attributed to any address. Addresses are public identifiers;
  this document describes observable regularities, not actors.
- **No generalisation to the whole market**: the sensor's end-to-end coverage is **6.8 %**
  and the sample over-represents the launches that succeeded (§0).

---

## Notes

1. **Reproduction.** All figures and tables regenerate offline from `code/` and `data/`:

   ```
   python3 code/f_figures_resultats.py        # figures F1 to F4
   python3 code/f_signature_gros_tokens.py    # §1.6, frozen sample n = 70
   python3 code/m4_infra_ubiquity.py          # §2.1, component collapse
   python3 code/t1_base_rate_sorties.py       # §3.2
   python3 code/t3_ath_avant_detection.py     # §3.1
   python3 code/t4_entree_post_snipe_20min.py # §3.3
   python3 code/t5_horizon_1h_24h.py          # §3.4
   ```

   None of these scripts makes a network call or requires an API key.

2. **Anonymisation.** The infrastructure addresses are referred to as `W1`…`W5` in this document and
   in the figures. This is not a general precaution — on-chain addresses are public and appear
   elsewhere in the repository — but a one-off necessity: **the prefix of address W1
   constitutes a racial slur**, presumably chosen by its owner via a
   "vanity address". Reproducing it would serve its diffusion while adding nothing to the result.
   It is replaced by a redaction token (`RDCT-…`) everywhere in the published data; W1 remains
   fully identifiable by its metrics (165 tokens, 58.5 % of the corpus) for anyone who wants to
   redo the computation. The four other addresses of table E are anonymised only for consistency of
   presentation and appear in clear in `docs/out/m4_infra.json`.

3. **Order of magnitude vs measurement.** The liquidation-tranche counts (§1.5, 119–194) come
   from the forensic track and are aggregated **per cluster**, not per launch: to be read as an
   order of magnitude. All other values in this document are measurements on a declared n.

4. **Six corrected figures.** This document replaces six values from working notes that do not
   reproduce: the selection-bias factor (6.4 → **4.39**), the share of ATH already past
   (67 % → **21.3 %**), the 1 h and 24 h multiples (0.35× / 0.08× → **0.48× / 0.20×**), the share
   of tokens without volume (50 % → **25 % at +24 h**), and the swap total (476,847 → **511,508**
   raw, a filter gap documented in §0). A seventh gap — the two estimates of the market cap at
   AMM open — was found and settled while writing this document (§1.7).
