# Why Solana Memecoins Are Over

## €400 to start. $237,137.87 withdrawn.

I started with **€400**.

Between **October and December 2024**, I withdrew **$237,137.87** trading memecoins on **pump.fun**.

I found a pattern in how fresh wallets were funded before launch. I traded the accumulation that followed.

Then the pattern disappeared.

**The mechanism had changed. I followed the money to find out how.**

This repository follows that trail: the pattern I traded, the launches I reconstructed, the recurring groups I identified, and the tests I ran to find another edge.

---

## What this repository demonstrates

This is not a tutorial and it is not a collection of screenshots.

It is a reproducible blockchain investigation built from transaction-level data.

The work covers:

* **Blockchain forensics**
* **On-chain transaction tracing and attribution discipline**
* **Wallet clustering and relationship analysis**
* **Funding-flow reconstruction**
* **Pattern and anomaly detection**
* **Detection of coordinated accumulation**
* **Real-time transaction monitoring**
* **Hypothesis testing and falsification**
* **Manual transaction verification**
* **Detection of instrumentation and data-quality failures**
* **Python-based data analysis**
* **Reproducible research**
* **On-chain financial-flow reconstruction**
* **Pre-registered hypothesis testing on a live detector's alerts**

The central question was simple:

> **What changed in the way successful Solana memecoins were accumulated, and could that change be measured directly on-chain?**

---

# My Trading Record

The pattern documented below is one I identified and traded myself, lawfully, under my own name.

I started with **€400**. Between October and December 2024, I withdrew **$237,137.87**.

The withdrawal figure is reconstructed directly from the blockchain by `code/expl_ledger.py` and reproduces from the committed artefacts.

My exchange deposit address is public. The transaction-level ledger is published. Anyone can reconstruct the withdrawals.

When the trading stopped, I turned the same methodology against my own claims. `docs/PITFALLS.md` documents fifteen competing explanations that were tested, corrected or retired. Results that could not be regenerated from the published data were withdrawn; `docs/PITFALLS.md` §18 lists them rather than silently removing them.

---

# Abstract

In 2024, some of the Solana memecoins that performed strongly followed a surprisingly repeatable accumulation pattern.

Fresh wallets appeared shortly before a token launch.

They were funded through **ChangeNOW**.

They accumulated meaningful portions of supply shortly after launch.

And because the accumulation happened publicly, somebody watching the chain closely could detect it early enough to participate.

I did.

The interesting part came later.

The wallets multiplied.

The funding pattern disappeared.

The public signal became harder to observe.

So I rebuilt the investigation from the blockchain and measured what changed.

Then I asked the question a trader would ask next: once the new mechanism is visible on chain, can it be traded?

Act IV is the answer. It is no, for a reason more precise than "the edge is gone".

The repository contains the data, scripts, validation procedures, competing hypotheses and transaction-level evidence behind that investigation.

---

# Act I — The 2024 Pattern

Before a pump.fun token existed, the wallets participating in it often already did.

Typically, they were:

* created the same day as the token
* funded through ChangeNOW
* holding nothing else
* buying immediately after launch
* accumulating meaningful percentages of supply

The funding trail led back to a single address:

`G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t`

a hot wallet attributed externally to the swap service **ChangeNOW**.[1]

ChangeNOW broke the direct on-chain trail.

The wallets therefore appeared unrelated.

They weren't.

The signal was in the funding behaviour.

Large SOL transfers reached multiple fresh wallets in **identical amounts, down to nine decimal places**.

One example:

* **9 wallets**
* all created that morning
* all funded with exactly **2.976815600 SOL**
* all funded within **343 seconds**
* token launched **7.6 hours later**

The interesting question was no longer:

> "Who is buying this token?"

It was:

> **"Why were these wallets funded in this exact configuration before the token even existed?"**

Once one wallet bought roughly **2% of supply** — around 20 million tokens — the others frequently followed.

That created something unusual in an otherwise chaotic market:

**a measurable, observable accumulation pattern.**

