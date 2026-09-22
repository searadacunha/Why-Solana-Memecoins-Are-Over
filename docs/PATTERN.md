# The Gateway Dispatch: A Launch-Funding Pattern

> **A transaction-level reconstruction of a pre-launch funding mechanism on Solana, and the detector built to identify it.**

This chapter documents a recurring funding pattern observed on Solana during the **2024–2025** window.

The investigation has four objectives:

1. define the mechanism using observable on-chain properties;
2. reconstruct it through transaction-level examples;
3. describe the detector used to identify it automatically;
4. determine how far the evidence supports cross-token linkage and attribution.

Throughout the analysis, four distinctions are maintained explicitly:

* **presence** is not **frequency**;
* **technical linkage** is not **identity**;
* **measurement** is not **interpretation**;
* **unmeasurable** is not **negative**.

---

## Scope and attribution boundary

This analysis is **not a prevalence estimate**.

The tokens examined in this chapter were selected from an observed outcome and therefore cannot support a statement such as:

> “X% of launches use this mechanism.”

The evidence establishes **presence**, not market-wide **frequency**.

See `SPLIT_PHASE1.md` §5 and `code/a4_selection_bias.py` for the corresponding selection-bias analysis.

The same principle applies to attribution. A shared gateway, repeated execution pattern, or linked wallet structure does not by itself establish common human ownership.

---

# 1. The Mechanism

The observed pattern is defined by four properties occurring together:

| # | Observable property                                                                                                         | Why it matters                                                                                                                                     |
| - | --------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 | The buyer wallet is **fresh** and was created shortly before the purchase                                                   | A newly created wallet may have been provisioned specifically for the launch rather than representing an established participant.                  |
| 2 | The wallet is funded **directly by the swap gateway**                                                                       | This is the observable entry point onto Solana and the point at which upstream provenance becomes more difficult to trace.                         |
| 3 | The funding amount is a **conversion output**, typically with nine significant decimals rather than a round transfer amount | For example, `2.976815600` is consistent with a swap-derived output, whereas `3.000000000` is consistent with an intentionally specified transfer. |
| 4 | The funding arrives **before the token exists**                                                                             | A payment occurring after token creation cannot have funded the initial purchase.                                                                  |

The third and fourth properties are particularly discriminating.

A period of high activity can naturally generate multiple wallets sharing a funder. It is more specific to observe:

> **multiple fresh wallets receiving the same nine-decimal amount from the same gateway within a short interval, before the target token exists.**

The mechanism is therefore not defined by a single heuristic. It is the combination of wallet freshness, funding provenance, amount structure, and chronology.

---

## 1.1 Gateway Attribution

The gateway address is represented in this document as:

**G2Y**

Full address:

```text
G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t
```

The source material reports that this address has been publicly attributed to a hot wallet of **ChangeNOW** by two independent public sources:

* a 2025 research study in which the author reports observing test funds arrive there;
* an earlier public attribution.

Neither source is presented as an official exchange label.

The identification is therefore treated as:

> **Publicly attributed, not officially confirmed.**

Reaching the gateway establishes a **routing observation**.

It does **not** establish:

* what the service knew;
* what the service intended;
* what the service permitted or prohibited;
* involvement by the service;
* involvement by any employee or other person.

No wrongdoing is attributed to the service, company, or any individual.

---

# 1.2 Two Layers, One Hop Apart

The gateway does not always fund the final buyer wallets directly.

In some cases, it first funds an intermediate distributor, which subsequently distributes capital in round amounts:

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

This distinction is important for detection.

A detector that requires the **conversion-output signature to appear directly at the buyer-wallet layer** will miss cases routed through a distributor.

The first implementation did exactly that: it returned zero on all 15 tested tokens, including the reference case.

The resulting detector rule is therefore:

> **Use the amount structure as evidence when present; do not require it as a hard criterion.**

This prevents a particular implementation detail from becoming a false-negative generator.

