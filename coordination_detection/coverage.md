# Coverage of the coordination variables, before the plan

1657 launches, 6822 sniper records (the detector's tickets), 40362 early buyers (the first 25 buyers outside the bundle up to alert - 1 s). No coordination measure was computed for this file.

| variable | OBSERVED | of |
|---|---:|---:|
| sniper_buy_time | 6822 (100.0 %) | 6822 |
| sniper_genesis_funder | 6064 (88.9 %) | 6822 |
| sniper_source | 6064 (88.9 %) | 6822 |
| sniper_last_funder | 6647 (97.4 %) | 6822 |
| creator_genesis_funder | 1638 (98.9 %) | 1657 |
| creator_last_funder | 1645 (99.3 %) | 1657 |
| early_genesis_funder | 5148 (12.8 %) | 40362 |
| tickets, buy slots and times, wallet identities (snipers and early buyers) | 100 % | |
| sniper exits (sell or transfer out) up to alert + 30 s | observed inside the window | |
| anything after alert + 30 s | 0 | |

## Missing, and what it would cost

- Early buyers' funders: 87 % of them have 1,000 earlier transactions or more; their genesis needs their whole history, unbounded for seasoned bots. Not collectable at a known cost.
- Genesis funder of the snipers with 1,000 transactions or more (11.1 %): unbounded as well; their last funder is OBSERVED for 97.4 % of all snipers.
- Sells after alert + 30 s: one signature page per sniper after its buy, then its transactions up to the exit: at least 27288 calls (6822 snipers x about 4), more for wallets active afterwards.

None of them is needed for the main question (coordination observable at the launch); the sells are a secondary, descriptive section. No collection is launched.
