# Microstructure of Solana memecoin launches

A measurement study of how pump.fun launches actually work, and a record of the fourteen times this
project produced a number that looked like a finding and was not.

Two eras are examined with the same instruments, seventeen months apart:

- **2024–2025.** Capital is routed to fresh wallets, split into near-identical amounts, and spent
  in sequence on a new token. The sequence is slow enough that an outsider watching the chain can
  see it happen.
- **2026.** The entire bonding curve is bought inside the token's own creation slot. There is no
  sequence left to watch: by the time the market opens, the supply is already held.

The interesting part is not that both were measured. It is that measuring them produced a long
series of confident wrong answers first, and that the chapter documenting those is the longest one
in the repository.

> **Vocabulary.** *The Matrix*, wherever it appears below, is a naming convention for the
> coordinated infrastructure observed on chain — a set of addresses that share funding origins and
> execution patterns. It is a label for a measured structure, never an actor, and nothing in this
> repository attributes intent, identity, or wrongdoing to any person or company.

---

## What is measured

### 1. Launch mechanics, 2026 — the window closes

On 42 launches verified transaction by transaction, the whole bonding curve is bought **inside the
creation slot**: median 85.2 SOL for 79.0 % of supply, with zero curve purchase preceding it in
42 of 42 cases. The position leaves at a median **t+17.5 s**. Market capitalisation goes from
~2 158 $ at launch to ~53 985 $ by the time a first external buyer can transact — **×25 before the
market opens**. On a separately frozen sample of 70 tokens that reached ≥ 500 k$, **58/70 = 82.9 %**
[95 % CI 72.4–89.9] carry the same creation-slot signature.

### 2. Operator clusters — and what they are not

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

### 3. Cost to a buyer — every exit policy loses

Across **15 exit policies** on 196 tokens and 20 clusters, the mean is negative in **15 of 15**, and
no policy has a 95 % cluster-bootstrap confidence interval above zero. 21.3 % of tokens (n = 1 243)
have already peaked at first external visibility; 50 % within 120 seconds. Post-snipe entry returns
0.35× at +1 h and 0.08× at +24 h.

There is no strategy in this repository. The measurement says there is nothing to extract, and that
result is the one that survived the most attacks.

### 4. The 2024–2025 funding dispatch — present, token by token

The reference case is a token whose first four buyers were born in a **single transaction** five
days before the token existed, each funded with exactly 3.000000000 SOL from one distribution hub.
Paging that hub back without bound — 217 615 signatures, genesis reached — shows an account
activated with 0.01 SOL in October 2024 and operating two weeks later as a **fan-out**: it receives
an amount and pays the same amount out within the minute, cut into round parts across several
recipients. Its principal funder is not new; that account dates to 2022 and its own genesis is
reached, which rules out infrastructure built for this window alone. Two upstream addresses exceed
the pagination ceiling and are reported as **out of reach**, not as unfunded.

Tested token by token on the fifteen tokens of the window, the dispatch is present on **8 of 15**,
and on **6 of 15** under a strict rule requiring three or more fresh wallets funded with an
identical amount inside 120 seconds. One token carries three same-transaction fan-outs of **twenty
wallets each**, at amounts identical to nine decimal places, within half an hour. The reference case
is recovered by the detector, which is the positive control. Every dispatch is listed with its
amount, span and timestamp in **[docs/PATTERN.md](docs/PATTERN.md)**.

One correction came out of the data: every cluster at the buying-wallet layer is a *round* amount,
not a conversion output. The two are one hop apart — a conversion pays a distributor, the
distributor pays the wallets in round parts — so the round amounts are the observable signal at the
wallet layer, and the hub above behaves exactly that way.

What the mechanism does **not** do is distinguish these tokens from other graduated tokens of the
same window: against those, **5/14 versus 3/12, p = 0.44**. Present here, and present elsewhere too.
Both are true, and the separate write-up keeps them separate:
**[docs/SPLIT_PHASE1.md](docs/SPLIT_PHASE1.md)**.

---

## The centrepiece: [docs/PITFALLS.md](docs/PITFALLS.md)

Fourteen episodes, each one a card: the misleading number first obtained, the specific test that
exposed it, the fix, the value that survived, and the transferable lesson. **Eleven of the fourteen
killed a positive result.**

A sample:

| # | what looked true | what was true |
|---|---|---|
| 1 | 69.8 % of tokens double | 46.3 % — that was the base rate |
| 4 | +30.0 pt, p = 0.0032 | Mantel-Haenszel odds ratio 1.22, p = 0.97 |
| 6 | median +1 h = 29.97× | **0.394×** — two variables, two units |
| 10 | best of 38 policies = +7.26 % | 5 % critical value of the maximum = +26.3 % |
| 12 | giant component 63.8 % | 17.0 % once hub nodes are handled |
| 13 | "these wallets share a funder" separates targets from controls | it fires on 88.9 % of *random* groups |
| 14 | split signature, targets vs controls, p = 0.0007 | vs *graduated* controls, p = 0.44 — the effect was the outcome |

Pitfalls 13 and 14 are the pair worth reading first — they killed the same claim from two
directions. A detector was built on three criteria and shipped a
verdict before any of the three had a null distribution of its own. Supplying one — by pooling the
control wallets and drawing random groups of forty — showed that the most intuitive criterion, *these
early buyers share a private funder*, fires on 88.9 % of groups that were never coordinated at all,
and on 99.5 % of groups restricted to wallets whose history could be read to the end. It would have
carried the headline claim. The two criteria that require a coincidence in identity **and** in time
fired 0 times in 5 000 draws, and those are the ones the conclusions now rest on.

Pitfall 14 finished the job. With the worthless criterion gone the signature still separated targets
from controls at p = 0.0007 — until a *second* control group was built. The first was matched on
creation slot and consisted entirely of tokens that died; every target had graduated. Two things
differed between the groups at once, and the design could not say which one the p-value belonged to.
Against graduated tokens of the same window, the separation vanishes: **p = 0.44**. It was measuring
success, not coordination.

There is also a **[What did not reproduce](docs/PITFALLS.md#what-did-not-reproduce)** section, for
three figures that circulate in the project's own notes and could not be re-derived from the
published data. They are recorded as unreproduced rather than quietly dropped.

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
- **No continuum between the two eras.** Roughly sixteen months separate the phase-1 window from
  the 2026 capture, and they are not observed. The repository compares two epochs; it does not
  claim to have watched one turn into the other.
- **No profitable strategy.** The measured outcome of buying into this microstructure is a loss
  under every exit policy tested. That is the result, and it is not hedged.
- **Negative results stay.** They are what makes the rest credible.