> **What Act I does and does not show.** The case above is one token. Across the 13 tokens measured, fresh wallets funded through the gateway before launch appear on 6, and several wallets at one identical amount on one of them, this one (`docs/PATTERN.md` §6; identical amounts are not required there, §2.4). That is a deliberately selected sample, not a prevalence estimate. The funding links these wallets on chain; that a single operator controls them is not established. And the split-funding detector of `docs/SPLIT_PHASE1.md` does not separate the tokens I traded: p = 0.0007 against dead tokens holds only with a criterion that also fires on 88.9 % of random wallet groups; without it, p = 0.060 against dead tokens and p = 0.44 against graduated tokens of the same period (§6.1).

---

# Exploiting the Pattern

Once I understood the pattern, I traded it.

The configuration I looked for was specific:

> A ChangeNOW-funded wallet buying at least **2% of supply** on a fresh pump.fun launch.

When that happened, I bought too — **1% of supply at most**, deliberately small enough not to become part of the signal.

The thesis was simple:

If the first wallet was part of a coordinated accumulation, the remaining wallets should follow.

The chain became the order-flow signal.

I did not need to know who controlled the wallets.

I needed to observe what they repeatedly did.

After every large gain, I moved to a fresh wallet. The objective was to avoid becoming another visible participant in the pattern I was exploiting.

The position was then managed from the operators' own behaviour: accumulation, curve shape, subsequent buying and eventual exhaustion.

The important point for this investigation is not the trading strategy itself.

It is that **the strategy depended on information being publicly observable on-chain.**

And eventually, that information stopped being observable.

---

# Results — $237,137.87 Reconstructed on Chain

The results below are reconstructed from the blockchain, from the deposit address's own balance changes.

| Metric                                     |             Result |
| ------------------------------------------ | -----------------: |
| Withdrawn, Oct–Dec 2024                    | **1,190.6957 SOL** |
| USD value at each transfer's own day price |    **$237,137.87** |
| Incoming transfers, Oct–Dec 2024           |            **245** |
| Distinct sending wallets                   |             **74** |
| Example trades in documented sample        |             **19** |
| Full window through 2 Feb 2025             |    **$244,315.58** |

The money rows are the strongest measurements.

Each transfer is valued using the SOL close of its own UTC day rather than a single average price.

The ledger also closes internally:

**1,226.4663 SOL** arrived over the full window against **1,226.4566 SOL** swept out to the exchange.

The transfer and wallet counts are more method-dependent. A transfer represents a successful transaction carrying a positive balance delta, while the sending wallet is attributed using the largest opposing delta in that transaction.

Those definitions are documented rather than hidden.

---

# The Evidence Is Public — Follow the Money

The deposit address used for the reconstruction is published:

`6tmiM84AxMzmXzRByq7m1dgNkHtn9wp671e1GMe2ZmWU`

It is my KYC'd exchange deposit address.

Publishing it was deliberate.

It means the central financial result does not depend on trusting a screenshot or trusting me.

Anyone can query the address on-chain and reproduce the ledger.

The reconstruction is:

`code/expl_ledger.py` → `docs/out/expl_ledger.json`

The 74 sending wallets are published as a count rather than as a curated identity list. Where the methodology cannot establish ownership, the repository does not claim ownership.

For example, four of the 74 are resolved by the same methodology as third-party exchange infrastructure and are therefore recorded as `NON_ETABLI` rather than assigned to an individual.

That distinction matters in blockchain investigations:

**transactional relationship is evidence; ownership attribution requires additional evidence.**

---

# Act II — Closing the Leak

That was the trade from my side.

From the operators' side, the model had an obvious weakness:

**it was observable.**

Funding happened hours before launch.

Accumulation happened slowly enough to detect.

The wallets became visible.

And anyone watching the chain could buy alongside them.

As the wallet inventory grew into the thousands, the original funding mechanism became less useful.

The public funding stage disappeared.

The question was no longer:

> "Can I detect the accumulation?"

It became:

> **"Can accumulation still be detected before the public gets there?"**

That is what led to the next investigation.

---

# Act III — What Replaced It

What replaced the previous pattern does not simply shorten the observation window.

**It removes it.**

The new mechanism I identified is what I call the **group snipe**:

instead of accumulating publicly after launch, a group purchases essentially the entire bonding curve in the token's creation slot itself.

The measurement was performed across **42/42 manually verified launches**, with each transaction checked individually.

