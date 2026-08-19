# Why Solana Memecoins Are Over

Between **October and December 2024**, I withdrew **$237,137.87** trading memecoins on **pump.fun**.

I stopped when the pattern I was exploiting disappeared.

This repository is a measurement of what replaced it.

---

## Disclosure

The pattern documented below is one I identified and traded myself, lawfully, under my own name.
Starting capital was roughly **$400**; withdrawals over October–December 2024 came to
**$237,137.87**, a multiple of roughly **590×**. The withdrawal figure is reconstructed on chain
by `code/expl_ledger.py` and reproduces from the committed artefacts; the starting capital is a
Phase-0 recollection listed as unsourced, and the multiple is arithmetic on the two, so it
inherits that status. When the trading stopped, the same instruments were turned on my own
claims: `docs/PITFALLS.md` records fifteen of them failing their designed tests, each corrected
or retired, and results that could not be regenerated from the published data were deleted
rather than kept.

---

## Abstract

In 2024, the Solana memecoins that performed followed a repeatable accumulation pattern: fresh wallets created shortly before a token launch, funded through **ChangeNOW**, then accumulating meaningful portions of the supply one after another. Because that accumulation happened in public, outsiders could detect it early enough to participate.

This repository documents how the transition happened, built on thousands of transactions, hundreds of successful launches, and launches **verified by hand, transaction by transaction**.

---

## Act I: The 2024 Pattern

Before a pump.fun token existed, the wallets for it already did. Typically they were:

- created the same day as the token
- funded through ChangeNOW
- holding nothing else
- buying immediately after launch
- accumulating meaningful percentages of supply

They were funded from a single address, `G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t`, a hot wallet of the swap service **ChangeNOW**.[^gw] ChangeNOW breaks the on-chain trail, so the wallets appeared unrelated.

