# The Gateway Dispatch: A Launch-Funding Pattern

> **A transaction-level reconstruction of a launch-funding mechanism on Solana, and the detector built to find it.**

This chapter documents a funding mechanism observed on Solana during the **2024–2025 window**.

It does four things:

1. defines the mechanism from observable on-chain properties;
2. reconstructs it through transaction-level examples;
3. describes the detector used to identify it automatically;
4. tests how far the evidence can support attribution across tokens.

The analysis deliberately separates:

* **presence** from **frequency**;
* **technical linkage** from **identity**;
* **measured facts** from interpretation;
* **unmeasurable cases** from genuine negative results.

### Scope limitation

This is **not a prevalence estimate**.

The tokens in this chapter were selected on their observed outcome, so the data cannot support a statement such as:

> “X% of launches use this mechanism.”

Presence is established; frequency is not.

See `SPLIT_PHASE1.md` §5 and `code/a4_selection_bias.py` for the selection-bias analysis.

---

# 1. The Mechanism

The pattern is defined by **four properties occurring together**.

| # | Property                                                                                                          | Why it matters                                                                                                                                |
| - | ----------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 | The buyer wallet is **fresh** and was created shortly before the purchase                                         | A wallet with an established history is an existing participant; a newly created wallet may have been provisioned specifically for the launch |
| 2 | The wallet is funded **directly by the swap gateway**                                                             | This is the observable entry point onto Solana and the point at which upstream provenance becomes difficult to trace                          |
| 3 | The funding amount is a **conversion output**, with nine significant decimals rather than a round transfer amount | `2.976815600` is consistent with a swap output; `3.000000000` is consistent with an intentionally specified transfer                          |
| 4 | The funding arrives **before the token exists**                                                                   | A payment after token creation cannot have funded the initial purchase                                                                        |

The third and fourth properties are particularly discriminating.

An active period can naturally produce wallets that share a funder.

It is substantially more specific to observe multiple fresh wallets receiving the **same nine-decimal amount from the same gateway within a short interval**, hours before the target token exists.

---

## 1.1 Gateway Attribution

The gateway address is represented here as:

**G2Y**

Full address:

`G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t`

The source document reports that this address has been publicly attributed to a hot wallet of **ChangeNOW** by two independent public sources:

* a 2025 research study in which the author reports observing test funds arrive there;
* an earlier public attribution.

Neither source is presented as an official exchange label.

The identification is therefore treated as:

> **Publicly attributed, not officially confirmed.**

Reaching the gateway is a **routing observation**.

This analysis does not establish what any service knew, intended, permitted, or prohibited.

No involvement or wrongdoing is attributed to the service, company, or any person.

---

# 1.2 Two Layers, One Hop Apart

The gateway does not always fund the final buyer wallets directly.

In some cases it first funds an intermediate distributor, which subsequently distributes the capital in round amounts:

```text
gateway
   │
   │ conversion output
   ▼
distributor
   │
   │ round amounts
   ▼
fresh wallets
   │
   ▼
buys
```

Both layers are part of the observed mechanism.

This distinction matters for detection.

A detector that requires the **conversion-output signature to appear directly at the buyer-wallet layer** will miss cases routed through a distributor.

The first implementation did exactly that: it returned zero on all 15 tested tokens, including the reference case.

The resulting rule is:

> **Report the amount structure when present; do not require it as a hard criterion.**

---

# 2. Transaction-Level Examples

The following cases illustrate the mechanism from different angles.

They are not presented as a statistical sample.

They are forensic examples showing how the pattern manifests on-chain.

---

## 2.1 h2w6gm6jz — Nine Wallets, One Amount

Token creation:

**2024-12-13 14:50 UTC**

Approximately 7.5 hours earlier, nine fresh wallets each received exactly:

**2.976815600 SOL**

from the gateway.