The observed signature:

* approximately **85 SOL**
* approximately **79% of supply**
* purchased inside the token creation slot
* **zero public bonding-curve purchases beforehand**

I then tested the same signature on a **separate frozen sample** of 70 tokens reaching at least $500k market cap.

**58 of 70 (82.9%)** exhibited the same signature.

This separation between the discovery sample and the frozen sample is deliberate.

It prevents the measurement from simply becoming a collection of examples selected after seeing the result.

> **What the frozen sample tests.** One thing: at least 60 SOL bought inside the creation slot, whatever the number of buyers (25 of the 58 have one or two buyers in that slot, `data/v09_signature_gros_tokens.json`). Three of the 70 tokens are also among the 42 (`data/v05_creation_block.json` against `data/v09_signature_gros_tokens.json`); without them the rate is 55 of 67. The sample is selected on outcome (tokens that reached $500k), so it shows that the signature is common among large tokens, not that it makes them large (`docs/RESULTATS.md`).

---

# Real-World Example

One instance is the launch associated with **ANSEM ("TheBlackBull")**:[2]

Mint:

`9cRCn9rGT8V2imeM2BaKs13yhMEais3ruM3rPvTGpump`

Created:

**2026-06-16 21:05:48 UTC**

Creation slot:

**426930467**

Using the same measurement scripts:

* **85.007 SOL** purchased in the creation slot
* **84.74 SOL** purchased by a single wallet
* only **two buyers**
* **sixteen signatures**
* no bonding-curve supply left for public buyers

Both wallets recur in the repository's wallet catalogue, built from launches of 27 June to 4 July 2026, after this one.

One was a repeat operator observed across multiple tokens.

The other was classified as shared infrastructure.

An alert fired on it shortly after creation; no log of that alert is published.

This is the point where the repository moves from historical analysis to something closer to **transaction monitoring**:

a behavioural signature can be defined, measured, and triggered on a new event.

> **Provenance and limits.** No artefact of this repository measures this launch's creation slot: `code/p1_readme_check.py` lists the figures above as unsourced, and the mint is published so they can be re-measured. What is committed: the launch's creation time and its creator in the pump.fun record (`data/bundle/frame_ath.json`, `data/bundle/_frame_ath_raw.json`), the creator being the repeat-operator wallet; and the catalogue that classifies the two wallets (`docs/out/m4_infra.json`: 24 and 44 of 282 launches). Who controls that wallet is not established: nothing here attributes it, or the purchase, to any person, including the public figure the token's name refers to. This launch is also outside the 1,657 alerts of Act IV: that detector started on 21 August 2026, and its rule (at least four wallets of 5 SOL or more) excludes a two-buyer block (`post_detection_edge/tables/T7_robustness.md`).

---

# Act IV — I Found the Teams. The Tests Found No Edge.

A live detector ran from 21 August 2026.

It is a separate project whose code is not published; this repository holds its frozen alert journal (`post_detection_edge/data/`).

Its rule is stricter than the Act III signature: at least four wallets of 5 SOL or more inside the creation slot. It was not watching for at least ~600 of the ~930 hours, mostly while the machine slept, so launches in those hours are missing (`post_detection_edge/results.md`).

By 29 September it had alerted on **1,657 launches**.

Which raised the question anyone who traded Act I would ask next:

> **Once the group snipe is visible on chain, can it be traded?**

Nine pre-registered studies and one systematic search later, the answer, within what was tested, is no.

The reason is the interesting part.

## What was tried

Each study was written as a plan before its rates were computed, and ended with a verdict.

The studies that tested a signal read the alerts after 15 September as their hold-out, one after another.

| question | verdict |
|---|---|
| Does buying right after the alert still pay? | Statistical signal, no tradable edge (`post_detection_edge/`) |
| Does the bundle's on-chain structure say which launches double? | No robust separation (`post_detection_forensics/`, `entry_zone/`, `sniper_capital/`) |
| Do the buying wallets act as a group? | Yes, in about four launches out of five (`coordination_detection/`) |
| How does the group operate? | A repeatable loop: one funder, four snipers, 78 % of the supply, exit wallets, the capital back, the same snipers funded again a median 21 minutes later (18 in the validation weeks) (`economic_mechanics/`, `exit_destination/`, `funder_network/`) |
| Is "a group we have already seen" a live signal? | No incremental signal (`known_group_reentry/`) |
| Is there any rule at all, over 415 features? | No exploitable pattern found (`alpha_patterns/`) |
| Do the teams, their rhythm, or the absorption of their inventory predict the outcome? | No (`alpha_patterns/`, three mechanism studies) |

