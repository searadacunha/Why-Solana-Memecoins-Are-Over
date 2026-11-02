# Plan: do same-amount gateway bursts behave as one group?

Written and committed before any burst outside the published case is read. Changing anything here after
results is an amendment in `forensics_v2/DECISIONS.md`, dated, with the reason.

## Why

The published case (h2w6gm6jz) was selected on its result, so it cannot say how common it is. The frozen
`historical_edge_2024` study showed that about 96 % of timestamp-defined groups are what recurring amounts
produce by chance. That study did not look at what the recipients did next. This test does.

## Population

G2Y payouts of at least 1 SOL on the 49 collected days (`historical_edge_2024/data/payouts.json`, read only,
91,789 rows). A **burst** is a maximal run of payouts of the exact same lamport amount with consecutive gaps of
at most 600 s, with at least 9 payouts, the published case's size. The case's own day, 2024-12-13, is not in the
49 days; it is never added to the rates below.

## Sample

150 bursts drawn uniformly, `random.Random(20261102)`, from the population sorted by first payout time. For each,
the first 12 members in time order. Each member's first page of history: at most 100 transactions, oldest first,
10 credits. Ceiling: 150 x 12 x 10 = 18,000 credits. If it runs out, what was read is reported as such.

## Outcomes, per burst, among the members read

- **O1, same-size buy:** at least 5 members buy the same mint with the identical raw token amount, within 72 h of
  their credit and within 10 slots of each other.
- **O2, same mint:** at least 5 members buy the same mint within 72 h of their credit.
- **O3, common destination:** at least 5 members each send at least 0.1 SOL to the same wallet within 7 days, by
  a direct instruction, excluding services in `service_attributions.json` and trade counterparties.

Freshness (the credit is the member's first transaction) is recorded, and the rates are also reported for bursts
with at least 5 fresh members. That split is secondary.

## Null

Member labels permuted within each UTC day, keeping burst sizes, 1,000 permutations, seed 20261102. Histories
already read are reused, so this costs no credit. It answers: how many bursts would meet the outcome if the same
wallets had been grouped by chance on the same day?

## Statistics

Three outcomes, three tests: one-sided permutation p, compared to 0.05 / 3. Proportions with Wilson intervals, and
a bootstrap by day for dependence between bursts of one day. No test of size or of any other split is promoted.

## Controls before reading the sample

- **Positive:** the 15 wallets of the published case, run through the same code, must meet O1, O2 and O3. If not,
  the detector is broken and no rate is read.
- **Negative:** the same code on 12 members drawn from 12 different bursts of one day, repeated 200 times. O1 must
  be rare there, or the outcome is not selective.

## What this will not show

Who controls any wallet. Why they coordinate. Whether a trade was profitable. The first 100 transactions of a wallet
are not its whole history, payouts under 1 SOL are not in the data, and 12 members are a lower bound for a large burst.
