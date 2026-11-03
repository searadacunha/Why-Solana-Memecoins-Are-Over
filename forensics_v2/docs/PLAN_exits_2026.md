# Plan: the 2026 groups' sales and exits, through the new engine

Written before any of these transactions is read. Until now the sales and exits of the 2026 groups came only from the frozen tables of `exit_destination/`, read
by their own parser and stopped at 10 transactions per event for 361 of 1,457 events. This does two things, on data dated before 2026-09-22 only (`DECISIONS.md` 10).

**Validation.** 100 events drawn with `random.Random(20261103)` among the 1,096 read to their end. Each of their transactions is decoded again from its raw form by this
engine. Compared per transaction, exactly: the wallet's SOL change, its token changes, and for a sweep the recipient and the amount. Passes if at least 99 % agree; every
disagreement is listed and none is fixed by changing the comparison.

**Extension.** 40 events drawn with the same generator among the 361 stopped by the cap. Each wallet's history is read over the event's dates, up to 3 pages. Reported: how many
sales and how much SOL the cap had hidden, whether the destination changes, and how many transactions involve a bridge program.

Ceiling 3,000 credits. No price or outcome file is opened. Limits: a 40-event sample says nothing about any one operator, and a bridge program seen says nothing about who
controls either end.
