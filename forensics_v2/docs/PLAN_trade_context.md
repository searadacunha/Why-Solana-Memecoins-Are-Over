# Plan: was the described signal there before the author's own entries?

Written and committed before any launch context is read. The frozen 2024 study could only test this through the group members it had
scanned, and left many trips undecided. This reads each token's first buyers directly, so it does not depend on that sample.
Descriptive: no test is promoted, and the motive for any trade stays unknowable. Results stay in the
private folder.

## The signal, as the author describes it

A wallet funded through the gateway attributed to ChangeNOW buys a large share of a token's supply early, and he buys after it.
Fixed here as:

- **S1 (strict):** before his first buy, on the same mint, a single buy of at least 2 % of supply (20 M tokens) by a wallet whose first
  transaction is a direct gateway credit, dated before that buy.
- **S2 (wider):** the same, whatever the wallet's first transaction, as long as a direct gateway credit precedes the buy within 7 days.
- **S0 (any large buyer):** any single buy of at least 2 % before his entry, whatever its funding. It says how often S1 or S2 could
  be told apart from a large buyer in general.

## Sample, fixed before reading

All trips entered on the bonding curve in 2024-10-01 to 2024-12-31 (closed or open), from the frozen table:

- **A:** the trips of frozen class P.
- **B:** the trips last sold on Raydium after graduation. Selected on their result, so never a base rate.
- **C:** 200 other curve-entry trips drawn with `random.Random(20261102)`. This is the only group from which a rate over his curve
  trades may be read.

Raydium entries are out: their launch context is far from the entry, and that is a limit of this test.

## Reading, per mint

The mint's first two pages, 200 transactions at most, 20 credits. Up to 8 earliest buyers of at least 2 % before his entry: each
one's first page, 10 credits. At most 100 credits per mint, about 45,000 in all. A mint whose first 200 transactions do not reach his
entry is marked `window_covers_entry: false`, its large buyers are a lower bound, and it is reported separately.

## Reported, per group

Share with S1, S2 and S0 with Wilson intervals; delay from the signal to his entry; the size of his first buy in percent of supply; rank among buyers; SOL in the curve at entry. Realised SOL by S1 yes or no for group C
only, marked as association.

## Outcome of this comparison

The description holds for his curve trades if most of group C show S1 or S2. It holds for part of them if a minority does, and the
share is the result. Trades that do not fit are listed as they are. None is reclassified to fit.

## Amendment, 2026-11-02, written after reading groups A, B and C

A share means little without a comparison, and the plan had none. Added after seeing S1 in group C, so this comparison was not fixed in advance, and
it is reported as such. **Group X:** 200 ordinary buys, one for each random moment drawn uniformly in 2024-10-01 to 2024-12-31 with
`random.Random(20261103)`: at that moment, the first successful pump.fun buy after it, taken with its wallet and mint, excluding the author's own wallets.
Same code as for his trades, with that buy as the entry. Reported for all and for `entry_seen`, overall and by SOL in the curve after entry (under 5, 5 to
20, 20 to 85). Comparison by a two-sided Fisher test on S1 with `entry_seen`, against group C only. Only one test is added, and the ceiling is 22,000 credits.

## Limits

A signal present before a trade does not show that it was why he bought. Curve trades are not all his trades. 2 % is one threshold, and
a group buying 0.2 % each, as in the published case, is invisible to S1 and S2. Attribution of the gateway is public, not proven here.

## Amendment, 2026-11-03, written before this read

The launches of the trips that weigh most are read too: every trip matched to a PnL card, and the 40 largest gains and 40 largest losses among closed trips of
2024-10-01 to 2025-02-02, whatever their venue, skipping those already read. Same code and same definitions of S0, S1, S2. These trips are chosen on their result,
so this is a case list and never a rate: the only rate stays group C. Ceiling 10,000 credits, on the two keys of the pool that still answer.
