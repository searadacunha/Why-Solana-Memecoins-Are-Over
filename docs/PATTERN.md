# The gateway dispatch: a launch-funding pattern, and how to detect it

**What this chapter is.** A description of one funding mechanism visible on the Solana chain during
the 2024–2025 window, six worked examples with transaction-level evidence, and the code that
detects it automatically.

**What it is not.** A prevalence estimate. The tokens below were selected on their outcome, so
nothing here supports a statement of the form *"X % of launches work this way"* — see
[`SPLIT_PHASE1.md`](SPLIT_PHASE1.md) §5 and `code/a4_selection_bias.py`. Presence is what is
established; frequency is not.

> Every address, amount and timestamp is a public technical identifier, verifiable on any Solana
> explorer. The gateway address, written **G2Y** for brevity, is
> `G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t`, publicly attributed to a hot wallet of the swap
> service **ChangeNOW** by two independent sources — a [2025 research study on Solana
> mixers](https://medium.com/@smartgenuise806/the-shadow-economy-a-research-study-on-mixers-in-solana-3eebc60dcd2a)
> whose author observed his own test funds land there, and an [earlier public
> attribution](https://x.com/CrypticZK/status/1616072613356535808). Neither is an official exchange
> label; the identification is reported as **publicly attributed, not officially confirmed**.
>
> Reaching it is a **routing fact**. Capital entering Solana passes through some such service by
> necessity, a swap service processes what its users send it, and nothing measured here concerns
> what the service knew, intended or permitted. No involvement or wrongdoing is attributed to any
> service, company or person.

---

## 1. The mechanism

Four properties, required together:

| # | property | why it matters |
|---|---|---|
| 1 | the buyer wallet is **fresh** — created shortly before it buys, no prior history | a wallet with a past is a trader; a wallet born days before a launch was made for it |
| 2 | it is funded **directly by the swap service** | the entry point onto the chain, one hop from the buy — and the point at which prior provenance stops being traceable |
| 3 | the amount is a **conversion output** — nine significant decimals, not a round figure | `2.976816` is what a swap leaves; `3.000000000` is what someone chooses to send |
| 4 | the payment lands **before the token exists** | a payment after the launch cannot have funded it |

Properties 3 and 4 are what separate this from coincidence. Any active week produces two wallets
that happen to share a funder; it does not produce five wallets receiving the *same nine-decimal
amount* from the same gateway inside four minutes, hours before a token that does not yet exist.

### The two layers, which are easy to confuse

The gateway does not always pay the buying wallets. Sometimes it pays an intermediate address which
then fans the money out in **round** parts:

```
gateway ──(conversion output)──► distributor ──(round amounts)──► fresh wallets ──► buys
```

Both layers are real and they are one hop apart. A detector that requires a conversion output at the
wallet layer will miss every case that runs through a distributor — the first version of the
detector here did exactly that and returned zero on all fifteen tokens, including the reference
case. The rule that follows: **report the calibre, never require it.**

---

## 2. Six worked examples

### h2w6gm6jz — nine wallets, one amount, 343 seconds

Token created **2024-12-13 14:50 UTC**. Seven and a half hours earlier, **nine freshly created
wallets each received exactly 2.976815600 SOL** from the gateway:

| wallet | amount (SOL) | time (UTC) |
|---|---|---|
| `Csye9QE8LomP9RHzQAWLVh8XFdyNXvaopzrAuo3a1PoW` | 2.976815600 | 07:07:49 |
| `BmkuX6DaZUp9UCeR3XqAD6NjSpiFySnBvXyLT9uo7ZEA` | 2.976815600 | 07:08:02 |
| `AwQqcqdQQ3zydrtWMVF1PPDaWMNK7Lmhm3sUyDNGnSSY` | 2.976815600 | 07:09:04 |
| `3bBaA1MpQZuQpHjWZBEig12JB1W1TTQikxYPjUgGG3kU` | 2.976815600 | 07:10:12 |
| `CDvfNWiamAR1B84GUgttvDCGtiQE5dvJ49toF4fzsV5g` | 2.976815600 | 07:10:31 |
| `92w4K8uLg78KHWHxRovTDksLmou7MekcenY5PntPR34R` | 2.976815600 | 07:10:53 |
| `6QMshP9zwFXKbpLPh7w8EwadjA6vVasKAC7zu5HfMA22` | 2.976815600 | 07:11:20 |
| `BXuznwXTXt4QbLtLTkQnKNaXwdJ4PDXHvDcXf9DMogxe` | 2.976815600 | 07:11:53 |
| `5ibajLyeBmJhDfyZJN9FQsJBi48h8QSYg7eHGGhFjog6` | 2.976815600 | 07:13:32 |

Nine wallets, one amount to nine decimal places, 343 seconds end to end, from a single gateway,
hours before the token existed. The amount is a conversion output — not a figure anyone types.

### The same amount, on another token, a month earlier

**2.976815600 SOL** also lands on a fresh wallet of **SAFFRON** — `wbzkg9ftnVEMzeCL6wW8bpNTPDQWhBBnKo3JWJe3wh5`,
on **2024-11-12 13:16:45**, thirty-one days before the h2w6gm6jz burst and from the same gateway.

An identical nine-decimal amount recurring across two unrelated tokens a month apart is not what a
conversion produces by chance: a swap output depends on the size, the route and the price at that
instant. Repetition of the exact figure points to a repeated operation rather than a repeated
coincidence. Stated as an observation; no further inference is drawn from it here.

### ACID — found only by dropping the 40-buyer cap

Token created **2024-12-09 09:47**. Three fresh wallets, gateway-funded in the week before:

| wallet | amount (SOL) | time (UTC) |
|---|---|---|
| `DrL5h6A1CyH1XDVsFd78Fnn4Nkx37GrQzqcPiKAaoFiq` | 1.526056960 | 2024-12-02 09:53:14 |
| `DrL5h6A1CyH1XDVsFd78Fnn4Nkx37GrQzqcPiKAaoFiq` | 0.739421380 | 2024-12-03 07:27:43 |
| `RwdMax1heLzDiBSk3g3MgvRuJkQYz7tnj96RFpbxxVA` | 1.958393160 | 2024-12-08 10:18:22 |
| `D3JwQSGkn8YUzCDkMphDhVbsEeK9qbttU971cqmFEKRM` | 1.504465720 | 2024-12-08 21:39:19 |

ACID measured **zero** in every earlier pass. Those passes stopped at the first 40 buyers; this
token has **743**, and the relevant wallets sit further down the curve. The cap was the finding.

### SAFFRON — one wallet funded four times before the launch

Token created **2024-11-12 22:54**. Three fresh gateway-funded wallets, and one of them
(`wbzkg9ftnVEMzeCL…`) received **four separate payments in the nine hours before creation**:
2.976815600 at 13:16:45, 2.380415590 at 13:53:56, 9.894826000 at 14:16:27, 7.778694250 at 21:27:20.
Two others were funded the day before — 1.982815600 and 8.624207890 SOL.

Repeated top-ups into one fresh wallet on the day of a launch is a variant of the same mechanism:
the amounts differ, the direction and the timing do not.

### QAMI — two wallets, the day before

Token created **2024-12-31 23:41**. `6nGLeqP1BW1MWrMsC7EYA57iei1V5XfpEW7YqdgFNA4K` received
4.949823400 SOL on 2024-12-30 17:31:45; `E2wJyPwoJAydxYpvKSv1uRSS9GdEzX8gpfqeWsaVHcab` received
0.481875600 SOL on 2024-12-31 17:19:21, six hours before the token existed.

### sumiko — two wallets, seven minutes apart, the day of the launch

Token created **2024-12-26 13:25**. `AJq5My8GFG6Jo7Pq…` received 1.446086 SOL at **12:55:43** and
`FYG2cyAmhKGyRnH5…` received 0.739785 SOL at **13:02:00** — both fresh, both from the gateway, the
first twenty-nine minutes before the token existed.

### CHOCO — two layers of the mechanism on one token

Token created **2024-10-10 13:35**. Two fresh wallets gateway-funded beforehand:
`Edx7xy6RG8nchSE833xJNGjNBL4QdZV587Zk8GZ3Kpho` (1.207495600 SOL at 09:24:43 the same morning) and
`4f6geAMUGzekQd3HemzHKWhJN9DiquNwTTtypPZckMQ5` (2.307396470 SOL three days earlier).

The same token also carries the **distributor** layer: an address created that morning at 09:26,
paid by the gateway at 13:26, which at 13:31 fanned out to **20 fresh wallets at 0.300000000 SOL
each in a single transaction** — then was never used again, 30 signatures in its entire life. Two
layers of one mechanism on one token, four hours apart.

---

## 3. Detecting it automatically

Four scripts, stdlib-only, no key needed for the offline ones.

| script | what it does |
|---|---|
| `code/a5_author_pattern.py` | scans the funding of a token's buyers for fresh wallets receiving near-identical amounts in one burst; sweeps both free thresholds instead of picking one |
| `code/a6_gateway_chains.py` | rebuilds the dated chain gateway → distributor → wallets, and drops any link that is chronologically impossible |
| `code/a1_null_model.py` | how often each criterion fires on random wallets — run this **before** trusting any detector output |
| `code/a3_hub_origin.py` | walks a distributor back to its own genesis, declaring whether the genesis was reached |

```bash
python3 code/a5_author_pattern.py      # burst detection, with a threshold sweep
python3 code/a6_gateway_chains.py      # dated chains, chronology enforced
```

### The four rules that make the difference between a detector and a random-number generator

**Page to genesis, or declare that you did not.** `getSignaturesForAddress` walks present → past,
1 000 per call. Bounded too short it returns only *recent* history and fails **without an error**:
a wallet's funding lives in its *first* transactions, so a partial walk reports "no funding found"
for a wallet that was funded. Every negative must carry the scope it was measured on.

**Make failures loud.** A client that returns `None` on error, with a caller writing `or []`, turns
an exhausted quota into "this curve has no transactions". That produced a clean `0/14 tokens` in
this project — from a wrong hostname. Errors raise; unmeasurable tokens are counted separately from
tokens measured negative. Full episode: `PITFALLS.md` P15.

**Give every criterion a null distribution first.** Pool wallets that were never coordinated, draw
random groups, run the criterion unchanged. The most intuitive criterion here — *these buyers share
a funder* — fires on **88.9 %** of random 40-wallet groups. It was retired. `PITFALLS.md` P13.

**Enforce chronology inside the chain.** The gateway must pay the distributor *before* the
distributor pays the wallet, and the whole chain must precede the token. Without the first check the
chain builder here reported a gateway payment in 2024 feeding a wallet payment from 2022.

### Cheap trick that makes a full-curve scan feasible

A fresh wallet has, by definition, no activity before the window. So page its history backwards and
**stop the moment you see a transaction older than (creation − N days)** — the wallet is old, cannot
be fresh, and its funding is irrelevant. Hyperactive wallets with hundreds of thousands of
signatures exit in one page. This is what makes scanning *every* buyer on a curve tractable rather
than only the first forty, and dropping that cap is what surfaced ACID.

---

## 4. One actor per split — and how far that goes

A split is one actor. A transaction paying twenty wallets an identical amount has one signer, one
decision, one hand. That is not an inference, it is what a transaction is, and the repository states
it plainly: **each dispatch observed here was performed by a single actor.**

The open question is different: are the dispatches on *different* tokens the same actor, the same
tool, or unrelated users of the same gateway? Three tests (`code/a7_cross_token_links.py`), across
13 measured tokens and 75 gateway payments:

**Recurring exact amount — one hit, and a strong one.** `2.976815600 SOL` appears on two tokens
31 days apart: once on a SAFFRON wallet (2024-11-12 13:16:45) and nine times on h2w6gm6jz wallets
(2024-12-13, 07:07:49 → 07:13:32). A swap output depends on the size, the route and the price at
that instant, so the same nine-decimal figure recurring across two unrelated launches is not what
conversions produce by chance. This is the strongest cross-token link in the corpus.

**Shared wallets — one, and weaker than it looks.** `GbYqi5jYdzNf6iKvfP1KWg7FyHhECMsZ5yYd7micig8h`
bought on both ACID and symx. But its gateway payment is dated 2025-01-23, *after* both tokens
existed, so it links the two launches as a **buyer** without supporting the funding pattern on
either. Reported at that strength.

Note what a null result would have meant here: an operator who burns addresses leaves no shared
wallets by construction, so few shared wallets is equally consistent with one careful actor and with
many unrelated ones. This test can raise the link, not lower it.

**Funding sessions — nothing.** Grouping payments separated by less than six hours gives 14
sessions, **none** touching more than one token. The dispatches are not batched together.

### What this supports, and what it does not

Two of the thirteen token pairs are linked by hard on-chain evidence. That is more than "unrelated
users of a common gateway" and less than "one person wrote all of it".

The alternative that survives is **a shared tool**, and it is not hypothetical: this repository
already documents two operator clusters that share *no wallet and no token* and nonetheless share a
byte-level execution fingerprint — the same software, run by different hands. A repeated method is
evidence of a repeated method. Getting from there to a repeated person requires an artefact that
identifies the hand rather than the technique, and none of the three tests above produces one.

So the repository writes what it measured: the dispatches are performed by single actors, at least
two of the operations are linked to each other, and the identity behind them is not established.

## 5. What the wallets do next: a fleet, not confetti

Every measurement above looks *upstream* — who funded the buyer. Looking the other way turned out to
be the direction that mattered, and it corrects something this repository had wrong.

Two models predict different things. A **disposable** wallet receives, buys, sells and dies: no
outgoing payments to accounts that did not already exist. A **fleet** wallet is kept, reactivated,
and used to fund fresh wallets that go on to fund others. The discriminating measurement is how many
of a wallet's later payment recipients were **born on receipt** — first activity within an hour of
the payment. Paying an address that comes into existence at that moment is not a transfer between
accounts; it is a wallet being created.

`code/a8_wallet_horde.py`, on the 14 readable gateway-funded wallets:

| | |
|---|---|
| wallets that went on to fund at least one **brand-new** address | **14 of 14** |
| new addresses spawned in total | **129** |
| median lifetime after the trade | 3.9 days |
| longest still active | **+356 days** |

Fourteen out of fourteen. Not a tendency — the behaviour of every wallet measured.

**The extremes make the shape clear.** `4f6geAMUGzekQd3HemzHKWhJN9DiquNwTTtypPZckMQ5`, a CHOCO
buyer, ran to **1 880 transactions** and was still active **356 days** after its trade, funding
**150 addresses of which 19 were newly born** — including 120.8 SOL to an address created that same
week. `291vRVW6QcL8Lj3F…` (SAFFRON) funded **47 addresses, 19 of them new**. These are not the
account histories of someone who bought a memecoin.

**And the h2w6gm6jz batch behaves as one object.** The nine wallets that received an identical
2.976815600 SOL within 343 seconds do not merely start together — the six whose history is readable
all **stop on the same day, 2024-12-17**, exactly 3.9 days after the launch, each having spawned
between 6 and 9 new addresses in the interval:

| wallet | last activity | addresses funded | of which newborn |
|---|---|---:|---:|
| `CDvfNWiamAR1B84G…` | 2024-12-17 | 21 | 8 |
| `BmkuX6DaZUp9UCeR…` | 2024-12-17 | 19 | 6 |
| `6QMshP9zwFXKbpLP…` | 2024-12-17 | 22 | 7 |
| `5ibajLyeBmJhDfyZ…` | 2024-12-17 | 20 | 6 |
| `AwQqcqdQQ3zydrtW…` | 2024-12-17 | 23 | 9 |
| `3bBaA1MpQZuQpHjW…` | 2024-12-17 | 18 | 7 |

Six wallets funded in the same burst, retired on the same day, each leaving behind a similar number
of children. Independent users do not synchronise their last transaction.

### The correction this forces

Section 4 reports no shared funder between the per-token distributors and concludes that the
operations are linked only in pairs. That test looked **upstream only**, and upstream is where a
careful operator leaves nothing: each launch gets its own distributor precisely so the ancestry does
not converge.

Downstream, it converges anyway. The wallets are not consumed by the launch — they survive it and
become funders themselves, which means the addresses buying later launches can be the descendants of
the ones that bought earlier. That is a materially different structure from "unrelated users of a
common gateway": it is a standing population, replenished from within.

What it still does not establish is a hand. A fleet of thousands of addresses spawning generations
is equally the signature of one operator with a script and of a tool many operators run. Section 4's
verdict is unchanged in that respect — but its *reasoning* was wrong, and the reason it was wrong is
that it only looked one way.

## 6. What was scanned

Every buyer on the curve, not a sample: 3 963 distinct buyers across thirteen tokens. One token
could not be read at all and is reported as unmeasurable rather than as a zero.

| token | curve buyers | fresh | unreadable | **gateway-funded before launch** |
|---|---:|---:|---:|---:|
| `h2w6gm6jz` | 223 | 67 | 90 | **9** |
| `ACID` | 743 | 188 | 0 | **3** |
| `SAFFRON` | 265 | 57 | 105 | **3** |
| `CHOCO` | 289 | 78 | 114 | **2** |
| `QAMI` | 266 | 59 | 107 | **2** |
| `sumiko` | 290 | 96 | 116 | **2** |
| `BLT` | 194 | 89 | 0 | 0 |
| `LEXICON` | 80 | 17 | 32 | 0 |
| `MIKU` | 804 | 173 | 322 | 0 |
| `OPTIMUS` | 246 | 53 | 99 | 0 |
| `POLMRKTBOT` | 315 | 67 | 126 | 0 |
| `RAO` | 143 | 42 | 58 | 0 |
| `symx` | 105 | 31 | 42 | 0 |
| `VISUALIZE` | — | — | — | *unmeasurable (HTTP 429)* |

**Six of thirteen** measured tokens carry the pattern.

The **unreadable** column is the one to read carefully, because it decides what a zero is worth.
Those wallets could not be paged back to their first transaction, so their funding origin is
unknown. `MIKU` has 322 of them and `OPTIMUS` 99 — their zeros are weak. `BLT` has none, so its
zero is a real negative, and `ACID` has none either and is positive: on the two tokens where the
scan is complete, one is negative and one is positive, and both statements are worth something.
Everywhere else the answer is partly "not measured".

One token produced no measurement at all and is marked as such rather than counted as negative. The
distinction between *measured negative* and *not measurable* is the subject of `PITFALLS.md` P15,
and it is not bookkeeping: collapsing the two is what produced a clean, entirely false `0/14` in
this project.

Full per-wallet detail: `data/split/all_buyers_g2y.json`. The separate question of whether this
mechanism also appears on tokens nobody traded is kept in [`SPLIT_PHASE1.md`](SPLIT_PHASE1.md) §6.