---

# 2. Transaction-Level Examples

The following cases illustrate different manifestations of the mechanism.

They are **forensic examples**, not a statistical sample.

Their purpose is to demonstrate how the pattern appears in transaction history and why individual heuristics are insufficient on their own.

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

The sequence contains four simultaneous characteristics:

* nine fresh wallets;
* an identical nine-decimal funding amount;
* a common gateway;
* a 343-second interval from the first to the last funding;
* all funding occurring hours before token creation.

The repeated amount is treated as a conversion output rather than an arbitrary manually specified transfer.

---

## 2.2 The Same Conversion Output on Another Token

The exact amount:

**2.976815600 SOL**

also appears on a fresh SAFFRON wallet:

```text
wbzkg9ftnVEMzeCL6wW8bpNTPDQWhBBnKo3JWJe3wh5
```

Timestamp:

**2024-11-12 13:16:45**

This occurs 31 days before the h2w6gm6jz burst and originates from the same gateway.

A swap output depends on input size, route, and execution price.

The recurrence of the exact nine-decimal amount across two separate launches is therefore treated as evidence of a repeated operation rather than as a repeated coincidence.

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

The problem was not absence of the pattern.

The scan stopped after the first **40 buyers**, while ACID had **743 buyers**. The relevant wallets appeared later in the curve.

The buyer cap therefore produced a false negative.

The final scanner consequently walks the **complete buyer population** rather than assuming that the first 40 buyers are representative.

---

## 2.4 SAFFRON — One Wallet Funded Four Times

Token creation:

**2024-11-12 22:54**

Three fresh gateway-funded wallets were identified.

One wallet,

```text
wbzkg9ftnVEMzeCL…
```

received four separate payments during the preceding nine hours:

| Time     |          Amount |
| -------- | --------------: |
| 13:16:45 | 2.976815600 SOL |
| 13:53:56 | 2.380415590 SOL |
| 14:16:27 | 9.894826000 SOL |
| 21:27:20 | 7.778694250 SOL |

Two additional wallets received:

* **1.982815600 SOL**
* **8.624207890 SOL**

on the preceding day.

The amounts vary, but the structural sequence remains:

```text
fresh wallet → gateway funding → launch
```

Repeated top-ups into the same fresh wallet are therefore treated as a variant of the mechanism. Identical amounts are not required.

---

## 2.5 QAMI — Two Wallets the Day Before

Token creation:

**2024-12-31 23:41**

Two fresh wallets received gateway funding the previous day:

### Wallet 1

```text
6nGLeqP1BW1MWrMsC7EYA57iei1V5XfpEW7YqdgFNA4K
```

* **4.949823400 SOL**
* **2024-12-30 17:31:45**

### Wallet 2

```text
E2wJyPwoJAydxYpvKSv1uRSS9GdEzX8gpfqeWsaVHcab
```

* **0.481875600 SOL**
* **2024-12-31 17:19:21**

The second payment occurs approximately six hours before token creation.

---

## 2.6 sumiko — Two Wallets Seven Minutes Apart

Token creation:

**2024-12-26 13:25**

Two fresh wallets received gateway funding shortly before creation:

* `AJq5My8GFG6Jo7Pq…`

  * **1.446086 SOL**
  * **12:55:43**

* `FYG2cyAmhKGyRnH5…`

  * **0.739785 SOL**
  * **13:02:00**

The first payment occurred 29 minutes before the token existed.

Both wallets are fresh and both are gateway-funded.

---

## 2.7 CHOCO — Both Layers on One Token

Token creation:

**2024-10-10 13:35**

Two fresh wallets were funded directly by the gateway:

* `Edx7xy6RG8nchSE833xJNGjNBL4QdZV587Zk8GZ3Kpho`

  * **1.207495600 SOL**
  * **09:24:43**