| Wallet                                         |      Amount | Time UTC |
| ---------------------------------------------- | ----------: | -------- |
| `Csye9QE8LomP9RHzQAWLVh8XFdyNXvaopzrAuo3a1PoW` | 2.976815600 | 07:07:49 |
| `BmkuX6DaZUp9UCeR3XqAD6NjSpiFySnBvXyLT9uo7ZEA` | 2.976815600 | 07:08:02 |
| `AwQqcqdQQ3zydrtWMVF1PPDaWMNK7Lmhm3sUyDNGnSSY` | 2.976815600 | 07:09:04 |
| `3bBaA1MpQZuQpHjWZBEig12JB1W1TTQikxYPjUgGG3kU` | 2.976815600 | 07:10:12 |
| `CDvfNWiamAR1B84GUgttvDCGtiQE5dvJ49toF4fzsV5g` | 2.976815600 | 07:10:31 |
| `92w4K8uLg78KHWHxRovTDksLmou7MekcenY5PntPR34R` | 2.976815600 | 07:10:53 |
| `6QMshP9zwFXKbpLPh7w8EwadjA6vVasKAC7zu5HfMA22` | 2.976815600 | 07:11:20 |
| `BXuznwXTXt4QbLtLTkQnKNaXwdJ4PDXHvDcXf9DMogxe` | 2.976815600 | 07:11:53 |
| `5ibajLyeBmJhDfyZJN9FQsJBi48h8QSYg7eHGGhFjog6` | 2.976815600 | 07:13:32 |

The sequence has four simultaneous characteristics:

* nine fresh wallets;
* identical nine-decimal funding;
* one gateway;
* 343 seconds from first to last funding;
* all funding occurs hours before token creation.

The repeated amount is treated as a conversion output rather than an arbitrary manually specified transfer.

---

## 2.2 The Same Conversion Output on Another Token

The exact amount:

**2.976815600 SOL**

also appears on a fresh SAFFRON wallet:

`wbzkg9ftnVEMzeCL6wW8bpNTPDQWhBBnKo3JWJe3wh5`

Timestamp:

**2024-11-12 13:16:45**

This is 31 days before the h2w6gm6jz burst and originates from the same gateway.

A swap output depends on the input size, route, and price at execution.

The recurrence of the exact nine-decimal amount across two unrelated launches is therefore treated as evidence of a repeated operation rather than a repeated coincidence.

No further attribution is made from this observation alone.

---

## 2.3 ACID — The 40-Buyer Limit Hid the Pattern

Token creation:

**2024-12-09 09:47**

Three relevant fresh wallets were gateway-funded during the preceding week:

| Wallet                                          |      Amount | Time UTC            |
| ----------------------------------------------- | ----------: | ------------------- |
| `DrL5h6A1CyH1XDVsFd78Fnn4Nkx37GrQzqcPiKAaoFiq`  | 1.526056960 | 2024-12-02 09:53:14 |
| `DrL5h6A1CyH1XDVsFd78Fnn4Nkx37GrQzqcPiKAaoFiq`  | 0.739421380 | 2024-12-03 07:27:43 |
| `RwdMax1heLzDiBSk3g3MgvRuJkQYz7tnj96RFpbxxVA`   | 1.958393160 | 2024-12-08 10:18:22 |
| `D3JwQSGkn8YUzCDKDMphDhVbsEeK9qbttU971cqmFEKRM` | 1.504465720 | 2024-12-08 21:39:19 |

ACID returned zero in earlier detector runs.

The reason was not absence of the pattern.

The earlier scan stopped after the first **40 buyers**.

ACID had **743 buyers**, and the relevant wallets appeared later in the curve.

The cap produced the false negative.

This is why the final scanner walks the complete buyer population rather than assuming the first 40 buyers are sufficient.

---

## 2.4 SAFFRON — One Wallet Funded Four Times

Token creation:

**2024-11-12 22:54**

Three fresh gateway-funded wallets were identified.

One wallet,

`wbzkg9ftnVEMzeCL…`

received four separate payments during the preceding nine hours:

| Time     |          Amount |
| -------- | --------------: |
| 13:16:45 | 2.976815600 SOL |
| 13:53:56 | 2.380415590 SOL |
| 14:16:27 | 9.894826000 SOL |
| 21:27:20 | 7.778694250 SOL |

Two additional wallets received:

* 1.982815600 SOL
* 8.624207890 SOL

on the preceding day.

The amounts vary, but the observed structure remains:

**fresh wallet → gateway funding → launch**

Repeated top-ups into the same fresh wallet before creation are therefore treated as a variant of the mechanism rather than requiring identical amounts.

---

