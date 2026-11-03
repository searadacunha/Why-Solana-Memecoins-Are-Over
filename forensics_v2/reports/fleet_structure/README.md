# The published fleet against the gateway's ordinary traffic

Figures: [results.json](results.json) and [hypotheses.json](hypotheses.json). Code: `investigations/posthoc/fleet_vs_gateway.py`, `investigations/fleet_hypotheses.py`. Plan for the second part, committed before reading: [../../docs/PLAN_fleet_hypotheses.md](../../docs/PLAN_fleet_hypotheses.md). Payouts come from the frozen study's list of public transfers, 91,789 over 49 days. 54 calls for the second part. Nothing here identifies a person.

**The exact amount links nobody: 2.9768156 SOL fits the gateway's fee line on a round 3 SOL, and it was paid 1,753 times in 49 days. What sets the fleet apart is acting together, and it is not alone in that: 5 of 150 sampled bursts repeat the same purchase on 3 tokens or more, as it does. The 8 strict bursts are not one operator. Their tools point to third-party bots, and only 3 of them, on the same day, share a destination.**

## The amount

| | |
|---|---:|
| Payouts of at least 1 SOL | 91,789 |
| Fall on one fee line | 22.1 % |
| Repeat an amount exactly | 37.7 % |
| Paid exactly 2.9768156 SOL | 1,753, about 38 per active day |
| Windows with 15 identical payouts within 380 s | 43 in 49 days, 2 at this amount |

The line, read from the amounts: payout = requested × 0.994 − 0.0051844 SOL, with the request in hundredths of a SOL. So 2.0 gives 1.9828156, 1.5 gives 1.4858156 and 3.0 gives 2.9768156. It holds to the lamport from 2024-09-30 to 2025-01-16 (`STRONG_TECHNICAL_INFERENCE`: the gateway's pricing is not on chain). Two wallets receiving the same amount may simply have asked for the same round figure. This is why a shared amount never decided anything in the [burst test](../gateway_bursts/README.md), and why it should not be read as a link on its own.

## The groups

| Group | Date | Payout, SOL | Tokens with a same-size purchase | Sweep destination | Fee account in the buys |
|---|---|---:|---:|---|---|
| Burst 33 | 2024-10-22 | 2.9768156 | 1 | `D15CAtUp…` | `F34kcgMg…` |
| Burst 106 | 2024-12-03 | 1.9828156 | 3 | `GrmXv6qK…` | `9RYJ3qr5…`, `28KqHiud…` |
| **Published fleet** | **2024-12-13** | **2.9768156** | **3 of 9** | **`ERGbjcz9…`** | **`BTQyUXhx…`, `F34kcgMg…`** |
| Burst 124 | 2025-01-14 | 1.9828156 | 3 | `8jPLUWVo…` | Maestro |
| Burst 126 | 2025-01-15 | 1.9828156 | 3 | `Cxw6iN92…` | Maestro |
| Burst 138 | 2025-01-28 | 1.0 | 1 | `3rb7jngm…` | `9RYJ3qr5…`, `28KqHiud…` |
| Burst 140 | 2025-01-28 | 1.98701297 | 1 | `6aRTeY51…` | none repeated |
| Burst 141 | 2025-01-28 | 1.98701297 | 3 | `6aRTeY51…` | Maestro |
| Burst 142 | 2025-01-28 | 1.98701297 | 4 | `6aRTeY51…` | Maestro, `AVUCZyuT…`, `7ks326H4…` |

Among the 150 sampled bursts, 142 have no same-size purchase, 3 have one token, and 5 have 3 or more. The fleet belongs to that last kind by this count. Its same size on more tokens with a looser timing was not measured for the others, so this is not a ranking.

## Which hypothesis

Read as written in the plan.

| Question | What was found | Reading |
|---|---|---|
| One operator behind all the groups? | Only bursts 140, 141 and 142 join, on the same day, through `6aRTeY51…` and its next hop. No other two groups meet within two hops | **Not supported** across the groups. Those three: `one operator` by the plan's rule |
| A coordinated group across them? | No shared token between groups that do not already share a destination | **Not supported** |
| Shared tools? | Maestro's fee account in 4 groups, `9RYJ3qr5…` with `28KqHiud…` in 2, `F34kcgMg…` in 2 including the fleet | **Supported as far as tools go.** Identical purchases can come from a bot's multi-wallet feature, so they may show one customer of a bot, not a separate infrastructure |
| Who runs each group? | One sweep destination per group, which fits one operator and a customer of a tool alike | `UNRESOLVED`, as the plan said it would stay |

Maestro is named from its accounts' own vanity prefix (`MaestroU…`, `MaestroA…`), not from a source. `F34kcgMg…` and the others are unnamed. Only the first page of 3 members per group was read.

Where the sweeps go next says more than the groups do:

- `8jPLUWVo…` → `3BzvGeit…` → **the gateway**, 29.09 SOL, and `6aRTeY51…` → `Cqep6bes…` → **the gateway**, 5 SOL. This money goes back through the service that funded it.
- `3rb7jngm…` → **an address labelled Bybit in this repository**, 193.83 SOL. It ends at an exchange.
- `D15CAtUp…` → two wallets, 609 and 600 SOL, one with a `god` prefix that passes it on to wallets of the same vanity. Not read further.

## The fleet's money: a closed ring

Read for the first time, with `AwzntLka…`'s first 200 transactions:

- **`AwzntLka…` → `G9X7F4Jz…`:** 39 transfers, 847.56 SOL, from 2024-11-20 to 2024-11-25.
- **`ERGbjcz9…` → `AwzntLka…`:** the transfers already reported, from 2024-11-20.
- **`G9X7F4Jz…` → `ERGbjcz9…`:** 1,491.80 SOL from 2024-11-20 to 2024-12-16, already reported.

So `G9X7F4Jz…`, `ERGbjcz9…` and `AwzntLka…` form a loop running in parallel (`ONCHAIN_VERIFIED` for the transfers). The fleet's 92.12 SOL entered this loop on 12-13 and 12-16, and `G9X7F4Jz…` also made the first payment to the deployers of 2 of the fleet's 9 tokens: 4.54 SOL on 12-14 and 1.76 SOL on 12-15, each about an hour before its token.

**What this changes:** the earlier note saw `G9X7F4Jz…` as a busy counterparty and nothing more. A loop is more than that: money comes back to it. It fits one treasury, and it also fits a busy service recycling its float. SOL is fungible, so this does not show that the fleet's own lamports reached a deployer. `G9X7F4Jz…` pays hundreds of other wallets, whose relation to the loop was not read. `EXPLORATORY_HYPOTHESIS`, and the next thing to test would be how much of its float returns to these two wallets against all its destinations.

## Limits

First-page reads, except where said. Labels come from the repository, and no label means only that. The 49 days are the frozen study's sample, not a full history. A fee line fitted on amounts is not the service's own statement.
