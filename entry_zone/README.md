# Entry zone: simple filters to enter a bundle snipe

A rule search separate from [post_detection_forensics](../post_detection_forensics/README.md): can a
few simple conditions on the entry market cap or premium, the SOL already engaged, and the buyers'
funding and spending capacity mark a zone where a 2x within 15 minutes is clearly more likely?

**Answer: no robust entry zone.** Rules chosen on TRAIN fall back to the base on VALIDATION, or hold
only as the premium or one operator; none makes money after costs.

| | |
|---|---|
| alerts, cut-offs | 1,657 (1,015 TRAIN, 642 VALIDATION), 9 cut-offs from the creation to alert + 5 min |
| confirmed 2x within 15 min at the alert / at + 5 min | 22.4 % / 11.1 % TRAIN, 26.4 % / 15.2 % VALIDATION |
| best TRAIN market-cap zone | 30k-35k USD at + 5 s: 47.4 % TRAIN, 31.4 % VALIDATION (base 25.3 %) |
| best TRAIN combination | 76.2 % TRAIN, 38.9 % VALIDATION on 18 alerts (base 26.4 %) |
| rules that hold on VALIDATION | 2 of 8, both explained by premium and operator |
| stable market-cap fact | above ~98k USD at the alert, 2.8 % and 1.7 %: the grouped operator family |
| trading, estimable VALIDATION cells with a positive net CI | 0 of 60 |

The full account, answers A to J, is in [results.md](results.md); the plan, written and committed
before any rate, in [analysis_plan.md](analysis_plan.md).

## Reproduce

From the repository root, offline, with the on-chain cache of `post_detection_forensics` in place:

```bash
python3 entry_zone/code/ez_10_build.py      # the table, once (refuses to rebuild once frozen)
python3 entry_zone/code/ez_20_search.py     # TRAIN search, VALIDATION once: E0, E1, E2
python3 entry_zone/code/ez_30_controls.py   # controls and classification: E3
python3 entry_zone/code/ez_40_trade.py      # trading simulation: E4
```