## The teams exist

On the **1,015 launches** before 15 September 2026, **612** had an observable one-hour outcome and **168 (27.5 %)** doubled from the entry price read 5 to 15 s after the alert (the declared trade buys at alert + 5 s).

Shared wallets, shared funders and identical ticket configurations confirm each other **47 to 212 times** above chance: the operators are real, recurring on-chain entities, though who controls them is not established.

**33 teams** have five or more observable launches; **19** have ten or more.

Their doubling rates differ a little more than chance would allow, from **0 % to 58 %**, and the difference survives the calendar day and the entry price (p = 0.0017 within the day).

## The same teams make GOOD and BAD

**28 of the 33 teams** have both.

A team's history does not predict its next launch: the rule that bets on teams with a strong record is right **3 times in 29**, against **44.1 %** for the launches it leaves aside.

The rhythm is real, one launch every **20.6 minutes** in the median inside a session, and it does not determine the outcome: 17 pre-registered tests, none passes.

Inside a team, **32 variables** measured before the alert (configuration, wallets, funders, tickets, synchronisation, concentration, rhythm, swarm, other teams, market) show no detectable separation: none passes the correction.

## Absorption comes too late

The last hypothesis was that a GOOD launch is one where outside demand absorbs the team's inventory.

Forty seconds after the creation, the team has sold **4.6 %** of what it holds on a GOOD launch and **4.5 %** on a BAD one (on the 78 GOOD and 213 BAD launches observed that long).

Outside buyers have paid for about one tenth of its value, on both: **11.0 %** on the GOOD launches and **9.9 %** on the BAD, 27 s after the alert.

The price of a GOOD launch is at **×1.09** thirty seconds after the entry and **×1.55** after five minutes; a BAD one at **×1.01** and **×0.64**.

The confirmed doubling arrives a **median 375 s** after the entry; **1.2 %** of the GOOD launches confirm it within 30 s.

Forty tests of demand at the moment of decision: none passes.

## Where the information moved

![F5. Where the information sits](figures/f5_act_iv_information_timing.png)

In 2024, in the reference case of Act I, the signal came **7.6 hours** before the launch, and the move it announced happened in public afterwards.

In 2026 the coordination is on chain in the creation slot itself, the detector alerts a median **12.6 s / 12.3 s** after the creation (GOOD / BAD launches), and the outcome is decided minutes later, inside the price.

The window in between is where an entrant has to decide, and it holds structure, not prediction.

## Structural signal, predictive signal

A structural signal says who is launching, and how.

A predictive signal says which launch will double.

This repository establishes the first and did not find the second.

> We found a strong structural signal of coordinated launch-time accumulation. The analyses performed did not establish that this signal, or anything else observable before the entry, was sufficient to predict which launches would subsequently produce the measured price outcome.

Most figures in this act are checked against their artefact by `code/p1_readme_check.py`; the four quoted from the studies' results tables (78 % of the supply, four snipers, 21 and 18 minutes, four launches out of five) are listed by it as unsourced. The full chapter, hypothesis by hypothesis, is `docs/ACT_IV.md`; the search itself is `alpha_patterns/`.

**Exploratory, not validated out of sample.** These analyses ran on the first 1,015 alerts. One pre-declared rule was read once on the following week and failed. The last week was never read by this search; those alerts had already served as the earlier studies' hold-out, so no block of the snapshot is untouched, and a confirmation has to come from new alerts.

---

# Why Solana Memecoins Are Over

The story of this repository is a single chain of questions.

