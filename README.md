# Why Solana memecoins are over

**In three months I withdrew 238 989.57 $ trading memecoin launches. Then I stopped, because the
thing I was trading stopped existing — and this repository is the measurement of why.**

Not a market that cooled. A market whose operators optimised their own extraction until there was
nobody left to extract from. Today **0.26 %** of pump.fun launches ever graduate, and Solana's daily
network fees have fallen **84 %** — from ~33 000 SOL a day in January to ~5 300 in June 2026.[^macro]
That collapse has a mechanism, it is visible transaction by transaction, and every figure below
regenerates from this repository with no network access.

[^macro]: Graduation rate and fee decline: [DEXTools, 22 June 2026](https://www.dextools.io/news/pump-fun-graduation-collapse-solana-fees-2026).
    For scale in the period this study covers, a Q4-2024 academic analysis put pump.fun at up to
    **71.1 % of all Solana token mints** and **40–67.4 % of all DEX transactions** — the launchpad
    was not a corner of the chain, it was a large share of its activity.

---

## Act I — 2024: how you make 238 989.57 $ from a market that is lying to you

A new token appears. Several wallets buy it early, one after another. That is what demand looks
like: independent participants, arriving separately, accumulating supply.

It is not demand. Trace the money and every one of those wallets was **created days before the token
existed**, holds nothing else, and was funded from a single address:
`G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t` — identified by independent researchers as a hot
wallet of the swap service **ChangeNOW**.[^gw]

That is the whole trick, and it is structural: **a swap service breaks the on-chain link between
where funds came from and where they land.** That is what it is for. Push a launch's capital through
one and the wallets that come out the far side are indistinguishable from unrelated buyers. You get
the *appearance* of organic demand without any.

[^gw]: A [2025 research study on Solana mixers](https://medium.com/@smartgenuise806/the-shadow-economy-a-research-study-on-mixers-in-solana-3eebc60dcd2a)
    whose author routed his own test funds through ChangeNOW and observed them arrive at this
    address, and an [earlier public attribution](https://x.com/CrypticZK/status/1616072613356535808)
    of the same address to the same service. Neither is an official exchange label. And nothing here
    concerns the service's conduct: a swap processes what its users send it, and no involvement,
    knowledge or wrongdoing is attributed to any company.

**Here is what that looks like on chain.** Nine freshly created wallets, each receiving *exactly*
2.976815600 SOL from that address, between 07:07:49 and 07:13:32 UTC on 2024-12-13 — **343 seconds**.
The token they would buy is created seven and a half hours later.

Nine decimals. Identical across nine wallets. Before the token existed. That amount is a conversion
output — not a figure anyone types — and **the same figure reappears on a different token thirty-one
days earlier**, from the same gateway.

**And that was the trade.** The accumulation was slow enough to read while it was still happening:
spot the fresh gateway-funded wallet, buy alongside it, sell into the crowd it was built to attract.
Fixed ladder — 50 % at ×2, tranches at ×5 and ×10 — so a signal at 4 a.m. could be taken unattended.

| | |
|---|---|
| withdrawn Oct–Dec 2024 | **1 200.12 SOL — 238 989.57 $** at the price on each transfer's own day |
| across | **312 transfers, 97 trading wallets** |
| documented executions | **20**, from +100 % to **+28 465 %** |
| the whole window, to Feb 2025 | 246 945.59 $ |

Receipts, execution stack and the full method: **[docs/EXPLOITATION.md](docs/EXPLOITATION.md)**.
The mechanism with six worked examples: **[docs/PATTERN.md](docs/PATTERN.md)**.

**What this does not claim.** Nothing about ChangeNOW's conduct. And not a single controller: each
launch traces to its *own* distributor, so what the data supports is *clusters sharing a funding
origin* — though the wallets themselves turn out to be a self-replenishing fleet, which is
[§5 of PATTERN.md](docs/PATTERN.md) and stranger than it sounds.

## Act II — greed, and the flaw it was fixing

The 2024 mechanism had one defect from its operators' point of view: **it was slow enough to watch.**
Wallets funded hours ahead, buying in sequence on a visible curve. Anyone paying attention — me, for
instance — could see the accumulation and buy alongside it.

From their side that is leakage. Every SOL an outsider makes is a SOL they did not.

But that leakage *was* the market. A launch needs outside buyers, and the sequence is what let them
in. The thing they were losing money to was the thing generating their exit liquidity.

## Act III — 2026: the fix, and what it killed

They fixed it. **On 42 launches verified transaction by transaction, the entire bonding curve is
bought inside the token's own creation slot** — 85 SOL, 79 % of supply, zero curve purchase
preceding it in 42 of 42 cases. On a separate frozen sample of 70 tokens that reached ≥ 500 k$,
**58/70 = 82.9 %** carry the same signature.

By the time the market opens, capitalisation has gone from ~2 158 $ to ~53 985 $ — **×25 before a
single outside buyer can transact.** The position leaves at a median **t+17.5 seconds**.

No sequence left to watch, because there is no sequence. And what follows is arithmetic:

- across **15 exit policies** on 196 tokens, the mean is negative in **15 of 15**, and no policy has
  a 95 % confidence interval above zero;
- **21.3 %** of tokens have already peaked when they first become visible; **50 %** within 120 s;
- entering after the snipe returns **0.35× at +1 h** and **0.08× at +24 h**.

**A market where every measurable strategy loses does not have disappointed participants. It has no
participants.** The optimisation that closed the window removed the counterparty — and the numbers
downstream are exactly what that predicts: graduation rate **0.26 %**, Solana network fees **−84 %**,
33 000 SOL a day down to 5 300.

They took the whole curve so they would not have to share it. There was then nobody to sell it to.

**The before-and-after runs on the same instrument.** The ladder that returned 238 989.57 $ — 50 % at
×2, tranches at ×5 and ×10 — is unchanged in `code/exit_ladder.py`. Applied to 2026 launches it has
**no positive expectancy under any of the fifteen policies tested**. The strategy did not decay. Its
counterparty was removed.

That is the answer to the title. Not a crash, not a rotation of narratives: the extraction was made
so efficient that there was nothing left to extract from — including for the people who made it
efficient.

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
- **The chain-wide figures are cited, not measured here.** The 0.26 % graduation rate and the 84 %
  fee decline come from published sources, linked at first use; this repository measures the launch
  microstructure that explains them, not the aggregates themselves. And no claim is made about the
  *price* of SOL — what is measured is that the buyer side of these launches stopped being
  survivable, and what is cited is that chain activity fell alongside it.
- **No profitable strategy.** The measured outcome of buying into this microstructure is a loss
  under every exit policy tested. That is the result, and it is not hedged.
- **Negative results stay.** They are what makes the rest credible.
