# The 2024–2025 Split: What the Chain Shows, and What It Does Not

This chapter examines the **2024–2025 phase**, approximately October 2024 through February 2025, before the later creation-slot acquisition compressed the observable trading window.

During this period, the investigated mechanism involved capital being routed to fresh wallets, divided into near-identical amounts, and subsequently deployed in sequence.

The investigation covers:

* one confirmed reference case;
* a funding hub traced to its own genesis;
* two control populations;
* a null distribution for the detector;
* a target cohort whose original interpretation does **not** survive the corrected controls.

The detector is presented before its aggregate output.

That ordering is deliberate: an earlier draft examined the output first and consequently overstated what the evidence supported.

---

## Terminology and attribution boundary

The term **“Matrix”**, where used in this phase of the research, refers only to the coordinated infrastructure observed on-chain:

> addresses sharing funding origins and/or execution patterns.

It is a label for a **measured structure**, not for an actor.

Every address quoted in this chapter is a public technical identifier.

Reaching a swap service, bridge, exchange, or other gateway establishes a **routing fact**. It does not establish involvement by that service, company, employee, or person.

No service, company, or individual is attributed with participation, knowledge, intent, or wrongdoing by this analysis.

---

# 1. The Reference Case

One token, created on:

**2024-11-22 at 23:49 UTC**

has four first buyers sharing an unusual funding structure.

All four wallets were created in the **same transaction**, five days earlier:

**2024-11-17 at 23:55 UTC**

That transaction moved:

**12.0001 SOL**

as:

**4 × 3.000000000 SOL**

with one allocation to each wallet from a single hub address.

All four wallet histories were paged back to their first signature:

**4/4 genesis reached**

This matters because the observation is not merely the residue of a bounded historical search.

---

## 1.1 The distinguishing signature

Two properties carry most of the evidentiary weight:

1. the amount is **round to nine decimals**;
2. the same amount is distributed to four recipients **inside one transaction**.

A conversion-derived amount would normally contain a non-round output such as:

```text
1.393934883
```

whereas:

```text
3.000000000
```

is consistent with an intentionally specified transfer.

The combination is therefore more informative than either property alone:

> **round amount + shared transaction**

An identical amount without a shared transaction is weaker.

A shared transaction without an informative amount structure is also weaker.

This distinction is important for the detector design and is discussed further in `docs/PITFALLS.md`.

---

# 2. The Hub, Traced to Its Own Genesis

Earlier work could not establish where the hub itself obtained its funds.

The historical walk was bounded and returned only recent activity.

The failure mode was particularly dangerous because the pagination problem produced a plausible-looking result instead of an explicit error.

The analysis was therefore rerun without an artificial bound using:

```text id="d3r6jq"
code/a3_hub_origin.py
```

from two independent unbounded walks.

| Measurement                       |                   Result |
| --------------------------------- | -----------------------: |
| Signatures read                   |              **217,615** |
| Genesis reached                   |                  **Yes** |
| First operation                   | **2024-10-22, 0.01 SOL** |
| Purpose of first operation        |       Account activation |
| Real activity begins              |           **2024-11-06** |
| Fan-outs observed in first events |                    **4** |

The hub's observed behaviour is primarily a **fan-out/distribution pattern**.

It receives capital and then distributes it in the same general time interval, often splitting it into round amounts across several recipients.

Four examples from the first day of substantive activity:

|    Received | Paid out to | Amounts          |
| ----------: | ----------: | ---------------- |
|  1.5001 SOL | 8 addresses | 0.1 ×6, 0.2, 0.3 |
| 15.0001 SOL | 6 addresses | 1, 1, 2, 3, 3, 5 |
| 16.0001 SOL | 3 addresses | 2, 6, 8          |
| 15.0001 SOL | 3 addresses | 5, 5, 5          |

The account therefore exhibits a distribution shape rather than the behaviour of a wallet simply accumulating and trading a balance.

---

## 2.1 Upstream funding

Three upstream relationships were examined to genesis, while two could not be resolved completely.

