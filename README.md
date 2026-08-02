# Why Solana memecoins are over

**Between October and December 2024 I withdrew 238 989.57 $ from trading pump.fun launches. I
stopped when the pattern I was trading disappeared, and this repository is the measurement of what
replaced it.**

**The pattern.** Before a pump.fun token exists, wallets are created for it — the same day,
sometimes minutes before. They are funded through **ChangeNOW**, a swap service, which is the point
beyond which their money is no longer traceable. When the token launches, those wallets buy its
supply.

It was visible only to those who see it. Exploiting it was still a different problem.

ChangeNOW moves large volumes of SOL out to fresh wallets continuously, most of it routine. Filtered
to a minimum of **1 SOL** per transfer, one shape stood out from the noise — the
**same amount landing on several fresh wallets at once**, the split signature. That alone was not a
trade. The trade began the moment **one of those wallets bought at least 20 million of a token's
supply on pump.fun** — about **2 %** of it. That threshold was the filter: a ChangeNOW-funded wallet
buying less than that had no real intention of controlling the token — it read as the dev's own buy,
not a split wallet worth following. Cross it, and every wallet in the split bought the same size,
together holding enough of the supply that the NPCs buying in afterward had no influence on the
price. The rest of the split had not moved yet, and that crossing was the tell that they were about
to. Position taken there, ahead of the demand the rest of the split was about to create — then it was
ordinary chart reading, judging how far the run would carry.

The same co-funding shows up on almost any token that runs: check the top holders of one that reached
$1 M+ and most were funded the same day, sometimes the same block. That much is real — it is
coordination, not noise. What it doesn't say is which way the coordination points. The same operators
stage dumps the same way they stage runs, so co-funding by itself predicts neither; following it alone
loses more often than it pays. The split needed the 20-million-token buy to say which one this was.

My position stayed small on purpose — never big enough to draw attention. It was a clean cut, taken
inside the rules, not a fight against the operators running the split. That was still more than they
were willing to share.

On a chart that reads as independent buyers arriving one after another. On one launch, nine wallets
received **the same amount to nine decimal places within 343 seconds**, seven and a half hours
before the token existed — the split signature, at scale.

That is where the 238 989.57 $ came from, and the receipts are in
[docs/EXPLOITATION.md](docs/EXPLOITATION.md).

By now, what comes out of ChangeNOW is mostly garbage — wallets funded to be burned on a rug. Enough
of them exist that the pool runs continuously, reactivated as needed rather than spent once.
Following them would be simple if that were the whole picture, but plenty of decoys get created
alongside the real ones. Reactivation covers two different plays: a rug that plays out entirely on
pump.fun, and the big one — a bundle-snipe, where the entire supply is bought inside a single block.

It no longer works. The supply is now taken in full inside the token's own creation block — 42
launches out of 42, verified transaction by transaction — so nothing reaches an outside buyer at
all. The consequences are visible at the scale of the chain: **0.26 %** of pump.fun launches now
graduate, and Solana's daily network fees have fallen **84 %**, from ~33 000 SOL in January to
~5 300 in June 2026.[^macro]

Buying into what remains has no measurable expectancy: across fifteen exit policies tested on 196
tokens and 20 detection clusters, **none** has a positive mean return and none has a 95 %
cluster-bootstrap interval clearing zero — the cluster unit matters, because tokens detected within
the same half hour are not independent observations and treating them as such inflates every
significance test in this domain.

The mechanism that made money in 2024 worked because outsiders could see the accumulation and take
part in it. Closing that gap removed the participants along with the leak.

**They were already making money. Refusing to leave a cent of it to anyone else is what ended the
market they were making it in.**

Every figure below regenerates from this repository with no network access.

