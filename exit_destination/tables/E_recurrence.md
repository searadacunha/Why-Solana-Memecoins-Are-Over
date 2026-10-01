# E. Exit-wallet recurrence (exit wallets with two read events or more)

Share of exit wallets whose events all share the relation (sets: a common element). Null: the relation's values permuted among events, each wallet keeping its number of events (null 1 for destinations, 2 for funders, 3 for sniper pairs); 1000 permutations.

| relationship | observed | null mean [95 %] | percentile | p | ratio |
|---|---:|---|---:|---:|---:|
| sniper -> same exit wallet (always the same sniper, corpus) | 0.420 | 0.000 [0.000, 0.000] | 100 % | 0.0010 | x21000.00 |
| exit -> same funder | 0.298 | 0.003 [0.000, 0.011] | 100 % | 0.0010 | x108.94 |
| exit -> same cluster | 0.443 | 0.003 [0.000, 0.010] | 100 % | 0.0010 | x142.86 |
| exit -> same deployer network | 0.000 | 0.001 [0.000, 0.003] | 0 % | 1.0000 | n/a |
| exit -> same first SOL destination | 0.419 | 0.010 [0.000, 0.023] | 100 % | 0.0010 | x40.72 |
| exit -> same collection (terminal) wallet | 0.360 | 0.022 [0.005, 0.041] | 100 % | 0.0010 | x16.48 |
| exit -> same hub | 0.596 | 0.170 [0.088, 0.263] | 100 % | 0.0010 | x3.50 |
| exit -> same destination architecture (return category) | 0.515 | 0.094 [0.065, 0.123] | 100 % | 0.0010 | x5.46 |

Null 5, exit-wallet pairs together in two launches or more (corpus events of the sample, degree-preserving rewiring): 4.13e+03 | 1.77e+04 [1.75e+04, 1.79e+04] | 0 % | 1.0000 | x0.23

Same first destination repeated at least once (null 1): 0.765 | 0.427 [0.377, 0.477] | 100 % | 0.0010 | x1.79
