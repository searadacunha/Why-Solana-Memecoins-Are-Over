# Plan: an independent control of the signal before the author's entries

Written and committed before any of this reading. The earlier comparison (`PLAN_trade_context.md`, amendment of 2026-11-02) was added after reading its first groups. Its comparison group was
ordinary buys at uniform moments, not matched on date, curve level or token age, and its trade sample left out trips already suspected. This test is on trips never read, against comparable buys
on other tokens. Results stay in the private folder; this page has no figure from them.

## Sample of the author's trips

Trips entered on the bonding curve between 2024-10-01 and 2024-12-31 whose launch has never been read, drawn with `random.Random(20261104)`: 40 from October and November, 20 from December. The split
at December 1 was chosen after seeing the earlier groups: it is what is tested here, on new data.

## Matched control, one per trip

- **Same time:** the first eligible buy after the author's entry, within one hour.
- **Same curve level after the buy:** under 5, 5 to 20, or 20 to 85 SOL. The author's own level comes from his first buy's event in the raw transaction.
- **Same token age at the buy:** under 1 minute, 1 to 10 minutes, 10 to 60 minutes, 1 to 24 hours, over a day.
- **Different token, different person:** a pump.fun token that none of the author's wallets traded, bought by a wallet outside his perimeter.
- At most 4 candidate tokens and 3 pages per trip. A trip with no match is dropped and counted.

## Measures, same code on both sides

- **S1:** as in the first plan.
- **S1 without creators:** the same, not counting the token's creator.
- **Sx, negative control:** S1 with exchange hot wallets instead of the gateway. These five carry public labels in the repository: `FWznbcNX…`, `5tzFkiKs…`, `H8sMJSCQ…`, `2AQdpHJ2…`, `GJRs4FwH…`.

## Tests, two, Holm

- **T1:** October-November pairs, S1, exact McNemar, two-sided.
- **T2:** the author's fresh trips, S1, October-November against December, two-sided Fisher.

## How it will be read

- **Confirmed:** T1 under 0.05 after Holm, author above control, and the pair difference on Sx less than half the one on S1.
- **Not specific to the gateway:** T1 passes, but Sx shows at least half the difference.
- **Not confirmed:** T1 does not pass. The report then says what size of effect this sample could have seen: 40 pairs have good power for a gap of about 40 points, and little for a gap under 10 points.
- **T2 under 0.05** says that the signal's frequency changed over time, not why. December pairs are descriptive.

## Limits and resources

Matching on three variables leaves a token's popularity unmatched. This says nothing of why any trade was taken. S1 stays a lower bound, as before. Ceiling 15,000 credits, on the pool's keys only; a stop keeps the finished pairs and is reported. Before the sample, 2 trips of frozen class P already flagged S1 are read again as a positive control: if either fails, the run stops.