* `4f6geAMUGzekQd3HemzHKWhJN9DiquNwTTtypPZckMQ5`

  * **2.307396470 SOL**
  * three days earlier

The same token also contains the **distributor layer**.

A distributor created that morning was funded by the gateway at **13:26** and, five minutes later, distributed:

**20 × 0.300000000 SOL**

to 20 fresh wallets in a single transaction.

The distributor was never used again and has only 30 signatures in its lifetime.

The token therefore contains both observed forms:

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

The core components are standard-library based and the offline analysis requires no API key.

| Script                      | Function                                                                                                                                        |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `code/a5_author_pattern.py` | Scans buyer funding for fresh wallets receiving near-identical amounts in a burst; sweeps thresholds instead of selecting one arbitrary cutoff. |
| `code/a6_gateway_chains.py` | Reconstructs dated gateway → distributor → wallet chains while enforcing chronology.                                                            |
| `code/a1_null_model.py`     | Measures how frequently individual criteria fire on random wallets.                                                                             |
| `code/a3_hub_origin.py`     | Traces a distributor toward its genesis and records whether genesis is reached.                                                                 |

Primary commands:

```bash
python3 code/a5_author_pattern.py
python3 code/a6_gateway_chains.py
```

---

# 3.1 Four Requirements for a Reliable Detector

## 1. Reach genesis — or explicitly report that you did not

`getSignaturesForAddress` retrieves history backwards in pages of 1,000.

If the walk is arbitrarily truncated, the scanner may inspect only recent activity.

That creates a dangerous false negative:

> “No funding found”

when the actual result is:

> “Funding not found within the portion of history inspected.”

Because funding often occurs near a wallet's first transactions, every negative result must carry the historical-search scope.

---

## 2. Make transport failures explicit

A client that returns `None` on error, followed by code such as:

```python
result = response or []
```

can silently transform:

```text
API failure
    ↓
empty dataset
    ↓
false negative
```

This happened in the project.

A wrong hostname produced:

**0/14 tokens**

instead of an explicit error.

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

A detector that fires on most random groups is not discriminating enough to establish the target phenomenon.

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

Chronology is therefore a **hard validity condition**, not an optional annotation.

---

# 3.2 Making a Full-Curve Scan Tractable

Scanning every buyer is more expensive than scanning only the first few buyers.

Wallet freshness provides an early stopping condition.

A wallet with activity older than:

```text
creation time − N days
```

is no longer eligible to be classified as fresh.

The scanner can therefore walk backward through the wallet's history and stop once it encounters activity older than the freshness window.

This provides two benefits:

* old, high-activity wallets can be rejected quickly;
* the scan can cover the **entire buyer population** rather than an arbitrary first-40 subset.

Removing the buyer cap is what exposed the ACID case.

---

# 4. Cross-Token Attribution: How Far Does the Evidence Go?

A separate question is whether dispatches observed on different tokens correspond to:

1. the same actor;
2. the same software or execution tool;
3. unrelated users of the same gateway.

Three tests were applied through:

```text
code/a7_cross_token_links.py
```

Population:

**13 measured tokens / 75 gateway payments**

---

## 4.1 Exact Amount Recurrence

The strongest cross-token linkage observed is the recurrence of:

**2.976815600 SOL**

It appears:

* once on a SAFFRON wallet on **2024-11-12**;
* nine times on h2w6gm6jz wallets on **2024-12-13**.

The events are separated by 31 days.

Because a swap output depends on input size, route, and execution price, exact recurrence across separate launches is treated as evidence of a repeated operation.

This is the strongest cross-token linkage observed in the measured corpus.

It does **not**, by itself, identify the operator.

---

## 4.2 Shared Wallet

One wallet:

```text
GbYqi5jYdzNf6iKvfP1KWg7FyHhECMsZ5yYd7micig8h
```

bought on both ACID and symx.

However, its gateway funding is dated:

**2025-01-23**

which is after both tokens existed.