## 2.5 QAMI — Two Wallets the Day Before

Token creation:

**2024-12-31 23:41**

Two fresh wallets received gateway funding the previous day:

* `6nGLeqP1BW1MWrMsC7EYA57iei1V5XfpEW7YqdgFNA4K`

  * 4.949823400 SOL
  * 2024-12-30 17:31:45

* `E2wJyPwoJAydxYpvKSv1uRSS9GdEzX8gpfqeWsaVHcab`

  * 0.481875600 SOL
  * 2024-12-31 17:19:21

The second payment occurs approximately six hours before token creation.

---

## 2.6 sumiko — Two Wallets Seven Minutes Apart

Token creation:

**2024-12-26 13:25**

Two fresh wallets received gateway funding shortly before creation:

* `AJq5My8GFG6Jo7Pq…`

  * 1.446086 SOL
  * 12:55:43

* `FYG2cyAmhKGyRnH5…`

  * 0.739785 SOL
  * 13:02:00

The first payment occurred 29 minutes before the token existed.

Both wallets are fresh and both are gateway-funded.

---

## 2.7 CHOCO — Both Layers on One Token

Token creation:

**2024-10-10 13:35**

Two fresh wallets were funded directly by the gateway:

* `Edx7xy6RG8nchSE833xJNGjNBL4QdZV587Zk8GZ3Kpho`

  * 1.207495600 SOL
  * 09:24:43

* `4f6geAMUGzekQd3HemzHKWhJN9DiquNwTTtypPZckMQ5`

  * 2.307396470 SOL
  * three days earlier

The same token also contains the **distributor layer**.

A distributor created that morning was funded by the gateway at **13:26** and, five minutes later, distributed:

**20 × 0.300000000 SOL**

to 20 fresh wallets in a single transaction.

The distributor was never used again and has only 30 signatures in its lifetime.

This token therefore contains both observed layers of the mechanism:

```text
gateway → fresh buyer wallets
```

and:

```text
gateway → distributor → fresh buyer wallets
```

---

# 3. Automatic Detection

The repository implements the analysis through four scripts.

All are standard-library based; the offline components require no key.

| Script                      | Function                                                                                                                                       |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `code/a5_author_pattern.py` | Scans buyer funding for fresh wallets receiving near-identical amounts in a burst; sweeps thresholds instead of selecting one arbitrary cutoff |
| `code/a6_gateway_chains.py` | Reconstructs dated gateway → distributor → wallet chains while enforcing chronology                                                            |
| `code/a1_null_model.py`     | Measures how frequently each criterion fires on random wallets                                                                                 |
| `code/a3_hub_origin.py`     | Traces a distributor toward its genesis and records whether genesis is reached                                                                 |

Primary commands:

```bash
python3 code/a5_author_pattern.py
python3 code/a6_gateway_chains.py
```

---

# 3.1 Four Requirements for a Reliable Detector

## 1. Reach genesis — or explicitly report that you did not

`getSignaturesForAddress` retrieves history backwards in pages of 1,000.

If the walk is arbitrarily truncated, the scanner may see only recent activity.

That creates a dangerous false negative:

> “No funding found”

when the actual result is:

> “Funding not found within the portion of history inspected.”

Because funding often occurs near a wallet's first transactions, every negative result must carry the scope of the historical search.

---

## 2. Make transport failures loud

A client that returns `None` on error, followed by code such as:

```python
result = response or []
```

can silently transform:

**API failure → empty dataset → false negative**

This happened in the project.

A wrong hostname produced:

**0/14 tokens**

instead of an error.

The corrected rule is:

> **Errors raise. Unmeasurable tokens are reported separately from measured negatives.**

The complete incident is documented in `PITFALLS.md` P15.

---

## 3. Define a null distribution before trusting a detector

Every criterion must first be tested on a population where coordination is not known to exist.

The procedure is:

1. pool wallets outside the target structure;
2. randomly draw groups;
3. apply the exact detector criterion unchanged;
4. measure its baseline firing rate.

The intuitive criterion:

> “These buyers share a funder”

fires on:

**88.9% of random 40-wallet groups.**

That criterion was therefore retired.

A detector that fires on most random groups is not a detector of the phenomenon.

---

## 4. Enforce chronology

