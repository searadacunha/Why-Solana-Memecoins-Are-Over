# The 2024–2025 split: what the chain shows, and what it does not

**What this chapter is.** An investigation of the era *before* the creation-slot buyback closed the
window — roughly October 2024 to February 2025 — when capital was routed to fresh wallets, cut into
near-identical amounts, and spent in sequence. It reports one confirmed reference case, a hub traced
to its own genesis, two control groups, a null distribution for the detector itself, and a target
cohort that cannot support the claim it was assembled to support.

The order matters. The detector is examined *before* its output, because the version of this chapter
that read the output first got the headline backwards.

> *The Matrix*, here, names the coordinated infrastructure observed on chain: addresses sharing
> funding origins and execution patterns. It is a label for a measured structure and never an actor.
> Every address quoted is a public technical identifier. Reaching a swap service or a bridge is a
> **routing fact** — all capital entering this chain passes through such a gateway — and no
> involvement by any service, company, or person is asserted or implied.

---

## 1. The reference case

One token, created 2024-11-22 at 23:49 UTC, has four first buyers that share an unusual property:
all four wallets were **born in the same transaction**, five days earlier, on 2024-11-17 at 23:55
UTC. That transaction moved 12.0001 SOL out as **4 × 3.000000000 SOL**, one per wallet, from a
single hub address. All four wallet histories were paged back to their first signature — genesis
reached, 4 of 4 — so this is an observation, not the residue of a bounded walk.

Two properties make the amount informative rather than decorative. It is **round to nine decimals**,
which a swap output is not: a conversion leaves values like 1.393934883. And it is **identical
across four recipients inside one transaction**, which a coincidence of independent deposits is not.
Round amount plus shared transaction is the signature; either alone is much weaker (see
`docs/PITFALLS.md`, mixed calibres).

## 2. The hub, traced to its own genesis

Earlier work could not say where the hub itself got its funds. The walk had been bounded and
returned only recent history — the silent pagination failure, arriving as a plausible-looking answer
rather than an error.

Redone without bound (`code/a3_hub_origin.py`, from two unbounded walks):

| | |
|---|---|
| signatures read | **217 615** |
| genesis reached | **yes** |
| first operation | 2024-10-22, **0.01 SOL** — an account activation |
| real activity begins | 2024-11-06, two weeks later |
| fan-outs observed in the first events | 4 |

The usage pattern is a **fan-out**: the hub receives an amount and pays the same amount out within
the minute, cut into round parts across several recipients. It does not hold a balance. Four
examples from its first day of real activity:

| received | paid out to | amounts |
|---|---|---|
| 1.5001 SOL | 8 addresses | 0.1 ×6, 0.2, 0.3 |
| 15.0001 SOL | 6 addresses | 1, 1, 2, 3, 3, 5 |
| 16.0001 SOL | 3 addresses | 2, 6, 8 |
| 15.0001 SOL | 3 addresses | 5, 5, 5 |

Upstream, three funders were paged to genesis and two were not:

| address role | signatures | genesis | active since |
|---|---|---|---|
| principal funder | 219 104 | reached | **2022-03-14** |
| first notable transfer | 14 798 | reached | 2023-01-01 |
| secondary funder | 109 | reached | 2024-11-06 |
| commission recipient | 400 000 read | **not reached** | — |
| account activator | 400 000 read | **not reached** | — |

**What this establishes.** The hub account is new at the opening of the studied window, and its
shape of use is distribution rather than trading. Its principal funder is *not* new — that account
dates to 2022 with its genesis reached — which rules out infrastructure built for this window alone.

**What it does not.** The last two rows are reported as **out of reach**, not as unfunded. An
address whose history exceeds the pagination ceiling has an unmeasured origin, and writing "no
funding found" for it would be reporting a measurement failure as a result. And a wallet that pays
out what it receives is equally consistent with an operation's distributor and with a third-party
service's relay: the *shape* is established, the *intent* is not.

---

## 3. The detector, and its null distribution

The split detector declares a token positive when any of three criteria fires on its first forty
buyers:

- **A** — two or more are funded inside the **same transaction**;
- **B** — three or more receive amounts equal to within 1e-4 relative, inside **one hour**;
- **C** — two or more share a **private funder** (known exchange and bridge terminals excluded,
  since a shared hot wallet is a deposit, not a coordination).

Before reading a single verdict, each criterion needs to be asked how often it fires on wallets that
were never coordinated. The control group already supplies the population: 136 early-buyer wallets
from tokens selected on creation slot alone, with funding measured by identical code. Pooling them
and drawing random groups destroys within-token co-occurrence, so any hit in a drawn group is a
coincidence by construction.

Over 5 000 draws (`code/a1_null_model.py`):

| criterion | group of 10 | group of 20 | group of 40 |
|---|---|---|---|
| **A** same funding transaction | 0.0000 | 0.0000 | 0.0000 |
| **B** same amount within one hour | 0.0000 | 0.0000 | 0.0000 |
| **C** shared private funder | 0.151 | 0.461 | **0.889** |