The wallet therefore establishes a link between the launches as a **buyer**, but does not support the specific pre-launch funding mechanism for either token.

The evidence is consequently reported at that weaker level.

---

## 4.3 Funding Sessions

Gateway payments separated by less than six hours were grouped into funding sessions.

Result:

**14 sessions**

None touches more than one token.

Under this six-hour session definition, the observed dispatches are therefore not batched across multiple tokens.

---

## 4.4 Attribution Boundary

The three tests support a deliberately narrow conclusion:

> **Two of the thirteen token pairs are linked by hard on-chain evidence.**

That is stronger than:

> “These are unrelated users of a common gateway.”

But it is weaker than:

> “One person or organization executed all of them.”

A remaining explanation is a **shared tool or execution method**.

This interpretation is consistent with a separate repository finding: two operator clusters that share neither wallet nor token nevertheless exhibit the same byte-level execution fingerprint.

A repeated technique does not establish a repeated human operator.

Crossing that boundary would require an artefact identifying the actor rather than merely the method.

No such artefact is produced by these tests.

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

Two wallet-lifecycle models make different predictions.

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

> **How many later payment recipients were born on receipt?**

An address whose first activity occurs within approximately one hour of receiving funds is treated as newly created rather than as an established account receiving an ordinary transfer.

---

# 5.1 The 14 Readable Gateway-Funded Wallets

`code/a8_wallet_horde.py` was applied to 14 readable gateway-funded wallets.

| Measurement                                    |        Result |
| ---------------------------------------------- | ------------: |
| Wallets that later funded ≥1 brand-new address |     **14/14** |
| New addresses spawned                          |       **129** |
| Median lifetime after trade                    |  **3.9 days** |
| Longest still active                           | **+356 days** |

The key observation is:

> **Every readable wallet in this population subsequently funded at least one newly created address.**

This is not merely a tendency within the measured wallets; it is universal within this specific 14-wallet population.

---

# 5.2 Examples of Long-Lived Wallets

One CHOCO buyer:

```text
4f6geAMUGzekQd3HemzHKWhJN9DiquNwTTtypPZckMQ5
```

recorded:

* **1,880 transactions**;
* activity continuing **356 days** after its trade;
* funding of **150 addresses**;
* **19 newly created addresses**;
* including a transfer of **120.8 SOL** to an address created during the same week.

A SAFFRON wallet:

```text
291vRVW6QcL8Lj3F…
```

funded:

* **47 addresses**;
* **19 newly created addresses**.

These histories are inconsistent with a simple “buy once and disappear” lifecycle.

They are compatible with a longer-lived provisioning role.

---

# 5.3 The h2w6gm6jz Fleet

The nine wallets in the h2w6gm6jz burst exhibit coordinated downstream behaviour.

Six wallets with readable histories:

* received the same **2.976815600 SOL** amount;
* received it within the same 343-second burst;
* all stopped activity on **2024-12-17**;
* all stopped approximately **3.9 days after the launch**;
* each subsequently spawned multiple new addresses.

| Wallet                | Last activity | Addresses funded | Newborn addresses |
| --------------------- | ------------- | ---------------: | ----------------: |
| `CDvfNWiamAR1B84G…`   | 2024-12-17    |               21 |                 8 |
| `BmkuX6DaZUp9UCeR…`   | 2024-12-17    |               19 |                 6 |
| `6QMshKAC7zu5HfMA22…` | 2024-12-17    |               22 |                 7 |
| `5ibajLyeBmJhDfyZ…`   | 2024-12-17    |               20 |                 6 |
| `AwQqcqdQQ3zydrtW…`   | 2024-12-17    |               23 |                 9 |
| `3bBaA1MpQZuQpHjW…`   | 2024-12-17    |               18 |                 7 |

The six wallets therefore share the same broad lifecycle:

```text
funded together
      ↓
operate for ~3.9 days
      ↓
stop together
      ↓
leave behind similar numbers of child wallets
```

