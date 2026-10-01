# H. Nulls and robustness (1000 permutations)

Each test: observed | null mean [95 %] | percentile | p | effect.

| subset | primary wallets | shared non-hub wallets (2+ operators) | operators in the largest component | null A (swaps): shared | null B (labels): shared | null C (cross-operator swaps): shared | null A: largest |
|---|---:|---:|---:|---|---|---|---|
| full | 62 | 16 | 7 | 16 | 24.7 [22, 27] | 0 % | 1.0000 | x0.65 | 16 | 28.2 [19, 43] | 0 % | 1.0000 | x0.57 | 16 | 24.8 [22, 27] | 0 % | 1.0000 | x0.65 | 7 | 16.7 [14, 19] | 0 % | 1.0000 | x0.42 |
| without the dominant operator (k:21.13+21.08+) | 39 | 8 | 5 | 8 | 13.2 [11, 14] | 0 % | 1.0000 | x0.61 | 8 | 13.2 [9, 14] | 1 % | 0.9940 | x0.60 | 8 | 13.2 [11, 14] | 0 % | 1.0000 | x0.61 | 5 | 12.1 [9, 15] | 0 % | 1.0000 | x0.41 |
| without the 10 primary wallets with the most sweeps | 52 | 9 | 6 | 9 | 17.2 [14, 20] | 0 % | 1.0000 | x0.52 | 9 | 16.7 [11, 20] | 0 % | 0.9950 | x0.54 | 9 | 17.2 [14, 20] | 0 % | 1.0000 | x0.52 | 6 | 9.72 [8, 11] | 0 % | 1.0000 | x0.62 |
| known non-hub (paths through a hub removed) | 62 | 4 | 6 | 4 | 13.6 [11, 15] | 0 % | 1.0000 | x0.29 | 4 | 16.6 [9, 31] | 0 % | 1.0000 | x0.24 | 4 | 13.5 [11, 15] | 0 % | 1.0000 | x0.30 | 6 | 11.7 [9, 14] | 0 % | 1.0000 | x0.51 |
| strict non-hub | 62 | 15 | 7 | 15 | 24.1 [21, 26] | 0 % | 1.0000 | x0.62 | 15 | 27.1 [18, 42] | 0 % | 1.0000 | x0.55 | 15 | 24 [21, 26] | 0 % | 1.0000 | x0.62 | 7 | 16.4 [14, 19] | 0 % | 1.0000 | x0.43 |
| TRAIN | 52 | 7 | 6 | 7 | 15.7 [12, 18] | 0 % | 1.0000 | x0.45 | 7 | 19.4 [11, 35] | 0 % | 1.0000 | x0.36 | 7 | 15.6 [13, 18] | 0 % | 1.0000 | x0.45 | 6 | 9.51 [8, 11] | 0 % | 1.0000 | x0.63 |
| VALIDATION | 10 | 7 | 5 | 7 | 7 [7, 7] | 0 % | 1.0000 | x1.00 | 7 | 7 [7, 7] | 0 % | 1.0000 | x1.00 | 7 | 7 [7, 7] | 0 % | 1.0000 | x1.00 | 5 | 6.88 [4, 9] | 4 % | 0.9630 | x0.73 |

Leave one shared wallet out (full sample: 16 shared, largest component 7 operators): without 27NsskNe: 15 shared, largest 7; without 7a2zhDAJ: 15 shared, largest 7; without 7oobYnBy: 15 shared, largest 7; without 8zHcWujH: 15 shared, largest 7; without AP6c8AS1: 15 shared, largest 7; without AyBdrsDJ: 15 shared, largest 7; without CS1egm8U: 15 shared, largest 7; without CekCebfL: 15 shared, largest 7; without CrAtVXEZ: 15 shared, largest 7; without DRUKt6L9: 15 shared, largest 7; without ED1oUL2L: 15 shared, largest 7; without EcnoSUW5: 15 shared, largest 7; without FEiQigJg: 15 shared, largest 7; without FizVVLFL: 15 shared, largest 7; without GMVasHNA: 15 shared, largest 7; without H9tyeSef: 15 shared, largest 6

## Time: ISO weeks in which each shared wallet appears on a path

- 27NsskNeGn: 2026-W34, 2026-W35
- 7a2zhDAJom: 2026-W36, 2026-W37
- 7oobYnByuw: 2026-W36, 2026-W37
- 8zHcWujHhy: 2026-W35, 2026-W39
- AP6c8AS1fd: 2026-W40
- AyBdrsDJ2A: 2026-W34, 2026-W35
- CS1egm8UeL: 2026-W40
- CekCebfLJJ: 2026-W38, 2026-W39
- CrAtVXEZ5C: 2026-W36, 2026-W39
- DRUKt6L9GM: 2026-W39, 2026-W40
- ED1oUL2Lsc: 2026-W36, 2026-W37
- EcnoSUW5ZK: 2026-W36, 2026-W37
- FEiQigJgXG: 2026-W40
- FizVVLFL2L: 2026-W40
- GMVasHNAuL: 2026-W40
- H9tyeSef4P: 2026-W35
