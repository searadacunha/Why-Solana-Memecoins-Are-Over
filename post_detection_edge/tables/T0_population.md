# T0. Population and coverage (no outcome in this table)

Snapshot `data/SNAPSHOT.json`, T_SNAP = 2026-09-29 11:23:00 UTC. Regenerate: `python3 post_detection_edge/code/build_10_dataset.py`.

| split | window (UTC) | alerts | with price series | fine sampling (5 s) | operator clusters |
|---|---|---:|---:|---:|---:|
| TRAIN | 2026-08-21 17:35 -> 2026-08-29 18:04 | 325 | 316 | 118 | 69 |
| VAL | 2026-08-30 11:11 -> 2026-09-14 23:04 | 690 | 690 | 690 | 146 |
| TEST | 2026-09-15 10:46 -> 2026-09-29 10:47 | 642 | 642 | 642 | 128 |
| all | 2026-08-21 17:35 -> 2026-09-29 10:47 | 1657 | 1648 | 1450 | 319 |

## Coverage of the entry-at-P0 window, by horizon

`observed` = the whole window is covered by reads (pde.window); `censored` = a detector outage or the end of the follow-up cuts it; `missing` = no series, or a horizon shorter than the 45 s sampling of the alerts before 2026-08-25 21:47 UTC.

| horizon | split | observed | censored | missing |
|---|---|---:|---:|---:|
| 10s | train | 117 | 1 | 207 |
| 10s | val | 688 | 2 | 0 |
| 10s | test | 640 | 2 | 0 |
| 30s | train | 117 | 1 | 207 |
| 30s | val | 686 | 4 | 0 |
| 30s | test | 639 | 3 | 0 |
| 60s | train | 117 | 1 | 207 |
| 60s | val | 682 | 8 | 0 |
| 60s | test | 636 | 6 | 0 |
| 5m | train | 279 | 37 | 9 |
| 5m | val | 665 | 25 | 0 |
| 5m | test | 626 | 16 | 0 |
| 15m | train | 272 | 44 | 9 |
| 15m | val | 624 | 66 | 0 |
| 15m | test | 606 | 36 | 0 |
| 1h | train | 250 | 66 | 9 |
| 1h | val | 519 | 171 | 0 |
| 1h | test | 528 | 114 | 0 |
| 24h | train | 0 | 316 | 9 |
| 24h | val | 0 | 690 | 0 |
| 24h | test | 47 | 595 | 0 |

Operator clusters (shared sniper wallet, creator or ticket configuration): 319 clusters; largest 320, 40, 40, 38, 23, 23, 22, 20; 133 singletons.

Actor label: {None: 11, 'grouped': 407, 'single': 1239}.