1. In 2024 I had an observable edge: wallets funded hours before a launch, accumulating in public.
2. The mechanism changed, and the edge went with it.
3. I identified what replaced it: the group snipe, the whole curve bought in the creation slot, on **42/42** manually verified launches and **58 of 70 (82.9%)** of an independent frozen sample, approximately **79% of supply** on the 42 verified launches.
4. I then asked whether the new mechanism could itself become an edge.
5. I identified the teams and their structure.
6. I tried their rhythm.
7. I tried the configuration of their bundles.
8. I tried to tell their GOOD launches from their BAD ones.
9. I tried the absorption of their inventory by outside demand.
10. Nothing tested gave a signal early enough to act on.
11. That is the result: the market now reveals the coordination of a launch without revealing, early enough, whether it will succeed.

In 2024, outsiders could observe accumulation, and that observation was the opportunity.

By 2026 the same activity happens inside the creation slot, and what the public sees first is the market after it.

The information advantage did not just shrink.

It moved: from the funding, hours ahead of the launch, to the demand, minutes behind the entry.

The conclusion I can defend from the on-chain evidence is narrower:

> **The observable accumulation pattern that made the 2024 strategy possible was replaced by a launch-time mechanism whose coordination is observable, and whose outcome was not found to be predictable early enough to trade.**

The public wasn't simply outcompeted.

**The observable order flow changed, and the part of it that predicts moved out of reach.**

---

# What I Tried to Prove Wrong

A blockchain pattern is not interesting because it looks convincing.

It is interesting if it survives attempts to explain it away.

`docs/PITFALLS.md` contains fifteen competing explanations and the tests used against them.

Among the questions I forced the analysis to answer:

* Could exchange infrastructure create the apparent clustering?
* Could batched transactions distort the counts?
* Could unrelated wallets happen to receive identical funding?
* Could bots explain the synchronization?
* Could the observed wallets simply be infrastructure?
* Does temporal proximity actually establish coordination?
* Can wallet activity establish common ownership?
* Can the result be reproduced from frozen data?

Some hypotheses survived partially.

Some were rejected.

Some claims were narrowed.

Some measurements were removed.

That is part of the result.

---

# Methodology

The investigation is built around a simple principle:

> **Every important claim should be traceable to an artefact, a transaction, or an explicitly identified external source.**

The workflow is approximately:

```text
Raw on-chain data
        ↓
Transaction normalization
        ↓
Wallet identification
        ↓
Funding-flow reconstruction
        ↓
Wallet clustering
        ↓
Temporal / behavioural analysis
        ↓
Hypothesis testing
        ↓
Manual verification
        ↓
Reproducible result
```

The repository distinguishes **reproducible measurements**, **analytical interpretations**, **external sources**, and **my firsthand trading account**.

---

# How It Is Built and Checked