The synchronization is itself observable.

It does **not**, by itself, identify the person or organization controlling the wallets.

---

# 5.4 The Correction Forced by the Downstream Evidence

The upstream cross-token analysis originally concluded that operations were linked only in pairs because no common funder was found.

That reasoning was incomplete.

It examined only the **upstream ancestry**.

An operator can prevent upstream convergence by provisioning different launches through separate distributors.

Downstream, however, the structure can converge again.

The observed wallets:

* survive the launch;
* become funders themselves;
* create additional wallets;
* potentially produce descendants that participate in later launches.

This is materially different from the simple hypothesis:

> “Unrelated users happen to use the same gateway.”

The data instead support the existence of a:

> **standing wallet population capable of downstream replenishment.**

The identity boundary nevertheless remains unchanged.

A large wallet fleet can represent:

* one operator running automated infrastructure;
* a shared tool operated by multiple actors;
* or another provisioning architecture not resolved by the available evidence.

The fleet structure alone cannot identify the controlling party.

Therefore, the attribution conclusion of §4 remains unchanged, while the reasoning leading to it is corrected:

> **Upstream non-convergence is not sufficient evidence that operators are unrelated.**

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

This is an observation about the deliberately selected measurement population.

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
* the positive result on ACID is fully observed;
* zeros on MIKU and OPTIMUS are weaker because a substantial fraction of wallet histories could not be inspected.

On the two tokens where the scan is complete, one is negative and one is positive.

Both observations remain informative.

Elsewhere, the correct interpretation is partly:

> **Not measured.**

---

# 6.2 Unmeasurable Is Not Negative

One token produced no measurement because its history could not be retrieved.

It is explicitly marked:

**unmeasurable**

rather than counted as a negative.

This distinction is methodological, not cosmetic.

Collapsing:

```text
not measurable → negative
```

can produce an apparently clean:

```text
0/14
```

result that is entirely false.

The incident is documented in `PITFALLS.md` P15.

---

# 7. Evidence Boundary

The current evidence supports the following conclusions.

## Established

* A reproducible pre-launch funding pattern exists in the measured population.
* The pattern can involve direct **gateway → wallet** funding.
* It can also involve **gateway → distributor → wallet** funding.
* Fresh wallets, pre-launch funding, repeated conversion-output amounts, and chronology form the core observable structure.
* The pattern appears on **6/13 measured tokens** in the scanned population.
* One case was initially hidden by an arbitrary 40-buyer scan limit.
* The downstream behaviour of the 14 readable gateway-funded wallets is consistent with a **standing wallet fleet**: all 14 subsequently funded at least one newly created address.
* At least two token pairs have hard on-chain links through recurring funding evidence.
* The identity behind those linked operations is **not established**.

## Not established

* The percentage of all pump.fun launches using the mechanism.
* That all observed dispatches belong to one operator.
* That the gateway service itself is involved in or aware of the activity.
* That identical execution implies identical human ownership.
* That absence of a shared upstream funder implies unrelated operators.
* That a shared gateway alone demonstrates coordination.
* That an observed wallet fleet identifies a specific person or organization.

---

# 8. Reproducibility

The core analysis is implemented through:

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

The most defensible description of the pattern is **not**:

> “A known operator funds its bots through a swap service.”

The evidence does not establish that level of attribution.

The defensible description is narrower:

> **A reproducible pre-launch funding mechanism exists in which fresh buyer wallets can be provisioned through a common gateway, sometimes through an intermediate distributor, with repeated conversion-output amounts and strict pre-launch chronology. The resulting wallets can persist and themselves become funders of newly created addresses.**

The evidence links some operations across tokens, but does not identify the controlling actor.

The downstream fleet analysis strengthens the case for a **persistent provisioning system** while leaving the identity question open.

That distinction is the central methodological point:

> **The transaction structure is observable; the human behind it is not established.**
