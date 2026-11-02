# Same-amount gateway bursts: what the recipients did next

Plan committed before reading: [../../docs/PLAN_gateway_bursts.md](../../docs/PLAN_gateway_bursts.md). Figures:
[results.json](results.json). The published case's day is not in the sample, and the case is not in these rates.

**Most same-amount bursts of at least 9 payouts behave as linked groups, far above what the same wallets show when grouped by
chance within a day. About 1 in 19 shows the strict signature of the published case. This says nothing about who controls them.**

## Result

296 bursts in the population (4,205 payouts); 150 sampled; 1,638 members read, 1,602 distinct wallets, none with an empty history; 49 days;
16,020 credits. An independent review found that a wallet credited twice in a burst counted twice for O3; fixed, and the counts did not move.

| Outcome, among up to 12 members of a burst | Bursts | Share | Wilson 95 % | Bootstrap by day 95 % | Permuted, mean | Permuted, 95th pct | p |
|---|---:|---:|---|---|---:|---:|---:|
| **O1** at least 5 buy the same mint, same raw amount, within 10 slots | 8 | 5.3 % | 2.7 to 10.2 | 1.2 to 11.3 | 0.92 | 2 | 0.001 |
| **O2** at least 5 buy the same mint within 72 h | 70 | 46.7 % | 38.9 to 54.6 | 35.6 to 57.0 | 19.4 | 23 | 0.001 |
| **O3** at least 5 send at least 0.1 SOL to the same wallet within 7 days | 124 | 82.7 % | 75.8 to 87.9 | 75.4 to 88.6 | 48.6 | 55 | 0.001 |

The three tests are compared to 0.05 / 3. With 1,000 permutations, 0.001 is the smallest p they can give.

Controls: the 15 wallets of the published case meet O1, O2 and O3. Twelve members drawn from 12 different bursts, 200 times, met
none of the three, 0 of 200 each. The plan asked for 12 bursts of one day; the sample rarely has that many, so they come from the
whole sample (amendment in `DECISIONS.md`).

## What it means, and how far it goes

- **Same amounts usually mean the same activity.** The frozen 2024 study showed that about 96 % of timestamp-defined groups come
  from recurring amounts by chance. That is a statement about timing. It is compatible with this one: the timing of a burst adds
  little, while the recipients of an amount are linked anyway. It does not follow that those groups were unrelated wallets, which
  a reader of that result could have inferred.
- **The strict signature is not unique.** O1 appears on 8 sampled bursts in four amounts (1.9828156, 1.98701297, 2.9768156 and
  1.0 SOL), from October 2024 to January 2025. Among the 9 sampled bursts at 2.9768156 SOL, 1 meets O1. So this amount does not
  define an operation, and the exact behaviour of the published case is a recurring pattern, not a one-off.
- **O3 is not a measure of one owner.** Post hoc, no destination dominates: 94 distinct wallets across the 124 bursts, at most 4
  bursts each. That rules out one universal service as the explanation. A platform with many clients, each with its own wallet,
  would look the same.

## Limits

- Payouts under 1 SOL are not in the data, and bursts of under 9 are outside this test.
- 12 members is a lower bound for a large burst. 82 of 1,638 members filled their first page of 100 transactions, so their later
  activity was not read. Both push the rates down.
- Bursts of one day can share an operator, which raises the permuted mean as well and makes the test conservative on that side.
  Hour of day is not preserved by the permutation: hot tokens at the same hour can inflate O2. O1 is much less exposed to that.
- The sample is from the collected days of the frozen study, picked there by another rule.
- This does not show that a trade was profitable, or that any wallet belongs to a given person.