[![ci](https://github.com/searadacunha/Why-Solana-Memecoins-Are-Over/actions/workflows/ci.yml/badge.svg)](https://github.com/searadacunha/Why-Solana-Memecoins-Are-Over/actions/workflows/ci.yml)

I built the Python pipeline that collects and rebuilds the transactions, the checks that try to break the conclusions (`docs/PITFALLS.md`), and a CI that fails when a committed table, or one of the 43 README figures it tracks, no longer matches the code behind it. I work with AI coding agents (Claude Code); the commits they co-wrote carry a co-author line.

## At a glance

| | |
|---|---|
| **Trading record** | I started with **€400** and withdrew **$237,137.87** in October–December 2024. The withdrawals are reconstructed from my public exchange deposit address. |
| **Question** | Can coordinated buying around token launches be measured from public chain data alone, and does it tell you which launches will succeed? |
| **What I built** | A Python pipeline, one script per measurement, that reads Solana blocks and transactions over RPC and rebuilds funding flows, launch-time purchases and exits. Every script under `code/` that computes a number uses the standard library only. |
| **How it is checked** | On every push, GitHub Actions reruns the 22 offline scripts and checks that each output is byte-identical to the committed one, checks 43 README figures against their sources, and runs 76 unit tests, type checks, a linter and a publication gate. |
| **Research design** | Nine studies on the 1,657 alerts of a live detector, each with a written plan, a frozen input table (SHA-256) and a verdict, then one exploratory search over 415 features. |
| **Measured** | 2024: fresh wallets funded through the same swap service before launch, on 6 of 13 measured tokens. 2026: the token's sale curve bought in the very block (slot) that creates the token, on all 42 launches of recurring buyer groups rebuilt transaction by transaction, a selected sample rather than a market-wide rate. The groups behind the 2026 alerts recur from launch to launch. |
| **Negative results** | No tradable edge. One of 12 signals locked before the test survived it (the chance of doubling within 15 minutes rose from 31.0 % to 45.7 %) and still lost money after costs. The search over 415 features found nothing exploitable. The 2024 funding signature stops separating the tokens I traded once a criterion that also fires on random wallets is removed (`docs/SPLIT_PHASE1.md` §6). |
| **Not established** | Who controls the wallets: links are measured, ownership and intent are not attributed. The live detector's code, a separate project: only its frozen alert journal is here. The October 2026 search (`alpha_patterns/`) is exploratory, not validated out of sample. |

## Where to look

| To check | Open |
|---|---|
| Python and data processing | `code/`, one script per measurement; shared logic in `statlib.py`, `splitlib.py`, `pumplib.py`, `common.py` |
| RPC and API integration | `code/rpc_client.py`, the RPC client of `code/`: key rotation, a cooldown after HTTP 429, bounded retries, and one error rule: a failed call raises, it never returns an empty result |
| Fund tracing | `code/02_cn_outflows.py` (a swap service's hot-wallet outflows, grouped into identical-amount splits), `code/05_trace_origin.py` (a wallet's origin past the RPC's 1,000-signature page limit, without pretending the start of its history was reached) |
| Pipeline and automation | `code/run_all.py` (runs the measurements by tier, then byte-compares the artefacts), `.github/workflows/ci.yml` |
| Detection logic | `code/v05_creation_block.py` and `code/v06_curve_ladder.py` (launch-block reconstruction), `code/splitlib.py` (identical-amount funding bursts), `code/a1_null_model.py` (how often the funding detector fires on random wallets) |
| Testing and validation | `tests/`, `code/p1_readme_check.py` (this README's figures against their artefacts), `code/p0_pitfalls_check.py`, `code/check_no_secrets.py` |
| Statistics | `code/statlib.py`, the cluster bootstraps in `code/pumplib.py` and `code/t1_base_rate_sorties.py`, `post_detection_edge/code/an_40_signals.py` (logistic regression and decision trees written from scratch, chosen on validation, locked before the test split was read) |
| Data-quality failures caught | `docs/PITFALLS.md`: an HTTP 403 that had become "no data" (P6b), a detector that needed its own null (P13), a network failure that looked like a result (P15) |
| Research design | `post_detection_edge/` (plan, lock, test split), `docs/ACT_IV.md`, `alpha_patterns/` |
| Method | `docs/INVESTIGATION.md`, `docs/METHODOLOGY.md`, `code/README.md` |

Some script names, JSON keys, console messages and the `alpha_patterns/` working notes are in French; this README and `docs/` are in English.

## Verify it yourself

Python 3.12 or 3.13, nothing to install, no key:

```bash
git clone https://github.com/searadacunha/Why-Solana-Memecoins-Are-Over.git
cd Why-Solana-Memecoins-Are-Over
python3 code/run_all.py --strict
python3 code/p1_readme_check.py
```

The first command ends with `22 ran, 20 skipped, 0 failed` and `every committed table and JSON reproduced byte for byte`, in about 30 seconds. The second prints the claim ledger, every sourced row `OK`, then the figures that have no artefact. The rest of the CI needs `pip install pytest mypy ruff`, then `python3 -m pytest -q` (76 passed) and `ruff check .`. Python 3.9 to 3.11 also run the scripts, but two floating-point aggregates then differ in their last digits, so `--strict` is byte-exact on 3.12 and 3.13 only.

What a clone does not rerun:

* Of the 42 scripts `run_all.py` lists, 13 need the network (a Solana RPC key, public price APIs), 5 a raw capture corpus that is not published, and 2 redraw figures with matplotlib; the runner names each one and why. The 2024 collection scripts outside it (`code/01_*.py` to `code/08_*.py`, `code/scan_gateway_dispatch.py`) need the network too. The outputs the offline scripts read are committed.
* CI does not run the nine studies or `alpha_patterns/`. `post_detection_edge/` reruns offline from its committed snapshot. The analysis scripts of `economic_mechanics/`, `exit_destination/` and `funder_network/` need an on-chain cache that is not committed: without it they finish without an error but write different numbers over their committed tables (a known defect, so run them in a scratch clone), and their post-hoc scripts stop on the missing cache. The `alpha_patterns/` scripts need unpublished derived files; `alpha_patterns/code/chk_00_integrity.py` checks the published hashes offline.
* The live detector is not published.

---

# Repository Structure

| Path                   | Description                                                                         |
| ---------------------- | ----------------------------------------------------------------------------------- |
| `docs/PITFALLS.md`     | Fifteen competing explanations, the tests designed to break them, and what survived |
| `docs/METHODOLOGY.md`  | Definitions, populations, validation protocol and declared limitations              |
| `docs/RESULTATS.md`    | The 2026 launch measurements in full: creation-slot signature, entry prices, exits, horizons |
| `docs/PATTERN.md`      | Funding distributions token by token with detected bursts                           |
| `docs/EXPLOITATION.md` | How I traded the pattern, the screenshotted receipts, and the on-chain totals       |
| `docs/SPLIT_PHASE1.md` | 2024–2025 split analysis with controls and null models                              |
| `docs/ACT_IV.md`       | Act IV in full: the studies after the detector, hypothesis by hypothesis, every figure traced to an artefact |
| `docs/INVESTIGATION.md` | The investigation framework used throughout                                        |
| `alpha_patterns/`      | The exploratory pattern search of October 2026: plan, pre-registrations, reports, result JSON, scripts, test registry, audits |
| `post_detection_edge/` … `known_group_reentry/` | Nine pre-registered studies, run 29 September to 1 October 2026 on the detector's 1,657 alerts of 21 August to 29 September 2026, each with its plan and results. `post_detection_edge/data/` holds the detector's frozen alert journal |
| `code/`                | One script per measurement, the runner, the RPC client and the publication gate; `code/README.md` explains how to reproduce each |
| `tests/`               | Unit tests for the shared libraries, the RPC client and the publication gate        |
| `.github/workflows/ci.yml` | The checks run on every push (see Verify it yourself)                           |
| `data/`                | Versioned derived datasets                                                          |
| `figures/`             | Figures regenerated from the analysis scripts (`code/f_figures_resultats.py`, `code/f_act_iv_timeline.py`) |

---

# Author

**Benjamin Da Cunha**

I published this investigation under my real name deliberately.

`teamdacunha` is the display name of my GitHub account.

The trading screenshots retain the `teamdacunha` referral handle.

The **$237,137.87** withdrawal figure is reconstructed from my own exchange deposit address.

The chain, the code, the artefacts and the person behind the investigation are therefore connected.

This repository is an investigation, not a software product.

What it shows is a way of working:

> **I find patterns in data, build the tools to measure them, try to break the hypotheses, and turn the surviving evidence into a reproducible result.**

Here the data was the Solana chain, and the tools were RPC collection, transaction reconstruction, a test suite and a CI that checks the prose against the measurements. That approach is what I would bring to transaction monitoring, fraud investigations, data pipelines and automation; this repository shows it on one domain.

That is the work I want to keep doing.

---

# Footnotes

1. A [2025 external study on Solana mixers](https://medium.com/@smartgenuise806/the-shadow-economy-a-research-study-on-mixers-in-solana-3eebc60dcd2a) observed funds routed through ChangeNOW arriving at the address used in this investigation. An [earlier public attribution](https://x.com/CrypticZK/status/1616072613356535808) also associates the address with the service. The repository measures what leaves the address; it does not independently establish who operates it.

2. External sources on the ANSEM / Black Bull launch: [Phemex Academy](https://phemex.com/academy/black-bull-ansem-solana-meme-token), [CryptoBriefing](https://cryptobriefing.com/ansem-airdrops-7m-ansem-memecoin-solana/) and [The Defiant](https://thedefiant.io/news/defi/ansem-airdrops-usd7m-of-usdansem-memecoin-in-bid-to-reach-1m-holders). The recurrence of the two wallets is measured in this repository (`docs/out/m4_infra.json`); the slot amounts, the buyer count and the signature count are not, and `code/p1_readme_check.py` lists them as unsourced.
