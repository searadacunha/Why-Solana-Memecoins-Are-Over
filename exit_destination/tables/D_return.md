# D. Capital return: every outgoing SOL transfer (0.1 SOL or more) of the exit wallet, followed

Read events 1457; with at least one outgoing transfer 1161; branches 1280 carrying 13645.3 SOL.

| first terminal | branches | % | SOL | % SOL | direct (hop 1) | multi-hop | events with one | launches | exit wallets |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| H1 launch funder | 631 | 49 % | 7697.8 | 56 % | 631 | 0 | 590 (51 %) | 72 | 183 |
| H2 same cluster | 7 | 1 % | 122.8 | 1 % | 7 | 0 | 7 (1 %) | 3 | 6 |
| H3 deployer network | 0 | 0 % | 0.0 | 0 % | 0 | 0 | 0 (0 %) | 0 | 0 |
| H4 known wallet, other cluster | 0 | 0 % | 0.0 | 0 % | 0 | 0 | 0 (0 %) | 0 | 0 |
| H5 hub | 300 | 23 % | 2685.0 | 20 % | 289 | 11 | 249 (21 %) | 19 | 107 |
| H6 unresolved | 342 | 27 % | 3139.7 | 23 % | 333 | 9 | 322 (28 %) | 21 | 127 |

Read events with no outgoing transfer of 0.1 SOL or more in the window (capital stays on the exit wallet, or left before the reading stopped): 296.

Unresolved branches by reason: too active 304, retained by an unknown wallet 35, cycle 3

Hops to the first terminal: 1: 1260, 2: 10, 3: 7, 4: 3

TRAIN: H1 46 %, H2 1 %, H3 0 %, H4 0 %, H5 41 %, H6 13 %
VALIDATION: H1 53 %, H2 0 %, H3 0 %, H4 0 %, H5 6 %, H6 41 %

Branches leaving after the exit wallet's first sale: 1236; their terminals: H1 51 %, H2 1 %, H3 0 %, H4 0 %, H5 22 %, H6 27 %.
Smaller outgoing transfers of intermediate wallets (recorded, not followed): unknown 70, H2 3
