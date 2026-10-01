# B. Funder -> destination map

Primary wallets: 62 (38 short-lived, 24 very active). Upstream chains 55, downstream branches 408.

## Upstream: who funded the primary wallets (terminal class of each chain)

| class | chains | operators | hops to terminal (median) |
|---|---:|---:|---:|
| A known hub | 52 | 16 | 1 |
| D deployer network | 1 | 1 | 1 |
| E cross-operator network | 1 | 1 | 1 |
| G unresolved | 1 | 1 | 5 |

Unresolved (up): UNRESOLVED >5 HOPS 1

## Downstream: where their outgoing SOL goes

| class | branches | SOL | operators | hops to terminal (median) |
|---|---:|---:|---:|---:|
| A known hub | 217 | 22158.7 | 15 | 1 |
| D deployer network | 2 | 6.2 | 1 | 1 |
| E cross-operator network | 13 | 711.9 | 3 | 2 |
| C operator-associated | 150 | 4465.7 | 11 | 2 |
| F new / unknown, keeps the SOL | 6 | 246.2 | 4 | 1 |
| G unresolved | 20 | 4104.3 | 7 | 3 |

Unresolved (down): unresolved: too active 13, UNRESOLVED >5 HOPS 4, circular flow 3

Upstream starts: read 55, hub 7
Ends of the short-lived wallets: read 38
Short-lived wallets: transactions after their last sweep and before TEST start, median 521.5; still active after TEST start: 0.

## Very active wallets: the sampled transactions

sweep received 425, other SOL out 258, other 2
