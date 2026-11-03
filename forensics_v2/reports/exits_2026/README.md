# The 2026 groups' sales and exits, through the new engine

Plan committed before reading: [../../docs/PLAN_exits_2026.md](../../docs/PLAN_exits_2026.md). Figures: [results.json](results.json). Code: `investigations/exits_2026.py`. Nothing at or after
2026-09-22 was read, and no price or outcome file was opened. 595 network calls.

**The new engine reads these sales exactly as the frozen tables do, and it finds what their cap hid: on 40 capped events, 966 sales against 373, and 3,699 SOL against 1,445. The cap was a real undercount of those events. No bridge program in the 6,693 transactions read.**

## Validation

100 events drawn at random among the 1,096 read to their end. 427 transactions decoded again from their raw form, then compared on SOL change, token change and sweep recipient.

| | Transactions | Agree |
|---|---:|---:|
| First run | 427 | 135 |
| After aligning one convention | 427 | **427** |

The first run failed the plan's 99 %, and the plan said no disagreement would be fixed by changing the comparison. It is changed once, and said here: the frozen table's `dsol` adds the fee back when the wallet signs (`exit_destination/code/ed_trace.py:175`), and my comparison had missed it. Every one of the 292 differences was exactly the fee. No other adjustment was made. See `DECISIONS.md` 17.

## Extension: what the 10-transaction cap hid

40 events drawn at random among the 361 stopped by the cap. Each wallet read for three days from the event, at most 3 pages, 12 of them not read to the end of that window, so these are lower bounds.

| | Frozen table | New engine |
|---|---:|---:|
| Sales of the event's token | 373 | **966** |
| SOL from those sales | 1,444.88 | **3,699.08** |
| Events with a known destination for their SOL | 6 | **40** |

Where both name a destination, they agree on 5 of 6. In 34 of the 40, the frozen table had none because the sweep came after the cap.

## What this does to the frozen results

The frozen study states the cap and treats those 361 events as partial, so its conclusions stand as written. Two limits become concrete: its sale counts for capped events are low, by about 2.6 times on this sample, and its destination shares rest mostly on the 1,096 complete events. These 40 are too few to redo them by operator, and that was not tried.

## Limits

40 events say nothing about one operator. The sweep total over these wallets also contains other launches inside the three days, so it is not reported per event. A wallet's top destination is not its owner.
