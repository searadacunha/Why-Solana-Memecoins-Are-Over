# Economic mechanics of coordinated groups

How the coordinated groups found in [coordination_detection](../coordination_detection/README.md) operate:
funding, coordinated buys, supply, price impact, exits, the return of capital and reuse on the next launch.
No price outcome defines any group, role, architecture or cluster.

**Answer: a repeatable operating loop.** A funder sends about 25 SOL to each of four sniper wallets in the same
second, minutes before the launch; the snipers buy 78 % of the supply in the creation slot, which sets the
opening price; within seconds most move their tokens to their own exit wallet, the same one launch after
launch; the leftover SOL goes back to the funder, which funds the same snipers again a median 21 minutes later,
behind a new deployer. Each of these steps lies far outside its null model in both periods, without the
dominant operator and without the dominant wallets. Who controls the wallets, and with what intent, is not
observable on-chain.

| | TRAIN | VALIDATION |
|---|---:|---:|
| coordinated launches with one funder for 2+ snipers | 92 % | 91 % |
| funding spread, median | 0 s | 0 s |
| first token moves in one slot (null) | 0.65 (0.05) | 0.76 (0.07) |
| returning snipers sending SOL back to their funder (null) | 60 % (2 %) | 92 % (7 %) |
| exit wallets always fed by the same sniper (null) | 81 % (0.4 %) | 83 % (0.3 %) |
| deployer funded from the snipers' own network (null) | 26 % (0) | 26 % (0) |

[results.md](results.md) gives sections A to J and the four closing sections; [analysis_plan.md](analysis_plan.md)
was committed with the frozen table before any measure.

## Reproduce

From the repository root, offline, with the on-chain cache of `post_detection_forensics` in place:

```bash
python3 economic_mechanics/code/em_10_build.py      # table and price file, freeze, integrity (once)
python3 economic_mechanics/code/em_20_analysis.py   # tables B to J and the price impact
python3 economic_mechanics/code/em_30_extra.py      # table K, the checks added for the classification
```
