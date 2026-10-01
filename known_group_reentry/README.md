# Known group re-entry as a live trading signal

Can recognising, at the moment of an alert, that the snipers belong to a group already seen in earlier alerts
improve a real trading decision? Built only from frozen data: the economic-mechanics table for the group
structure (recognised chronologically, no look-ahead) and the post-detection-edge snapshot for live features,
spot prices and the cost model. No new Helius call; TEST untouched.

**Answer: NO INCREMENTAL SIGNAL, and no trade.**
- **The group carries information on its own.** Known-group alerts reach +50 % within 15 minutes more often
  (61 % against 34 % in VALIDATION).
- **It is already in the launch's size and price.** Matched on them, the difference is not distinguishable
  from zero, and adding the group to the baseline model does not improve it.
- **Every strategy loses after costs.** Known group or not, every entry, exit and size loses. The primary
  strategy loses 17 % per trade on known groups in VALIDATION.

| VALIDATION, entry +5 s | known group | unknown group |
|---|---:|---:|
| +50 % within 15 min | 61.2 % | 33.6 % |
| same, matched on the baseline features | +15.9 pts [-4.2, +32.9] | |
| log loss, baseline + group minus baseline | -0.0023 [-0.012, +0.008] | |
| primary strategy (target +50 %, stop -15 %, 15 min, $500), net per trade | -17.3 % [-21.3, -13.0] | -21.8 % |
| best gross case of the whole grid, at $100 | -1.6 % [-4.0, +1.6] | |

[results.md](results.md) gives sections A to J and the four closing sections;
[analysis_plan.md](analysis_plan.md) was committed with the group features before any outcome was computed.

## Reproduce

From the repository root, offline:

```bash
python3 known_group_reentry/code/kg_10_features.py   # chronological group features (no price read)
python3 known_group_reentry/code/kg_20_outcomes.py   # outcomes and simulated trades
python3 known_group_reentry/code/kg_30_analysis.py   # tables B to J and the decision
```
