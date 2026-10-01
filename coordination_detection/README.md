# Coordination detection: do the buying wallets of a launch act as a group?

A study independent of price: it asks whether the wallets that snipe a pump.fun launch show an
on-chain structure of coordination, not whether the token goes up. No 2x, ATH, future market cap or
volume is used or computed.

**Answer: COORDINATED ON-CHAIN ACTIVITY, in about four launches out of five.** The data show a
coordinated funding and buying structure observable on-chain; they do not, by themselves, establish
the actors' intent.

| | TRAIN | VALIDATION |
|---|---:|---:|
| launches | 1,015 | 642 |
| two snipers or more on one non-hub funder (null mean) | 790 (18) | 454 (20) |
| the same, funders known not to be hubs only (null mean) | 300 (9) | 160 (7.5) |
| snipers funded together, tighter than the null | 98 % | 98 % |
| snipers already seen sniping together before | 47 % | 36 % |
| recurring sniper pairs (null mean) | 664 (44) | 368 (36) |
| two labels or more / none | 87 % / 2.8 % | 81 % / 3.9 % |

The typical structure: one wallet funds all the snipers in one go, about 3 minutes before the launch.
It holds in every week, without the dominant operator and without the dominant wallets. The population
is the detector's alerts, already selected for bundle snipes; these rates describe it, not pump.fun.

[coverage.md](coverage.md) first, [analysis_plan.md](analysis_plan.md) second (committed with the
frozen table before any rate), [results.md](results.md) for the answers A to N.

## Reproduce

From the repository root, offline, with the on-chain cache of `post_detection_forensics` in place:

```bash
python3 coordination_detection/code/cd_00_coverage.py   # coverage, no measure
python3 coordination_detection/code/cd_10_build.py      # table, freeze, integrity (once)
python3 coordination_detection/code/cd_20_analysis.py   # C1 to C8
```