| Address role           |   Signatures | Genesis         | Active since   |
| ---------------------- | -----------: | --------------- | -------------- |
| Principal funder       |      219,104 | Reached         | **2022-03-14** |
| First notable transfer |       14,798 | Reached         | **2023-01-01** |
| Secondary funder       |          109 | Reached         | **2024-11-06** |
| Commission recipient   | 400,000 read | **Not reached** | —              |
| Account activator      | 400,000 read | **Not reached** | —              |

The hub account itself is new relative to the opening of the studied period.

Its principal funder, however, is not new: that account dates to **2022**, and its genesis was reached.

This rules out the narrow interpretation that the entire upstream infrastructure was created specifically for this observation window.

The two unresolved histories are explicitly reported as:

> **out of reach**

rather than:

> **unfunded**

An address whose history exceeds the available pagination/search boundary has an **unmeasured origin**.

Likewise, a wallet that receives and redistributes funds is compatible with multiple roles, including:

* an operational distributor;
* a relay;
* another intermediary service.

The **shape of the activity is established**.

The **intent is not**.

---

# 3. The Detector and Its Null Distribution

The original split detector classified a token as positive when at least one of three criteria fired among its first 40 buyers.

### Criterion A — Same funding transaction

At least two buyers are funded inside the **same transaction**.

### Criterion B — Same amount within one hour

At least three buyers receive amounts equal within **1e-4 relative tolerance** inside a **one-hour window**.

### Criterion C — Shared private funder

At least two buyers share a **private funder**.

Known exchange and bridge terminals were excluded because a shared exchange hot wallet represents a common deposit endpoint rather than evidence of coordination.

---

## 3.1 The detector must be tested against a null

Before interpreting any criterion as evidence of coordination, it must be measured against wallets for which coordination is not known to exist.

The control population contained:

**136 early-buyer wallets**

from tokens selected using creation-slot information alone.

Funding was measured using the same code as the target population.

The wallets were pooled and randomly regrouped.

This destroys their original within-token co-occurrence.

Any resulting detector hit is therefore a coincidence under the construction of the null.

Across:

**5,000 random draws**

the firing rates were:

| Criterion                           | Group of 10 | Group of 20 | Group of 40 |
| ----------------------------------- | ----------: | ----------: | ----------: |
| **A — same funding transaction**    |      0.0000 |      0.0000 |      0.0000 |
| **B — same amount within one hour** |      0.0000 |      0.0000 |      0.0000 |
| **C — shared private funder**       |       0.151 |       0.461 |   **0.889** |

Restricting the analysis to the 70 wallets whose genesis was actually reached does not rescue criterion C:

> **C fires on 99.5% of random draws.**

---

## 3.2 Criterion C is retired

Criterion C behaves like a birthday-collision problem.

As the number of wallets in a group increases, the number of possible pairwise relationships increases, while the funder population remains finite.

The result is that:

> **more wallets → more apparent shared-funder relationships**

By a group size of 40, criterion C fires on **88.9%** of random groups.

At that point, C is effectively becoming the verdict itself.

It therefore cannot be included in a disjunctive detector:

```text
A OR B OR C
```

if C is already positive for most random groups.

Criteria A and B, by contrast, fired:

**0 times in 5,000 draws at every tested group size.**

They require coincidence in both identity and timing and are consequently much narrower criteria.

---

## 3.3 Recount after retiring C

Every token was therefore recounted using:

```text
A OR B
```

only.

The corrected recount is implemented in:

```text id="v3tdqf"
code/a2_recount.py
```

The complete methodological episode is documented as card 13 in `docs/PITFALLS.md`.

---

# 4. Two Control Groups — and Why One Was Not Enough

A major lesson from this phase is that a single control group can answer the wrong question very precisely.

Two control populations were therefore constructed.

---

## 4.1 Control Group 1 — Matched on Creation Slot

**n = 9**

Each control token was selected within approximately **±200 slots** of a target.

Selection depended only on creation-slot information and market outcome, with the rule fixed before funding was measured.

Bonding-curve pagination reached genesis for all:

**171 harvested mints**

This control was useful but incomplete.

The problem was that all target tokens had graduated, while all tokens in this first control group were dead.

That leaves a major confound:

> **success**

A difference between the groups can arise because one group contains successful tokens and the other does not.