The funding chain must satisfy:

```text
gateway payment
       ↓
distributor payment
       ↓
wallet
       ↓
token purchase
```

in chronological order.

Without this constraint, the chain builder produced impossible histories, including a gateway payment in 2024 apparently feeding a wallet payment from 2022.

Chronology is therefore a hard validity condition, not an optional annotation.

---

# 3.2 Making a Full-Curve Scan Tractable

Scanning every buyer is more expensive than scanning the first few buyers.

Freshness provides a useful early stopping condition.

A wallet that has activity older than:

**creation time − N days**

is no longer eligible to be classified as fresh.

The scanner can therefore walk backwards through the wallet's history and stop as soon as it encounters activity older than the freshness window.

This produces two benefits:

* old, high-activity wallets can be rejected quickly;
* the scan can cover the **entire buyer population** rather than an arbitrary first-40 subset.

Dropping the buyer cap is what exposed the ACID case.

---

# 4. Cross-Token Attribution: How Far Does the Evidence Go?

A separate question is whether dispatches observed on different tokens correspond to:

1. the same actor;
2. the same software/tool;
3. unrelated users of the same gateway.

Three tests were applied through:

`code/a7_cross_token_links.py`

Population:

**13 measured tokens / 75 gateway payments**.

---

## 4.1 Exact Amount Recurrence

The strongest cross-token link is the recurrence of:

**2.976815600 SOL**

It appears:

* once on a SAFFRON wallet on 2024-11-12;
* nine times on h2w6gm6jz wallets on 2024-12-13.

The events are separated by 31 days.

Because a swap output depends on its input, route, and execution price, exact recurrence across unrelated launches is treated as evidence of a repeated operation.

This is the strongest cross-token linkage observed in the corpus.

---

## 4.2 Shared Wallet

One wallet:

`GbYqi5jYdzNf6iKvfP1KWg7FyHhECMsZ5yYd7micig8h`

bought on both ACID and symx.

However, its gateway funding is dated:

**2025-01-23**

which is after both tokens existed.

Therefore the wallet creates a link between the launches as a **buyer**, but does not support the specific pre-launch funding mechanism for either token.

The evidence is consequently reported at that weaker strength.

---

## 4.3 Funding Sessions

Gateway payments separated by less than six hours were grouped into funding sessions.

Result:

**14 sessions**

None touches more than one token.

The observed dispatches are therefore not batched across multiple tokens within the tested six-hour session definition.

---

# 4.4 Attribution Boundary

The three tests support a deliberately narrow conclusion.

**Two of the thirteen token pairs are linked by hard on-chain evidence.**

That is stronger than:

> “These are unrelated users of a common gateway.”

But it is weaker than:

> “One person or organization executed all of them.”

The surviving alternative is a **shared tool or execution method**.

This interpretation is consistent with a separate finding in the repository: two operator clusters that share neither wallet nor token nevertheless exhibit the same byte-level execution fingerprint.

A repeated technique does not establish a repeated human operator.

To cross that boundary would require an artefact identifying the actor rather than merely the method.

No such artefact is produced by these three tests.

### Measured position

The evidence supports:

* dispatches are executed by single actors at the transaction level;
* at least two operations are linked by hard on-chain evidence;
* the identity behind those operations is **not established**.

---

# 5. The Downstream Structure: A Standing Wallet Fleet

The upstream analysis asks:

> **Who funded the buyer?**

The downstream analysis asks:

> **What happens to the buyer wallet after the launch?**

This distinction materially changes the interpretation.

Two models make different predictions.

### Disposable wallet

A disposable wallet:

1. receives funds;
2. buys;
3. sells;
4. disappears.

It does not subsequently fund newly created addresses.

### Fleet wallet

A fleet wallet:

1. is provisioned;
2. participates in a launch;
3. remains active;
4. funds newly created wallets;
5. those wallets can subsequently participate in further activity.

The discriminating measurement is therefore:

> How many later payment recipients were **born on receipt**?

An address whose first activity occurs within approximately one hour of receiving funds is treated as newly created rather than as an established account receiving a normal transfer.

---

## 5.1 The 14 Readable Gateway-Funded Wallets

`code/a8_wallet_horde.py` was applied to 14 readable gateway-funded wallets.

