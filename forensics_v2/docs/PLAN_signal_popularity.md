# Plan: does the signal survive a match on the token's popularity?

Written and committed before this reading. Results stay in the private folder; this page has no figure from them.

`PLAN_signal_matched.md` matched on date, curve level and token age, and left a token's popularity unmatched, its main remaining bias. A popular launch draws more large buyers, so more chances of one funded through the gateway. This plan has two parts, and only the second is new evidence.

## Part 1: the same 40 pairs, descriptive

It reuses the same observations, so it is **never a confirmation**. No test is added to the earlier Holm family.

- **Popularity measure:** `T200`, the time from a mint's first transaction to its 200th, from the pages already cached, no network. Bands: under 1 minute, 1 to 10 minutes, 10 to 60 minutes, over an hour, and `under_200` when the mint's history ends before 200 transactions.
- **Reported:** the bands on each side, the signal by band, and `n_large_before`, the number of large buyers read.
- **Variants of T1 on October-November pairs, as counts with McNemar's p, not corrected, and all labelled exploratory:** pairs in the same `T200` band, pairs without wallets not established, pairs without the 2 tokens already read, pairs without a signal coming from the perimeter, and all those filters together.

## Part 2: a new sample

- **Trips:** curve entries of October-November 2024, wallets CERTAIN or PROBABLE only, `launch_not_read`, and now a **token never read in any earlier group** of this work, which corrects the deviation in `DECISIONS.md` 26. Drawn with `random.Random(20261105)`, 40 trips.
- **Control, same rules as before:** the first eligible buy after the entry, within an hour, same curve band, same age band, another token no author's wallet traded, a wallet outside the perimeter.
- **New rule:** the same `T200` band. Up to 8 candidates per trip and 4 pages against 4 and 3 before, since this rule refuses more of them. A trip without a match is dropped and counted.
- **Same code on both sides:** S1, S1 without creators, Sx. A signal from a wallet of the perimeter is not excluded in the test, as before, and such cases are counted.

## One test

**T1b:** S1 on these pairs, exact two-sided McNemar.

- **Confirmed once popularity is matched:** T1b under 0.05, trips above control, and the pair difference on Sx less than half the one on S1.
- **Not specific to the gateway:** T1b passes, and Sx shows at least half the difference.
- **Not confirmed:** T1b does not pass. The report then says what gap this number of pairs could see, and that the earlier result may owe something to popularity, without showing it does.

Before the sample, 2 trips already flagged S1 are read again as a positive control. If either fails, the run stops.

## Limits

`T200` measures interest at launch, and it counts transactions after the author's entry when he enters within the first 200. It leaves later popularity unmatched. A wider signal, buys under 2 % of supply, stays invisible. This says nothing of why any trade was taken, nor that it paid. A signal present before a trade does not show it was seen.

## Resources

Ceiling 15,000 credits, on the pool's keys, estimated at about 400 per pair. A stop keeps the finished pairs and is reported.
