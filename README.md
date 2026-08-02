# Why Solana memecoins are over

**A measurement study of how a market ate itself**, told in three acts and backed by on-chain
evidence at every step — plus a record of the fifteen times this project produced a number that
looked like a finding and was not.

The short version: a launch mechanism that worked *because* outsiders could still see it coming got
optimised until outsiders could not participate at all. The optimisation worked. It also removed
the reason anyone was there.

---

## Act I — 2024: manufactured organic demand

A new token appears. Several wallets buy it early, one after another. On the surface that is what
demand looks like: independent participants, arriving separately, accumulating supply.

Trace the money and the picture changes. Those wallets were **created days before the token
existed**, they hold nothing else, and their funding arrives from one address:
`G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t` — publicly identified as a **hot wallet of the swap
service ChangeNOW**.[^gw]

That is the whole mechanism, and it is structural rather than sinister: **a swap service breaks the
on-chain link between where funds came from and where they land.** That is what it is for. Anyone
can use one and most users do so for ordinary reasons. But a set of wallets funded through one is
*indistinguishable on chain* from a set of unrelated buyers — which is exactly the appearance of
organic demand, obtained without any.

[^gw]: Identification from two independent public sources, both checkable: a research study on
    Solana mixers ([Nevan, 23 April 2025](https://medium.com/@smartgenuise806/the-shadow-economy-a-research-study-on-mixers-in-solana-3eebc60dcd2a)),
    whose author observed his own test funds arrive at this address and attributes it to ChangeNOW;
    and an earlier public attribution of the same address to the same service
    ([2023](https://x.com/CrypticZK/status/1616072613356535808)). Neither is an official exchange
    label, so the identification is reported at that level of confidence: **publicly attributed,
    not officially confirmed.** Nothing about the service's conduct follows from it — see below.

The evidence, token by token, is in **[docs/PATTERN.md](docs/PATTERN.md)**. The clearest single
instance:

> **Nine freshly created wallets each receive exactly 2.976815600 SOL** from the same gateway,
> between 07:07:49 and 07:13:32 UTC — 343 seconds — on 2024-12-13. The token they would go on to buy
> is created seven and a half hours later, at 14:50.
>
> Nine decimals. Identical across nine wallets. Before the token existed.

That amount is a conversion output, not a figure anyone types — and **the same figure reappears on a
different token thirty-one days earlier**, from the same gateway. A swap output depends on size,
route and the price at that instant, so the exact number recurring is a repeated operation, not a
repeated coincidence.

The pattern is confirmed on **6 of 13 tokens** scanned across **3 963 distinct buyers**. Where it is
absent, the repository says whether that is a measured no or an unread wallet — the difference
matters, and [PITFALLS P15](docs/PITFALLS.md) explains what happens when you collapse the two.

**What this does not establish**, and the repository never claims:

- **Nothing about ChangeNOW's conduct.** Naming the address is naming a *route*, not an accomplice.
  A swap service processes what its users send it; capital entering Solana passes through some such
  service by necessity, and none of the measurements here touch what the service knew, intended or
  permitted. The property being used is a property of *every* swap service, not a failing of one.
- **One actor per dispatch — that much is certain.** A transaction paying twenty wallets an
  identical amount has one signer and one decision; the repository says so plainly. What is *not*
  established is that the dispatches on different tokens are the same actor. Testing it
  (`code/a7_cross_token_links.py`) found two real cross-token links — an exact nine-decimal amount
  shared by two launches 31 days apart, and one wallet buying on two of them — against 14 funding
  sessions that never touch more than one token. That is more than unrelated users of a common
  gateway and less than one hand behind everything. The alternative that survives is a **shared
  tool**, which this corpus documents elsewhere: two operator clusters sharing no wallet and no
  token nonetheless share a byte-level execution fingerprint. A repeated method proves a repeated
  method; identifying the hand needs an artefact none of the tests produced.
- **But the wallets are not disposable, and that changes the shape.** Those tests looked *upstream*,
  where a careful operator leaves nothing. Looking downstream — what each funded wallet does after
  its trade — **14 of 14** went on to fund addresses that were **born on receipt**: 129 new wallets
  spawned, one buyer still active **356 days** later after funding 150 addresses. And the nine
  wallets funded in the same 343-second burst do not only start together: the six that are readable
  all **stop on the same day**. This is a standing population that replenishes itself, not confetti
  — see [docs/PATTERN.md](docs/PATTERN.md) §5.

**And it was traded.** The author detected this signal in real time and acted on it: 20 documented
executions, and **1 200 SOL — 238 990 $ at the price on each transfer's own day — withdrawn over
October, November and December 2024**, measured on chain across 312 transfers. The receipts, the
execution stack, the exit ladder and the totals are in
**[docs/EXPLOITATION.md](docs/EXPLOITATION.md)**.

## Act II — the window, and why it was worth closing

The 2024 mechanism had one flaw from its operators' point of view: **it was slow enough to watch.**
Wallets funded hours ahead, buying in sequence on a visible curve. Someone paying attention could
see the accumulation and buy alongside it.

That is not a bug in the market. That *is* the market: a launch needs outside buyers, and the
sequence is what let them in.

## Act III — 2026: the lock, and the death it caused

The obvious optimisation: stop leaving a window at all.

On **42 launches verified transaction by transaction, the entire bonding curve is bought inside the
token's own creation slot** — median 85.2 SOL for 79.0 % of supply, with zero curve purchase
preceding it in 42 of 42 cases. On a separate frozen sample of 70 tokens that reached ≥ 500 k$,
**58/70 = 82.9 %** carry the same signature.

By the time the market opens, market capitalisation has gone from ~2 158 $ to ~53 985 $ — **×25
before a single outside buyer can transact.** The position leaves at a median **t+17.5 seconds**.

There is no sequence left to watch, because there is no sequence. And the consequence is
arithmetical:

- across **15 exit policies** on 196 tokens, the mean is negative in **15 of 15**, and no policy has
  a 95 % confidence interval above zero;
- **21.3 %** of tokens have already peaked when they first become visible; **50 %** within 120
  seconds;
- entering after the snipe returns **0.35× at +1 h** and **0.08× at +24 h**.

A market where every measurable strategy loses does not have disappointed participants. It has
**no** participants. The optimisation that removed the window removed the counterparty — and a
launch venue without buyers is not a venue.

That is the answer to the title. Not a crash, not a narrative rotation: the extraction was made so
efficient that there was nothing left to extract from.

**The before-and-after is measured on the same instrument.** The exit ladder that returned 238 990 $
over three months of 2024 — take 50 % at ×2, tranches at ×5 and ×10 — is unchanged in
`code/exit_ladder.py`. Applied to 2026 launches it has **no positive expectancy under any of the
fifteen policies tested**. The strategy did not decay. Its counterparty was removed.

---

## The part that makes this credible: [docs/PITFALLS.md](docs/PITFALLS.md)

Anyone can publish an analysis that agrees with its author. Fifteen cards, each one a number this
project got wrong, the test that killed it, and what survived. **Eleven killed a positive result.**

Three worth reading:

- **P13** — the detector's most intuitive criterion, *these buyers share a funder*, fires on
  **88.9 %** of randomly drawn wallet groups. It was carrying the headline claim. Retired.
- **P14** — with that gone the signal still separated targets from controls at p = 0.0007, until a
  second control group revealed the controls were all *dead* tokens while every target had
  graduated. Against graduated controls: **p = 0.44**. It was measuring success, not coordination.
- **P15** — a scan returned a clean `0/14 tokens carry the pattern`. It was a wrong hostname. Three
  transport failures in one session, each returning a plausible number instead of an error.

There is also a **[What did not reproduce](docs/PITFALLS.md#what-did-not-reproduce)** section for
figures in the project's own notes that could not be re-derived. They are recorded as unreproduced
rather than quietly dropped.

> **Vocabulary.** *The Matrix*, where it appears, names the coordinated infrastructure observed on
> chain — addresses sharing funding origins and execution patterns. It labels a measured structure,
> never an actor. Every address and amount quoted is a public technical identifier. Nothing here
> attributes intent, identity or wrongdoing to any person or company.

---

## The measurements behind the story

Acts I and III quote the headline figures. The full versions, with their `n`, their confidence
intervals and the attacks each one had to survive, are in
[docs/RESULTATS.md](docs/RESULTATS.md) and [docs/PATTERN.md](docs/PATTERN.md). Two results deserve
their own place here, because both cut against the story rather than for it.

### Operator clusters — and what they are not

A token–token graph built on shared wallets is dominated by 9 shared-infrastructure addresses.
Removing them collapses the giant component from **180/282 to 57/282**. What remains is 6 disjoint
clusters covering 76/282 tokens, with intra-cluster wallet reuse of 0.90–1.00 against a **0.019**
base rate.

Then the result argues against itself. Cluster membership does **not** predict how high a token
goes (p = 1.000), and clustered tokens perform *below* the baseline — 0.130 against 0.213 on tokens
peaking above 300 k$. Detecting a coordinated launch is a **negative** signal for a buyer, not an
edge. Two clusters that share no wallet and no token nonetheless share a byte-level execution
fingerprint: that is a shared tool, not a shared identity, and the repository says so rather than
counting them as one operator.

### Cost to a buyer — every exit policy loses

Across **15 exit policies** on 196 tokens and 20 clusters, the mean is negative in **15 of 15**, and
no policy has a 95 % cluster-bootstrap confidence interval above zero. 21.3 % of tokens (n = 1 243)
have already peaked at first external visibility; 50 % within 120 seconds. Post-snipe entry returns
0.35× at +1 h and 0.08× at +24 h.

There is no strategy in this repository. The measurement says there is nothing to extract, and that
result is the one that survived the most attacks.

---

## Reproducing it

Stdlib-only Python 3.9+. No install step, no credential in any file, relative paths throughout.

```bash
python3 code/run_all.py --strict
```

That runs every offline measurement — no API key, no network, ~20 s — and then **byte-compares each
regenerated table and JSON against the committed one**. A green run means the numbers in `docs/`
are what this code produces from this data today, not what it produced on some earlier state of
either.

Measurements that need the chain are listed and skipped unless a Helius key is present:

```bash
export HELIUS_API_KEYS=key1[,key2]
python3 code/run_all.py --with-net
```

Before any push, the publication gate:

```bash
python3 code/check_no_secrets.py --identity identity.txt
```

Seven classes of leak — keys, credential files, local paths, personal handles, bot tokens,
unsubstituted redactions, oversized data — each with a mechanical rule. The point is not that a
scanner proves a repository clean. The point is that *"I checked"* becomes a command with an exit
code instead of an assertion.

---

## Repository map

| path | what is in it |
|---|---|
| [`docs/PITFALLS.md`](docs/PITFALLS.md) | thirteen ways this project was wrong, and how each was caught |
| [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) | definitions, populations, validation protocol, declared limits |
| [`docs/RESULTATS.md`](docs/RESULTATS.md) | the 2026 measurements in full, with an English summary at the top |
| [`docs/PATTERN.md`](docs/PATTERN.md) | the funding dispatch, token by token, with every burst listed |
| [`docs/EXPLOITATION.md`](docs/EXPLOITATION.md) | trading it: signal, automation, exit ladder, 20 receipts, on-chain totals |
| [`docs/SPLIT_PHASE1.md`](docs/SPLIT_PHASE1.md) | the 2024–2025 split: targets, two control groups, null model |
| [`code/`](code/) | every measurement, one script per result — see [`code/README.md`](code/README.md) |
| [`data/`](data/) | derived data, committed; network caches are git-ignored and re-fetchable |
| [`figures/`](figures/) | regenerated by `code/f_figures_resultats.py` |

---

## What is deliberately not claimed

- **No identity, no intent.** Every address and signature quoted is a public technical identifier.
  Reaching a swap service or a bridge is a **routing fact**: all capital entering this chain passes
  through such a gateway, and no involvement of any service is asserted or implied. "A single
  controller" is not demonstrable from chain data and is never written; what is measured is
  *clusters sharing a funding origin*.
- **No prevalence for the 2024–2025 era.** The phase-1 targets are tokens their author traded and
  screenshotted — selected on the outcome twice over. All 11 graduated, against a **1.17 %** base
  rate for the era; a random draw of 11 would be graduated throughout with probability ~5×10⁻²². The
  cohort supports a *conditional* comparison against other graduated tokens of the same window, and
  nothing about how common the pattern is. Six symbols could not be resolved to a mint with
  confidence and are left marked AMBIGUOUS rather than guessed.
- **No continuum between the two eras.** Roughly sixteen months separate the Act I window from the
  Act III capture, and they are not observed. The three acts are a reading of two measured
  end-states, not a filmed transition: the repository shows what the market looked like at each end
  and argues the link, it does not claim to have watched one become the other.
- **No causal claim about SOL itself.** What is measured is the buyer economics of pump.fun
  launches — every exit policy negative, no counterparty left. Nothing here measures the price of
  SOL or attributes its moves to this mechanism.
- **No profitable strategy.** The measured outcome of buying into this microstructure is a loss
  under every exit policy tested. That is the result, and it is not hedged.
- **Negative results stay.** They are what makes the rest credible.
