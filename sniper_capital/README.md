# Sniper capital: does the share of capital a sniper risks say which launches double?

A study separate from [post_detection_forensics](../post_detection_forensics/README.md) and
[entry_zone](../entry_zone/README.md), on the snipers' state strictly before their buy: capital,
ticket, last funding, its timing, and who funded them.

**Answer: no relation survives.** Ticket over capital separates on its own (ROC-AUC 0.62 TRAIN,
0.73 VALIDATION) but adds +0.013 [-0.029, +0.057] once premium, operator and the number of snipers
are known, and its effect between comparable launches changes sign from week to week. The rules that
hold on VALIDATION hold only by setting the grouped operators aside, and none makes money after costs.

| | |
|---|---|
| sniper records, launches | 6,822, 1,657 (896 TRAIN and 606 VALIDATION labeled) |
| a typical sniper | 25 SOL of capital, 20 SOL ticket, funded from zero minutes before the buy |
| threshold rules: TRAIN OVERFIT / NO SIGNAL / CONFOUNDED | 4 / 1 / 4 |
| trading, estimable VALIDATION cells with a positive net CI | 0 of 300 |
| not tested (option 1, no RPC call) | funding over 1 h to 7 days, SOL spent in the history |

[coverage.md](coverage.md) measures what the collected data cover and what completing them would
cost; [analysis_plan.md](analysis_plan.md) was written and committed before any rate;
[results.md](results.md) gives the answers.

## Reproduce

From the repository root, offline, with the on-chain cache of `post_detection_forensics` in place:

```bash
python3 sniper_capital/code/sc_00_coverage.py   # coverage and costs, no label read
python3 sniper_capital/code/sc_10_build.py      # the table, once (refuses to rebuild once frozen)
python3 sniper_capital/code/sc_20_analysis.py   # S1 descriptive, S2 central test, S3 rules and controls
python3 sniper_capital/code/sc_30_trade.py      # S4 trading simulation
```