[^macro]: Graduation rate and fee decline: [DEXTools, 22 June 2026](https://www.dextools.io/news/pump-fun-graduation-collapse-solana-fees-2026).
    For scale over the period this study covers, a Q4-2024 academic analysis put pump.fun at up to
    **71.1 % of all Solana token mints** and **40–67.4 % of all DEX transactions**.

---

## Act I — 2024: the pattern, and what it paid

A new token appears. Several wallets buy it early, one after another. That is what demand looks
like: independent participants, arriving separately, accumulating supply.

Every one of those wallets was **created the same day as the token** — median **9.6 hours** before
it existed, and the two on $sumiko were created **24 and 30 minutes** before. They hold nothing else.
They were funded from a single address: `G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t`, identified
by independent researchers as a hot wallet of the swap service **ChangeNOW**.[^gw]

A swap service breaks the on-chain link between where funds came from and where they land. Push a
launch's capital through one and the wallets that come out the far side are indistinguishable from
unrelated buyers.

[^gw]: A [2025 research study on Solana mixers](https://medium.com/@smartgenuise806/the-shadow-economy-a-research-study-on-mixers-in-solana-3eebc60dcd2a)
    whose author routed his own test funds through ChangeNOW and observed them arrive at this
    address, and an [earlier public attribution](https://x.com/CrypticZK/status/1616072613356535808)
    of the same address to the same service.

**On chain it looks like this.** Nine wallets, created that morning, each receiving *exactly*
2.976815600 SOL from that address between 07:07:49 and 07:13:32 UTC on 2024-12-13 — **343 seconds**.
The token they would buy is created seven and a half hours later.

Nine decimals. Identical across nine wallets. Before the token existed. That amount is a conversion
output, not a figure anyone types — and **the same figure appears on a different token thirty-one
days earlier**, from the same address.

The wallets are not discarded afterwards. All fourteen that could be read went on to fund addresses
that were **born on receipt** — 129 of them. One was still active **356 days** later, having funded
150 addresses. The nine paid in that 343-second burst also stop together: the six readable ones make
their last transaction **on the same day**.

**That was the trade.** The split could be read while it was still happening: identify the wallets
funded through the gateway, wait for one of them to buy its 20-million-token stake, then buy
alongside it — small, clean, never enough to draw attention — and sell into the demand the rest of
the split was about to create. A fixed ladder — 50 % at ×2, tranches at ×5 and ×10 — meant a signal
arriving at 4 a.m. could be taken without supervision.

| | |
|---|---|
| withdrawn Oct–Dec 2024 | **1 200.12 SOL — 238 989.57 $** at the price on each transfer's own day |
| across | **312 transfers, 97 trading wallets** |
| screenshotted executions (a sample; the window holds hundreds) | **19**, from +100 % to **+28 465 %** |
| the whole window, to Feb 2025 | 246 945.59 $ |

Receipts and method: **[docs/EXPLOITATION.md](docs/EXPLOITATION.md)**. The mechanism with six worked
examples and every timestamp: **[docs/PATTERN.md](docs/PATTERN.md)**.

## Act II — the flaw, from the other side

Seen from the operators' position, the 2024 mechanism had one defect: it was slow enough to watch.
Wallets funded hours ahead, buying in sequence on a public curve. Anyone paying attention could read
the accumulation and buy alongside it, and every SOL that went to an outsider was one that did not
go to them.

But a launch needs outside buyers. The sequence that let them in was the same sequence that created
the demand to sell into. The leak and the exit liquidity were the same thing.

The shift away from it took about three months, not one release. Fewer and fewer of the wallets
ChangeNOW funded were the ones actually buying — the wallet count kept growing, but more of it sat
idle instead of spending. They were building a reserve: thousands of wallets, all carrying the same
untraceable ChangeNOW origin, held rather than spent. Once the reserve was big enough, ChangeNOW was
dropped.

## Act III — 2026: what replaced it

The gap was closed: the bundle snipe became the default. **On 42 launches verified transaction by
transaction, the entire bonding curve is bought inside the token's own creation slot** — 85 SOL,
79 % of supply, zero curve purchase preceding it in 42 of 42 cases. On a separate frozen sample of 70 tokens that reached ≥ 500 k$,
**58/70 = 82.9 %** carry the same signature.

By the time the market opens, capitalisation has gone from ~2 158 $ to ~53 985 $ — **×25 before a
single outside buyer can transact.** The position leaves at a median **t+17.5 seconds**.

### The same signature, on a launch the whole market was watching

$ANSEM — created **2026-06-16 21:05:48 UTC**, mint `9cRCn9rGT8V2imeM2BaKs13yhMEais3ruM3rPvTGpump` —
carries it exactly. Measured with the same frozen script as the 42, paginated to the curve's own
first signature: **the entire bonding curve, 85.007 SOL, is bought inside the creation slot**
(426930467), 84.74 of it by one wallet. Two buyers, sixteen signatures, nothing left on the curve by
the time the launch is visible.

What makes it worth naming is that **both slot-0 wallets were already catalogued in this repository
before that token existed**:

| wallet | SOL at slot 0 | already in this repo as |
|---|---|---|
| `yHCxHBEa…6PRe` | **84.743** | **OP1** — a repeat operator, present on **24 of 282** tokens, explicitly *not* classed as shared infrastructure |
| `9ryBR3Sn…XLaq` | 0.265 | a **shared-infrastructure sniper**, 5th by ubiquity at **44 of 282** tokens |

A launch that a large part of the market read as memecoin season restarting was executed by the same
addresses running the mechanism that ended it. That is the closest this repository gets to answering
*who* — not a name, an address with a history.

Two things this does **not** say. It does not identify who controls those wallets, which is not on
chain. And it says nothing whatsoever about the person the token is named after: the measurement
reads a curve, not an intent, and a token bearing someone's name is not that person's transaction.

No sequence left to watch, because there is no sequence. And what follows is arithmetic:

- across **15 exit policies** on 196 tokens, the mean is negative in **15 of 15**, and no policy has
  a 95 % confidence interval above zero;
- **21.3 %** of tokens have already peaked when they first become visible; **50 %** within 120 s;
- entering after the snipe returns **0.35× at +1 h** and **0.08× at +24 h**.

A market in which no measurable strategy returns anything does not keep its participants. The
chain-level figures follow: graduation rate **0.26 %**, Solana network fees **−84 %**, 33 000 SOL a
day down to 5 300.

The curve was taken in full so that none of it would be shared. What went with it was the buyer it
had to be sold to.

**The before-and-after runs on the same instrument.** The ladder that returned 238 989.57 $ — 50 % at
×2, tranches at ×5 and ×10 — is unchanged in `code/exit_ladder.py`. Applied to 2026 launches it has
**no positive expectancy under any of the fifteen policies tested**. The strategy did not decay. Its
counterparty was removed.

That is the answer to the title. Not a crash and not a rotation of narratives: the extraction was
optimised to the point where there was nothing left to extract from — including for whoever
optimised it.

Who that is stays an open question. The chain gives up addresses and their history — OP1 on 24
tokens, the infrastructure snipers on 44 and 99 and 165 — and stops there. Millions of dollars move
through ChangeNOW every day, and for nearly all of it the wallets on the other side belong to nobody
in particular. Whether the ones behind this specific mechanism trace back to one operation, several,
or nothing more than coincidence is not something this repository can answer, and it does not
pretend to.

---

## Hypotheses tested to destruction: [docs/PITFALLS.md](docs/PITFALLS.md)

Anyone can publish an analysis that agrees with its author. Fifteen cards, each one a claim this
project held, the test built to break it, and what was left afterwards. **Eleven of them died.**

Three worth reading, because all three killed something I wanted to be true:

- **P13 — the detector was measuring nothing.** Its most intuitive criterion, *these early buyers
  share a private funder*, was carrying the headline result. Giving it a null distribution — pool
  the control wallets, draw random groups of forty, run the criterion unchanged — showed it fires on
  **88.9 %** of groups that were never coordinated at all, and 99.5 % of groups restricted to
  wallets whose history could be read to the end. A criterion that fires on nine random groups in
  ten cannot enter a verdict. Retired, and every token recounted without it.
- **P14 — the control group answered a different question.** With that criterion gone the signal
  still separated targets from controls at p = 0.0007. The controls were all *dead* tokens; every
  target had graduated. Two things differed at once, and the design could not say which the p-value
  belonged to. Against a second control group of *graduated* tokens from the same window: **p =
  0.44.** It had been measuring success, not coordination.
- **P15 — a clean number produced by a broken connection.** A scan returned `0/14 tokens carry the
  pattern`. It was a wrong hostname, swallowed as an empty answer. What caught it was arithmetic,
  not debugging: a graduated curve has hundreds of transactions by definition, so zero buyers on a
  curve reporting 587 is a contradiction rather than a low number.

### Is there still a way to win?

That question gets its own tests, because it is the one that decides whether any of this is
actionable. Fifteen exit policies on 196 tokens and 20 detection clusters; entry timed at the snipe,
after it, and at every horizon out to 24 hours; the null distribution of the *best* of 38 policies,
because picking the winner from a search is not the same as finding one.

**Nothing clears zero.** Not one policy, not one horizon, not the best-of after correcting for the
search. Entering post-snipe returns 0.35× at +1 h and 0.08× at +24 h, and 21.3 % of tokens have
already peaked before an outsider can see them.

The answer is no, and the work to establish that is the same work that found the pattern in the
first place. Knowing a thing is finished is worth as much as knowing it started.

There is also a **[What did not reproduce](docs/PITFALLS.md#what-did-not-reproduce)** section for
figures in the project's own notes that could not be re-derived from the published data. They are
recorded as unreproduced rather than quietly dropped.

> **Vocabulary.** *The Matrix*, where it appears, names the coordinated infrastructure observed on
> chain — addresses sharing funding origins and execution patterns. It labels a measured structure,
> never an actor. Every address and amount quoted is a public technical identifier.

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
| [`docs/PITFALLS.md`](docs/PITFALLS.md) | fifteen claims, the test built to break each one, and what survived |
| [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) | definitions, populations, validation protocol, declared limits |
| [`docs/RESULTATS.md`](docs/RESULTATS.md) | the 2026 measurements in full, with an English summary at the top |
| [`docs/PATTERN.md`](docs/PATTERN.md) | the funding dispatch, token by token, with every burst listed |
| [`docs/EXPLOITATION.md`](docs/EXPLOITATION.md) | trading it: signal, automation, exit ladder, 19 receipts, on-chain totals |
| [`docs/SPLIT_PHASE1.md`](docs/SPLIT_PHASE1.md) | the 2024–2025 split: targets, two control groups, null model |
| [`code/`](code/) | every measurement, one script per result — see [`code/README.md`](code/README.md) |
| [`data/`](data/) | derived data, committed; network caches are git-ignored and re-fetchable |
| [`figures/`](figures/) | regenerated by `code/f_figures_resultats.py` |

---

## Scope

Standard limits, stated once. Everything above is an observation; the reader draws their own
conclusions from it.

- **Addresses, not people.** Every address and signature quoted is a public technical identifier.
  Who operates them is not on chain and is not claimed here.
- **No prevalence.** The 2024–2025 targets are tokens their author traded and screenshotted —
  selected on the outcome twice over. All 11 graduated, against a **1.17 %** base
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
- **No strategy on offer.** Buying into this microstructure loses under every exit policy tested.
- **Negative results stay.** They are what makes the rest credible.
