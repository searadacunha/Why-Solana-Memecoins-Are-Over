# T5. Pre-registered protocol of 2026-08-29 ("400"), evaluated on the snapshot

Protocol text: `data/protocol400_caches/PROTOCOLE_400.md` (unchanged). T0 = 2026-08-29 18:36 UTC; now = T_SNAP = 2026-09-29 11:23:00 UTC. Success = x2 CONFIRMED in the series (two consecutive reads >= 2 inside 180 s, one read after); failure = no confirmed x2 and age >= 24 h. The detector's outages are not corrected for (the protocol does not), so success is a lower bound. Regenerate: `python3 post_detection_edge/code/an_50_protocol400.py`.

Test alerts after T0: 1332; decided: 1321 (confirmed x2: 492).

| hypothesis | registered size | reading | n | x2 | rate [Wilson] | verdict |
|---|---:|---|---:|---:|---|---|
| C1 grouped actor outside lineage 4kwM | 40 | registered | 30 | 9 | 30.0 % (9/30) [16.7-47.9] | NOT EVALUABLE: 30 of 40 required |
| C1 grouped actor outside lineage 4kwM | 80 | registered (extension) | 30 | 9 | 30.0 % (9/30) [16.7-47.9] | NOT EVALUABLE: 30 of 80 required |
| C1 grouped actor outside lineage 4kwM | 40 | as coded | 314 | 118 | 37.6 % (118/314) [32.4-43.1] | RETRACTED (protocol backtest -17.3 %) |
| C1b lineage 4kwM (elimination) | 10 | registered | 8 | 1 | 12.5 % (1/8) [2.2-47.1] | NOT EVALUABLE: 8 of 10 required |
| C2 copied name | 15 | registered | 3 | 1 | 33.3 % (1/3) [6.1-79.2] | NOT EVALUABLE: 3 of 15 required |
| C3 low pool density at 60 s (within C1) | 30 | registered | 30 | 9 | 30.0 % (9/30) [16.7-47.9] | RETRACTED (n60<=100: 3/13, n60>100: 6/17, Fisher p = 0.691) |
| C4 second verdict at 15 min, x0.50 (x2 afterwards = false negative) | 60 | registered | 60 | 0 | 0.0 % (0/60) [0.0-6.0] | CONFIRMED (0 false negative) |
| C4 second verdict at 15 min | 60 | as coded (all decided) | 656 | 2 | 0.3 % (2/656) [0.1-1.1] | RETRACTED |
| C6 core exit destination | 30 | registered | 0 | 0 | - | NOT EVALUABLE: exit caches never collected after T0 |

Collection state in the snapshot: funding lineage for 38 post-T0 alerts (last on 2026-08-31), copied-name checks for 105, pool density n60 for 30, core-exit data for 0. The daily `--collecte` stopped on 2026-08-31.