| Measurement                                    |        Result |
| ---------------------------------------------- | ------------: |
| Wallets that later funded ≥1 brand-new address |     **14/14** |
| New addresses spawned                          |       **129** |
| Median lifetime after trade                    |      3.9 days |
| Longest still active                           | **+356 days** |

The 14/14 result is notable because it is not merely a tendency across the measured wallets:

> **Every readable wallet in this population subsequently funded at least one newly created address.**

---

## 5.2 Examples of Long-Lived Wallets

One CHOCO buyer:

`4f6geAMUGzekQd3HemzHKWhJN9DiquNwTTtypPZckMQ5`

recorded:

* **1,880 transactions**
* activity continuing **356 days** after its trade
* funding of **150 addresses**
* **19 newly created addresses**
* including a transfer of **120.8 SOL** to an address created during the same week.

A SAFFRON wallet:

`291vRVW6QcL8Lj3F…`

funded:

* **47 addresses**
* **19 newly created**

These histories are inconsistent with a simple “buy once and disappear” wallet lifecycle.

---

# 5.3 The h2w6gm6jz Fleet

The nine wallets in the h2w6gm6jz burst exhibit coordinated downstream behaviour.

Six wallets with readable histories:

* received the same **2.976815600 SOL** amount;
* received it within the same 343-second burst;
* all stopped activity on **2024-12-17**;
* all did so approximately **3.9 days after the launch**;
* each subsequently spawned multiple new addresses.

| Wallet              | Last activity | Addresses funded | Newborn addresses |
| ------------------- | ------------- | ---------------: | ----------------: |
| `CDvfNWiamAR1B84G…` | 2024-12-17    |               21 |                 8 |
| `BmkuX6DaZUp9UCeR…` | 2024-12-17    |               19 |                 6 |
| `6QMshP9zwFXKbpLP…` | 2024-12-17    |               22 |                 7 |
| `5ibajLyeBmJhDfyZ…` | 2024-12-17    |               20 |                 6 |
| `AwQqcqdQQ3zydrtW…` | 2024-12-17    |               23 |                 9 |
| `3bBaA1MpQZuQpHjW…` | 2024-12-17    |               18 |                 7 |

Six wallets therefore show the same broad lifecycle:

**funded together → operate for ~3.9 days → stop together → leave behind similar numbers of child wallets**

The synchronization is itself an observable property.

It does not, by itself, identify the person or organization controlling them.

---

# 5.4 The Correction Forced by the Downstream Evidence

The upstream cross-token analysis originally concluded that operations were linked only in pairs because no common funder was found.

That reasoning was incomplete.

It looked only **upstream**.

A careful operator can deliberately prevent upstream ancestry from converging by provisioning each launch through a separate distributor.

Downstream, however, the structure can converge again.

The observed wallets:

* survive the launch;
* become funders themselves;
* create additional wallets;
* potentially produce descendants that participate in later launches.

This is materially different from the hypothesis:

> “Unrelated users happen to use the same gateway.”

The data instead support the existence of a **standing wallet population that can replenish itself downstream**.

But the identity boundary remains unchanged.

A large fleet of wallets can be:

* one operator running automated infrastructure;
* or a shared tool operated by multiple actors.

The fleet structure alone does not identify the controlling hand.

Therefore the attribution conclusion of §4 remains unchanged, while the **reasoning that led to it is corrected**: upstream non-convergence is not sufficient evidence of unrelated operators.

---

# 6. Full Scan Population

The final scan covers:

**3,963 distinct buyers across 13 tokens**

rather than a first-40 subset.

One additional token could not be read and is therefore classified as **unmeasurable**, not negative.