Restricted to the 70 wallets whose genesis was actually reached — the only subset on which a
negative is admissible — **C fires on 99.5 %** of draws.

**Criterion C is retired.** Its rate climbs with group size the way a birthday problem does: more
wallets, more pairs, funders drawn from a finite pool. It cannot enter a disjunctive verdict,
because at 88.9 % it *is* the verdict. Criteria A and B fired 0 times in 5 000 draws at every size:
they demand a coincidence in identity **and** in time, and that is what makes them specific.

Every token was therefore recounted under **A and B only** (`code/a2_recount.py`). The full episode,
including which conclusion this reversed, is card 13 of `docs/PITFALLS.md`.

---

## 4. Two control groups, and why one was not enough

**Control group 1 — matched on creation slot (n = 9).** Every pump.fun mint created within ±200
slots of a target, selection depending only on creation slot and market outcome, with the rule fixed
before any funding was measured. Bonding-curve pagination reached genesis for all 171 harvested
mints.

That group leaves one confound wide open: the targets all graduated, and these controls are all dead
tokens. A difference between the two groups can come from **success** rather than from coordination.
Sophisticated buyers cluster on tokens that go somewhere; that alone could produce coordinated-looking
funding without any operation behind it.

**Control group 2 — matched on the outcome (n = 12).** Graduated pump.fun tokens from the same
window that the author never traded, drawn by systematic sampling across the full capitalisation
range of the reachable pool (`data/trace_gradues/t0_gradues.json`), with the retention rule fixed
before measurement. This is the comparison that carries weight; group 1 is kept to show how far the
confound moves the answer.

The reachable pool is itself survivor-selected — it comes from a capitalisation-ranked listing — so
these controls did, on average, *better* than the targets. That bias runs **against** the hypothesis
under test, which makes a negative among them more informative, not less.

---

## 5. The target cohort, and the claim it cannot support

The targets are tokens their author traded and screenshotted. That is selection on the outcome twice
over: once because the token went somewhere worth trading, once because the trade went well enough
to screenshot. `code/a4_selection_bias.py` puts a number on it:

| | |
|---|---|
| graduation rate of the era, five neutral term families | 32 / 2 740 = **1.17 %** |
| graduation rate, slot-matched creation windows | 6 / 171 = 3.51 % |
| target cohort | **11 / 11 = 100 %** |
| probability of that under random sampling | **~5 × 10⁻²²** |

Mint resolution is uneven and is labelled as such: 8 read directly from a capture, 2 resolved by
symbol *and* date, 1 by symbol alone. **Six symbols could not be resolved** to a mint with any
confidence — homonyms are endemic on pump.fun, which is itself part of the subject — and are left
marked AMBIGUOUS rather than guessed. One fragment resolved to a mint sharing its first nine
characters with a pool created on the capture's own date; the differences are consistent with OCR,
and it is recorded at that level of confidence, not higher.

**What the cohort can answer.** Among graduated tokens of the same window, do the traded ones carry
the signature more often than the others? That, and a presence test: is the signature observable
where the author says it was?

**What it cannot answer.** Prevalence. *"X % of tokens carry the signature"* is not derivable from a
sample selected on the outcome, however carefully the sentence is worded. Nor profitability: the
captures are winning trades, and the losing ones are not in the dossier and cannot be.

---

## 6. Result — the signature does not survive its own control group

**The short version.** Against dead tokens, the split signature separates the traded tokens from the
rest with p = 0.0007. Against graduated tokens of the same window, it separates nothing: p = 0.44.
The apparent effect was the difference between a token that went somewhere and a token that did not,
not the difference between a coordinated launch and an ordinary one.

Read the four rows of the second table in order. Each one strips away one thing that was doing the
work:

1. **Original verdict, dead controls — 12/14 vs 1/9, p = 0.0007.** This is the number the project
   would have published. It rests on criterion C, which §3 showed fires on 88.9 % of random groups.
2. **A or B only, dead controls — 5/14 vs 0/9, p = 0.060.** Removing the worthless criterion costs
   most of the effect and all of the significance.
3. **Original verdict, graduated controls — 12/14 vs 8/12, p = 0.25.** Holding the outcome fixed,
   two thirds of *untraded* graduated tokens also "carry the signature". Criterion C is not
   detecting coordination; it is detecting that a token had buyers.
4. **A or B only, graduated controls — 5/14 vs 3/12, p = 0.44.** Both corrections applied. Nothing
   remains.

The strongest criterion tells the same story more quietly. Criterion A — two early buyers funded
inside the *same transaction*, the one that fired 0 times in 5 000 null draws — appears on exactly
**one** target out of fourteen and on **none** of the twelve graduated controls (p = 0.54). One case
is not a rate. It is a case.

**What stands.** The reference case is real: four wallets born in one transaction, four identical
round amounts, five days before the token, genesis reached on all four. So is the second instance
found among the targets. So is the hub, its fan-out shape, and its 2022 funder. These are
observations, and they are not withdrawn.

**What falls.** The claim these observations were assembled to support — that the tokens this author
traded were systematically launched on split-funded wallets — does not survive the comparison with
graduated tokens he never touched. Coordinated-looking funding is **ordinary among tokens that
graduate**. It is not a marker of the traded subset.

