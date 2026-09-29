# Post-detection edge: buying after a bundle snipe

A separate study from the rest of this repository, with its own data and nothing shared but the
statistics helpers and the redaction module. It asks one question, set up to be refuted:

> When a bundle snipe is detected at the launch of a pump.fun token, does buying right after the
> detection still yield large multiples, and does anything observable at the moment of detection
> separate the launches that will from those that will not?

**Answer: SIGNAL STATISTIQUE MAIS PAS D'EDGE TRADABLE** (statistical signal, no tradable edge).

On 1,657 bundle snipes detected live between 2026-08-21 and 2026-09-29, entering at the alert price:

| | |
|---|---|
| reached 2x within 10 s / 60 s / 15 min / 1 h | 0.0 % / 1.5 % / 30.1 % / 36.3 % |
| signals locked before the test | 12 |
| survived the test | 1: a logistic score, P(2x within 15 min) 45.7 % against 31.0 % (N = 164) |
| rules at 80 % or more in training | 10, all with N of 20 to 28; 11 to 44 % on the test |
| best mean net return per trade of the survivor, pre-declared strategies, +10 s, $500 | -8.1 % [-21.7, +1.6] |
| its own strategy (hold to 2x, 15 min) | -9.8 % before costs, -23.3 % after |
| doubling rate needed to break even when holding for 2x | 49.7 % before costs, 58.5 % after |

The full account is in [results.md](results.md), which ends with the FINAL VERDICT section. How every
number is defined is in [methodology.md](methodology.md), and what went wrong along the way is in
[pitfalls.md](pitfalls.md).

## Layout

| path | content |
|---|---|
| `data/` | the frozen snapshot: detector journal and price series cut at 2026-09-29 11:23 UTC, the pre-registered protocol and its caches, hourly SOL/USD; `SNAPSHOT.json` holds a sha256 per file. Read-only |
| `derived/` | one row per alert, features and targets: `dataset_dev` (TRAIN + VALIDATION) and `dataset_test.sealed` (TEST) |
| `code/` | the scripts below, stdlib only |
| `tables/` | every table quoted in the documents, and `LOCK.json` |

## Reproduce

From the repository root, offline:

```bash
python3 post_detection_edge/code/build_10_dataset.py     # features, targets, coverage (T0)
python3 post_detection_edge/code/an_20_baseline.py       # base rates, TRAIN and VALIDATION (T1)
python3 post_detection_edge/code/an_30_univariate.py     # univariate screen (T2)
python3 post_detection_edge/code/an_40_signals.py        # rules, logistic, tree; checks LOCK.json (T3)
python3 post_detection_edge/code/an_50_protocol400.py    # the protocol pre-registered on 2026-08-29 (T5)
python3 post_detection_edge/code/an_60_final_test.py     # the final test on the locked signals (T1b, T4, T6, T7)
python3 post_detection_edge/code/an_70_payoff.py         # payoff decomposition and latency (T8)
```

`an_40` never rewrites the committed lock: it recomputes it and stops if the result differs. The two
`snap_*` scripts built `data/` once. The first needs the detector's private directory, the second the
network; neither is needed to reproduce anything above.

The lock and everything before it were committed in `e310335`, before the test split was first read.