Sophisticated buyers may naturally cluster around tokens that subsequently perform well.

That alone can create funding structures that look coordinated.

---

## 4.2 Control Group 2 — Matched on Outcome

**n = 12**

The second control group consisted of graduated pump.fun tokens from the same period that the author did **not** trade.

They were selected systematically across the full capitalization range of the reachable population:

```text id="s0rq1w"
data/trace_gradues/t0_gradues.json
```

The retention rule was fixed before measurement.

This is the comparison that carries the substantive weight.

The first control group remains in the document because it demonstrates how strongly the outcome confound can alter the apparent result.

---

## 4.3 Important limitation of the graduated controls

The reachable pool itself is survivor-selected because it comes from a capitalization-ranked listing.

The graduated controls consequently performed, on average, better than the target population.

That selection runs against the hypothesis being tested.

This does not make the controls unbiased in an absolute sense.

It means the control construction does not simply reproduce the original target selection and therefore provides a more informative comparison than the dead-token controls.

---

# 5. The Target Cohort — and the Claim It Cannot Support

The target cohort consists of tokens that the author traded and for which screenshots were retained.

That introduces outcome selection twice:

1. the token had to reach a level worth trading;
2. the trade had to be successful enough to be documented.

The selection-bias analysis is implemented in:

```text id="v7yscp"
code/a4_selection_bias.py
```

The resulting graduation rates are:

| Population                                          |              Graduated |
| --------------------------------------------------- | ---------------------: |
| Era-wide estimate across five neutral term families | **32 / 2,740 = 1.17%** |
| Slot-matched creation windows                       |    **6 / 171 = 3.51%** |
| Target cohort                                       |     **11 / 11 = 100%** |
| Approximate probability under random sampling       |         **~5 × 10⁻²²** |

The target cohort is therefore highly selected.

---

## 5.1 Mint-resolution limitations

Mint resolution is uneven and is explicitly labelled.

* **8** tokens were resolved directly from a capture.
* **2** were resolved using symbol **and** date.
* **1** was resolved using symbol alone.
* **6 symbols** could not be resolved to a mint with sufficient confidence.

The unresolved symbols are retained as:

> **AMBIGUOUS**

rather than being guessed.

One fragment resolved to a mint sharing its first nine characters with a pool created on the capture date.

The differences are consistent with OCR, but the identification is retained only at that level of confidence.

The principle is:

> **uncertainty is preserved rather than silently converted into certainty.**

---

## 5.2 What the cohort can answer

The cohort can support two limited questions.

### Question 1

Among graduated tokens from the same period, do the tokens traded by the author carry the signature more often than graduated tokens the author did not trade?

### Question 2

Is the signature actually observable in the cases from which the investigation originated?

Those are presence/comparison questions.

---

## 5.3 What the cohort cannot answer

The cohort cannot establish prevalence.

A statement such as:

> “X% of pump.fun tokens carry the signature”

is not derivable from a population selected on outcome.

The cohort also cannot establish profitability.

The captures are selected winning trades, while losing trades are not represented in the screenshot dossier.

---

# 6. Result: The Signature Does Not Survive Its Own Control Group

Against dead tokens, the original split signature strongly separated the traded tokens from the controls:

**p = 0.0007**

Against graduated tokens from the same period, the difference disappears:

**p = 0.44**

The apparent effect was therefore substantially explained by the difference between:

> **a token that went somewhere**

and:

> **a token that did not.**

It was not demonstrated to be a difference between:

> **a coordinated launch**

and:

> **an ordinary successful launch.**

---

## 6.1 The four-stage correction

Each comparison removes one source of the original apparent effect.

### 1. Original verdict vs dead controls

**12/14 vs 1/9**

**p = 0.0007**

This was the number the project could have published under the original protocol.

However, it depends on criterion C, which fires on **88.9% of random groups**.

---

### 2. A or B only vs dead controls

**5/14 vs 0/9**

**p = 0.060**

Removing criterion C eliminates most of the apparent effect and removes conventional statistical significance.

---

### 3. Original verdict vs graduated controls

**12/14 vs 8/12**

**p = 0.2478**

Once the outcome is held approximately constant, the original detector still fires frequently among untraded graduated tokens.