**Why this is the more useful result.** A pattern confirmed on the case that suggested it, and then
found at the same rate in a properly matched control group, is the exact shape of a false discovery
that a weaker protocol would have shipped. Two control groups were needed to see it: the first
answered a question nobody asked — *do traded tokens differ from dead ones?* — to which the answer
is yes, and uninformative. The confound is P4 of `docs/PITFALLS.md` recurring in a new domain, which
is itself worth recording: knowing a pitfall by name does not stop you walking into it.

Consequently, nothing in this repository asserts that the phase-1 window was systematically
coordinated. What it documents is a mechanism that demonstrably existed in at least two measured
cases, a distribution hub traced to its genesis, and a test that failed to show the mechanism was
general.

<!-- RESULTS-TABLE -->

| group | token | A | B | C | verdict A-or-B-or-C | verdict A-or-B |
|---|---|---:|---:|---:|:-:|:-:|
| target | `ACID` | 0 | 0 | 1 | + | – |
| target | `BLT` | 0 | 4 | 4 | + | **+** |
| target | `CHOCO` | 3 | 3 | 2 | + | **+** |
| target | `LEXICON` | 0 | 1 | 2 | + | **+** |
| target | `MIKU` | 0 | 0 | 1 | + | – |
| **discovery case** (excluded from every p below) | `ODIN_POSITIF` | 1 | 1 | 2 | + | **+** |
| target | `OPTIMUS` | 0 | 0 | 1 | + | – |
| target | `POLMRKTBOT` | 0 | 0 | 1 | + | – |
| target | `QAMI` | 0 | 0 | 4 | + | – |
| target | `RAO` | 0 | 0 | 0 | – | – |
| target | `SAFFRON` | 0 | 0 | 1 | + | – |
| target | `VISUALIZE` | 0 | 1 | 1 | + | **+** |
| target | `h2w6gm6jz` | 0 | 2 | 5 | + | **+** |
| target | `sumiko` | 0 | 0 | 1 | + | – |
| target | `symx` | 0 | 0 | 0 | – | – |
| control, graduated | `G_$RIF` | 0 | 0 | 0 | – | – |
| control, graduated | `G_CHATOSHI` | 0 | 1 | 1 | + | **+** |
| control, graduated | `G_FORK` | 0 | 0 | 0 | – | – |
| control, graduated | `G_Fartcoin ` | 0 | 0 | 1 | + | – |
| control, graduated | `G_GOAT` | 0 | 1 | 2 | + | **+** |
| control, graduated | `G_TRENCH` | 0 | 0 | 0 | – | – |
| control, graduated | `G_TULSA` | 0 | 0 | 3 | + | – |
| control, graduated | `G_VAL` | 0 | 2 | 3 | + | **+** |
| control, graduated | `G_WOLF` | 0 | 0 | 2 | + | – |
| control, graduated | `G_stkr` | 0 | 0 | 2 | + | – |
| control, graduated | `G_vvaifu` | 0 | 0 | 0 | – | – |
| control, graduated | `G_xavier` | 0 | 0 | 1 | + | – |
| control, dead | `BandD` | 0 | 0 | 0 | – | – |
| control, dead | `CREEKS` | 0 | 0 | 0 | – | – |
| control, dead | `Calm` | 0 | 0 | 0 | – | – |
| control, dead | `DONGOE` | 0 | 0 | 0 | – | – |
| control, dead | `GOOREUREKA` | 0 | 0 | 0 | – | – |
| control, dead | `HLGOOFY` | 0 | 0 | 1 | + | – |
| control, dead | `PORTAL` | 0 | 0 | 0 | – | – |
| control, dead | `QUEENAI` | 0 | 0 | 0 | – | – |
| control, dead | `faith` | 0 | 0 | 0 | – | – |

| comparison | targets | controls | Fisher one-sided *p* |
|---|---|---|---|
| original verdict (A or B or **C**) vs dead controls | 12/14 | 1/9 | 0.0007 |
| **A or B only** vs dead controls | 5/14 | 0/9 | 0.0595 |
| A alone (zero false positives in the null) vs dead controls | 1/14 | 0/9 | 0.6087 |
| original verdict (A or B or **C**) vs graduated controls | 12/14 | 8/12 | 0.2478 |
| **A or B only** vs graduated controls | 5/14 | 3/12 | 0.4371 |
| A alone (zero false positives in the null) vs graduated controls | 1/14 | 0/12 | 0.5385 |

<!-- /RESULTS-TABLE -->
---

## 7. Reproducing this chapter

```bash
python3 code/a1_null_model.py      # null distribution of the three criteria
python3 code/a2_recount.py         # every token recounted under A and B, Fisher's exact test
python3 code/a3_hub_origin.py      # hub genesis and upstream, from the two unbounded walks
python3 code/a4_selection_bias.py  # distance between the cohort and a random sample
```

All four read only committed files under `data/`. No network, no key. The walks that produced those
files need a Helius key and are listed in `code/run_all.py` under `--with-net`.