[^gw]: A [2025 research study on Solana mixers](https://medium.com/@smartgenuise806/the-shadow-economy-a-research-study-on-mixers-in-solana-3eebc60dcd2a)
    whose author routed his own test funds through ChangeNOW and observed them arrive at this
    address, and an [earlier public attribution](https://x.com/CrypticZK/status/1616072613356535808)
    of the same address to the same service. The attribution is external; this repository measures
    what leaves that address, not who runs it.

They weren't. The signal was hidden in the funding: large SOL transfers reaching multiple fresh wallets in **identical amounts down to nine decimals**. Coincidence does not produce that.

One case:

- 9 wallets
- all created that morning
- all funded with exactly **2.976815600 SOL**
- all funded within **343 seconds**
- token launched **7.6 hours** later

Nobody manually types nine identical decimal amounts.

It was a split.

Once one wallet bought roughly **2% of the supply** (around 20 million tokens), the rest almost always followed. That was enough to buy alongside them, ahead of the public.

---

## Exploiting the Pattern

As soon as one wallet bought, the others followed. The strategy waited for one configuration: a ChangeNOW-funded wallet buying at least **2% of supply** on a fresh pump.fun launch. Then I bought too: **1% of the supply at most**, never large enough to draw attention.

The bet was that the rest of the coordinated wallets would follow, draining available supply until retail buyers had almost no influence on price.

After every large gain I moved to a fresh wallet. Being copied would have ended the pattern faster than anything else: if everyone piled in alongside me, the edge closed.

From there the position was read off the operators' own behaviour, trade by trade, from the shape of the curve. A double top says they have set their exit and do not intend to carry it higher, so sell there; take profit into a move rather than chasing it past resistance; a lower high after a parabolic run is exhaustion, not a dip to buy. Only the hours away from the screen were fully automated.

Results, reconstructed on chain from the deposit address's own balance deltas:

| Metric | Value |
|---------|------:|
| Withdrawn, Oct–Dec 2024 | **1,190.6957 SOL** |
| USD at each transfer's own day price | **$237,137.87** |
| Incoming transfers, Oct–Dec 2024 | **245** |
| Distinct sending wallets, Oct–Dec 2024 | **74** |
| Example trades (a sample; the window holds hundreds) | **19 (+100% to +28,465%)** |
| Full window to 2 Feb 2025 | **$244,315.58** |

The two money rows are the strong ones: the net of every incoming transfer in the window, winners and losers alike, each valued at the SOL close of its own UTC day rather than at one average price. The wallet is a pass-through, and the totals close on themselves: **1,226.4663 SOL** arrived over the full window against **1,226.4566 SOL** swept out to the exchange.

The two count rows are weaker and method-dependent. A transfer here is one successful transaction carrying a positive balance delta, so a batched or multi-hop route counts once; a sending wallet is attributed as the counterparty with the largest opposing delta in the same transaction, which bounds the number of distinct senders without decomposing every transfer exactly.

The deposit address is published: **`6tmiM84AxMzmXzRByq7m1dgNkHtn9wp671e1GMe2ZmWU`**. It is my KYC'd exchange deposit address, so publishing it attaches my legal identity to this ledger permanently. What it buys: every number in the table stops being "trust the artefact" and becomes one explorer query, reproducible by anyone against the chain. Earlier commits redacted it behind a salted-HMAC label, `RDCT-838bf381fe`; the de-redaction is deliberate.

The artefact itself still publishes the 74 sending wallets as a count rather than a list. That is a limit of its scope and conceals nothing: with the address in the clear anyone can enumerate them on chain. And it claims the count, never the ownership: the same heuristic resolves four of the 74 to third-party exchange hot wallets this repository already labels elsewhere, so `docs/out/expl_ledger.json` files any identity behind a sending wallet under `NON_ETABLI`.

Receipts and methodology: `docs/EXPLOITATION.md` and `docs/PATTERN.md`. The reconstruction itself is `code/expl_ledger.py` → `docs/out/expl_ledger.json`.

---

## Act II: Closing the Leak

That was the trade from my side. From the operators' side, the model had one flaw: it was observable. Funding ran hours ahead of launch, accumulation was slow, anyone paying attention could buy beside them, and every SOL an outsider earned was one they didn't keep.

As their wallet inventory grew into the thousands, ChangeNOW became unnecessary. The public funding stage disappeared.

---

## Act III: What Replaced It in 2026

What replaced it does not shorten the observation window. It removes it.

The new mechanism is the **group snipe**: instead of accumulating publicly, insiders purchase essentially the entire bonding curve in the creation slot itself.

Measured across **42/42 manually verified launches**, every transaction individually checked:

- **85 SOL**
- approximately **79% of supply**
- purchased inside the token creation slot
- zero public bonding-curve purchases beforehand

On a **separate frozen sample** of **70 tokens reaching at least $500k market cap**, **58 (82.9%)** exhibit the same signature.

By the time trading becomes visible, market cap is already around **25×**, public buyers are already late, and insiders typically exit around **17.5 seconds** after launch.

---

## Real-World Example

This signature is now the norm. One instance: the launch associated with **ANSEM ("TheBlackBull")**, mint `9cRCn9rGT8V2imeM2BaKs13yhMEais3ruM3rPvTGpump`, created **2026-06-16 21:05:48 UTC**, creation slot **426930467**.

Measured independently, using the same frozen scripts as the previous 42 launches:

- entire bonding curve purchased in the creation slot: **85.007 SOL**
- **84.74 SOL** purchased by a single wallet
- only two buyers
- sixteen signatures
- nothing left for public buyers

Both wallets had already been catalogued inside this repository before the token existed:

| wallet | SOL at slot 0 | already in this repo as |
|---|---|---|
| `yHCxHBEa…6PRe` | **84.743** | a repeat operator on **24 of 282** tokens, explicitly *not* classed as shared infrastructure, `docs/out/m4_infra.json` |
| `9ryBR3Sn…XLaq` | 0.265 | a **shared-infrastructure sniper**, 5th by ubiquity at **44 of 282** tokens, `docs/out/m4_infra.json` |

The alert triggered immediately after creation.[^ansem]

[^ansem]: Deployer, the 650 M transfer and the holding range: [MEXC News](https://www.mexc.com/news/1182542)
    and [Phemex Academy](https://phemex.com/academy/black-bull-ansem-solana-meme-token). The 7 M$
    airdrop and the one-million-holder target: [CryptoBriefing](https://cryptobriefing.com/ansem-airdrops-7m-ansem-memecoin-solana/)
    and [The Defiant](https://thedefiant.io/news/defi/ansem-airdrops-usd7m-of-usdansem-memecoin-in-bid-to-reach-1m-holders).
    The two wallet rows are measured in this repository (`docs/out/m4_infra.json`); the slot-0 SOL
    amounts are not: no artefact of this repository covers this mint, and `code/p1_readme_check.py`
    lists them as unsourced. The mint and slot are published here so that the claim is falsifiable.

---

## Why Solana Memecoins Are Finished

In 2024, outsiders could observe accumulation, and that observation created the opportunity. Today, nothing reaches the public: across **42 out of 42** verified launches, the full pump.fun supply is purchased inside the creation block itself. Only insiders participate. Everyone else buys after the move.

The aggregates agree:

- only **0.26%** of pump.fun tokens now graduate
- Solana daily network fees fell roughly **84%**, from approximately **33,000 SOL/day** to roughly **5,300 SOL/day** by June 2026[^macro]

Solana, which runs in large part on memecoin activity, has shed billions in market cap as a result. People left memecoins because they were tired of no longer being able to win.

[^macro]: Graduation rate and fee decline: [DEXTools, 22 June 2026](https://www.dextools.io/news/pump-fun-graduation-collapse-solana-fees-2026).
    These are network-wide aggregates from an outside source; no script in this repository computes
    them, and `code/p1_readme_check.py` lists both as unsourced by the measurements here.
    For scale over the period this study covers, a Q4-2024 academic analysis put pump.fun at up to
    **71.1% of all Solana token mints** and **40–67.4% of all DEX transactions**.

The mechanism that made money in 2024 worked because outsiders could still join; closing that loophole removed the outsiders. The memecoin season didn't end because traders became worse. It ended because participation became impossible.

The public wasn't outcompeted. It was optimized out of the order flow.

---

## Author

**Benjamin Da Cunha.** Published under my name on purpose. The commit history is authored under it, the `teamdacunha` referral handle is left visible on the trade screenshots in `data/screens/trades/`, and the **$237,137.87** reconstructed on chain in the deposit ledger is mine. Commits, handle and money are the same person, and I am not anonymising any of it. That includes the KYC'd exchange deposit address itself, `6tmiM84AxMzmXzRByq7m1dgNkHtn9wp671e1GMe2ZmWU`, published above: earlier commits kept it behind a salted-HMAC label as an attack-surface precaution, and I have since chosen to publish it so the ledger is verifiable by anyone rather than only attested by me. The only redactions left in this repository are the slur-vanity identifiers, decency rather than secrecy. I do not present myself as a generic engineer: I find and exploit patterns, and this repository is the evidence, checked line by line by the code beside it.

For the record, and outside the measured perimeter: I began with roughly **$400** of starting capital, and my first trade on this pattern staked **1-2 SOL** and closed near **$2,000**. That is a Phase-0 recollection from before the 2024-10 window the ledger measures, and no artefact here reconstructs it: a deposit ledger sees proceeds landing on the exchange, not the buys that produced them. So `p1_readme_check.py` lists both figures as unsourced, exactly like every other number without an artefact behind it: the story is mine to tell, but only the measured figures are asserted as measured.

---

## Repository Structure

| Path | Description |
|------|-------------|
| `docs/PITFALLS.md` | Fifteen competing explanations, the tests designed to break each one, and what survived |
| `docs/METHODOLOGY.md` | Definitions, populations, validation protocol and declared limitations |
| `docs/RESULTATS.md` | Complete 2026 measurements with an English executive summary |
| `docs/PATTERN.md` | Funding distributions token by token with every detected burst |
| `docs/EXPLOITATION.md` | Trading methodology, automation, exit strategy, receipts and on-chain totals |
| `docs/SPLIT_PHASE1.md` | 2024–2025 split analysis with controls and null models |
| `code/` | One script per measurement (see `code/README.md`) |
| `data/` | Versioned derived datasets; network caches are ignored and reproducible |
| `figures/` | Figures regenerated by `code/f_figures_resultats.py` |