This demonstrates that criterion C was not specifically detecting coordination.

It was detecting a property strongly associated with having a successful token and a sufficiently active buyer population.

---

### 4. A or B only vs graduated controls

**5/14 vs 3/12**

**p = 0.4371**

Both corrections are now applied:

* the weak null criterion C has been retired;
* the control group is matched on graduation/outcome.

No statistically distinguishable effect remains in this small measured sample.

---

# 6.2 Criterion A as the strongest individual test

Criterion A is particularly informative because it fired:

**0 times in 5,000 null draws.**

It requires two or more early buyers to be funded within the **same transaction**.

It appears on:

**1/14 targets**

and:

**0/12 graduated controls**

with:

**p = 0.5385**

The appropriate interpretation is therefore:

> **One observed target case, not an estimated rate.**

The null result does not invalidate the reference case.

It limits what can be inferred from that case.

---

# 6.3 What remains established

The reference case is real:

* four wallets were born in one transaction;
* all four received identical round amounts;
* the funding occurred five days before the token;
* genesis was reached for all four wallets.

A second instance was also identified among the target cases.

The distribution hub is real.

Its fan-out structure is real.

Its principal upstream funder is traceable to an account active since 2022.

These are observations and remain valid.

---

# 6.4 What does not survive

The broader claim that these observations were evidence that:

> **the tokens traded by the author were systematically launched through split-funded wallets**

does not survive comparison with graduated tokens that the author did not trade.

The corrected evidence instead indicates that coordinated-looking funding structures can also occur among successful graduated tokens outside the target trading cohort.

That is a materially narrower conclusion.

---

# 7. Final Evidence Boundary

The phase-1 analysis supports the following:

### Established

* A split-funding mechanism demonstrably existed in at least two measured cases.
* One reference case contains four wallets created in the same transaction and funded with four identical round amounts.
* The relevant wallet histories were traced to genesis.
* The hub exhibits a measurable fan-out/distribution structure.
* The hub's principal upstream funder dates to 2022.
* The original shared-private-funder criterion produces extremely high false-positive rates under the null and must not be used as a coordination detector.
* Same-transaction funding and tightly synchronized equal-amount funding are substantially rarer under the tested null.
* The target cohort is heavily selected on outcome.
* Once outcome is controlled and the weak criterion is removed, the small target/control comparison does not establish a systematic difference.

### Not established

This analysis does **not** establish:

* a market-wide prevalence rate;
* that the phase-1 launch population was systematically coordinated;
* that all target tokens shared one operator;
* that the observed hub belonged to a particular person or organization;
* that a shared funding origin establishes common ownership;
* that the observed pattern implies malicious intent;
* that the historical trading screenshots measure overall profitability;
* that the absence of a shared upstream funder proves that operators were unrelated.

---

# 8. The Corrected Conclusion

The strongest defensible conclusion from phase 1 is deliberately narrow:

> **A reproducible split-funding mechanism existed on Solana during the 2024–2025 measurement window and can be demonstrated at transaction level in multiple cases. However, the corrected detector and outcome-matched controls do not establish that this mechanism was systematically characteristic of the tokens traded by the author.**

The investigation therefore separates two claims that an earlier version had conflated:

```text id="9ppgdy"
The mechanism existed
        ≠
The mechanism was systematically responsible for the target cohort
```

The first survives.

The second does not.

That distinction is the central result of this phase.

---

# 9. Reproducing This Chapter

All four analyses read only committed files under `data/`.

No network access or API key is required for reproduction of the published outputs.

```bash id="d2oy2h"
python3 code/a1_null_model.py      # null distribution of the three criteria
python3 code/a2_recount.py         # recount under A and B + Fisher exact tests
python3 code/a3_hub_origin.py      # hub genesis and upstream reconstruction
python3 code/a4_selection_bias.py  # target-cohort selection analysis
```

The historical walks that generated the committed data require a Helius key and are listed in:

```text id="w3w1pd"
code/run_all.py --with-net
```

The reproducibility boundary is therefore explicit:

> **The published analysis is reproducible from committed data; regenerating the underlying historical chain extracts requires network access and the configured RPC credentials.**