| Token        | Curve buyers | Fresh | Unreadable | Gateway-funded before launch |
| ------------ | -----------: | ----: | ---------: | ---------------------------: |
| `h2w6gm6jz`  |          223 |    67 |         90 |                        **9** |
| `ACID`       |          743 |   188 |          0 |                        **3** |
| `SAFFRON`    |          265 |    57 |        105 |                        **3** |
| `CHOCO`      |          289 |    78 |        114 |                        **2** |
| `QAMI`       |          266 |    59 |        107 |                        **2** |
| `sumiko`     |          290 |    96 |        116 |                        **2** |
| `BLT`        |          194 |    89 |          0 |                            0 |
| `LEXICON`    |           80 |    17 |         32 |                            0 |
| `MIKU`       |          804 |   173 |        322 |                            0 |
| `OPTIMUS`    |          246 |    53 |         99 |                            0 |
| `POLMRKTBOT` |          315 |    67 |        126 |                            0 |
| `RAO`        |          143 |    42 |         58 |                            0 |
| `symx`       |          105 |    31 |         42 |                            0 |
| `VISUALIZE`  |            — |     — |          — |  **Unmeasurable (HTTP 429)** |

### Observed result

**6 of 13 measured tokens carry the pattern.**

This is an observation about this deliberately selected measurement population.

It is **not** a market-wide prevalence estimate.

---

# 6.1 Why “Zero” Is Not Always Negative

The `unreadable` column determines how much confidence can be placed in a zero.

Examples:

* `MIKU`: **322 unreadable wallets**
* `OPTIMUS`: **99 unreadable wallets**
* `BLT`: **0 unreadable**
* `ACID`: **0 unreadable**

Therefore:

* a zero on BLT is a genuine measured negative;
* a positive result on ACID is fully observed;
* zeros on MIKU and OPTIMUS are weaker because a substantial fraction of wallet histories could not be inspected.

On the two tokens where the scan is complete, one is negative and one is positive.

Both observations remain informative.

Everywhere else, the correct statement is partly:

> **Not measured.**

---

# 6.2 Unmeasurable Is Not Negative

One token produced no measurement at all because its history could not be retrieved.

It is explicitly marked:

**unmeasurable**

rather than counted as a negative.

This distinction is methodological rather than cosmetic.

Collapsing:

**not measurable → negative**

previously produced an apparently clean:

**0/14**

result that was entirely false.

The incident is documented in `PITFALLS.md` P15.

---

# 7. Evidence Boundary

The current evidence supports the following narrow conclusions.

### Established

* A reproducible pre-launch funding pattern exists in the measured population.
* The pattern can involve direct gateway → wallet funding.
* It can also involve gateway → distributor → wallet funding.
* Fresh wallets, pre-launch funding, repeated conversion-output amounts, and chronology provide the core observable structure.
* The pattern appears on **6/13 measured tokens** in the scanned population.
* One case was initially hidden by an arbitrary 40-buyer scan limit.
* The downstream behaviour of the 14 readable gateway-funded wallets is consistent with a **standing wallet fleet**: all 14 subsequently funded at least one newly created address.
* At least two token pairs have hard on-chain links through recurring funding evidence.
* The identity behind those linked operations is **not established**.

### Not established

* The percentage of all pump.fun launches using the mechanism.
* That all observed dispatches belong to one operator.
* That the gateway service itself is involved in or aware of the activity.
* That identical execution implies identical human ownership.
* That absence of a shared upstream funder implies unrelated operators.
* That a shared gateway alone demonstrates coordination.
* That an observed wallet fleet identifies a specific person or organization.

---

# 8. Reproducibility

The core analysis is implemented in the repository through:

```text
code/a5_author_pattern.py
code/a6_gateway_chains.py
code/a1_null_model.py
code/a3_hub_origin.py
code/a7_cross_token_links.py
code/a8_wallet_horde.py
```

The full per-wallet dataset is:

```text
data/split/all_buyers_g2y.json
```

The separate question of whether the mechanism also appears on tokens that nobody traded is handled in:

```text
SPLIT_PHASE1.md §6
```

---

# Conclusion

The most defensible description of the pattern is not:

> “A known operator funds its bots through a swap service.”

The evidence does not establish that level of attribution.

The defensible description is narrower:

> **A reproducible pre-launch funding mechanism exists in which fresh buyer wallets can be provisioned through a common gateway, sometimes through an intermediate distributor, with repeated conversion-output amounts and strict pre-launch chronology. The resulting wallets can persist and themselves become funders of newly created addresses.**

The evidence links some operations across tokens, but does not identify the controlling actor.

The downstream fleet analysis strengthens the case for a **persistent provisioning system** while leaving the identity question open.

That distinction is the point of the investigation:

**the transaction structure is observable; the human behind it is not established.**
